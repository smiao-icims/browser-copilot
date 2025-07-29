"""
Message integrity utilities for context management

These utilities ensure that AIMessage/ToolMessage pairs are never broken,
which is critical for avoiding "Bad Request" errors from LLMs.
"""

from typing import List, Set, Dict, Tuple, Optional
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage


class MessageIntegrityValidator:
    """Validates and ensures message integrity across all strategies"""
    
    @staticmethod
    def find_tool_dependencies(messages: List[BaseMessage]) -> Dict[str, Dict[str, any]]:
        """
        Find all tool call dependencies in the message list
        
        Returns:
            Dictionary mapping tool_call_id to {
                'ai_message_index': index of AIMessage,
                'tool_message_index': index of ToolMessage (if found),
                'ai_message': the AIMessage object
            }
        """
        dependencies = {}
        
        # First pass: Find all AIMessages with tool calls
        for i, msg in enumerate(messages):
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tc in msg.tool_calls:
                    tc_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                    if tc_id:
                        dependencies[tc_id] = {
                            'ai_message_index': i,
                            'tool_message_index': None,
                            'ai_message': msg
                        }
        
        # Second pass: Find all ToolMessages
        for i, msg in enumerate(messages):
            if isinstance(msg, ToolMessage) and hasattr(msg, 'tool_call_id'):
                tc_id = msg.tool_call_id
                if tc_id in dependencies:
                    dependencies[tc_id]['tool_message_index'] = i
        
        return dependencies
    
    @staticmethod
    def get_required_indices(
        message_index: int,
        messages: List[BaseMessage],
        dependencies: Dict[str, Dict[str, any]]
    ) -> Set[int]:
        """
        Get all indices that must be included with a given message
        
        Args:
            message_index: Index of the message to check
            messages: Full message list
            dependencies: Tool dependencies from find_tool_dependencies
            
        Returns:
            Set of indices that must be kept together
        """
        required = {message_index}
        msg = messages[message_index]
        
        # If it's an AIMessage with tool calls, include all its tool responses
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                tc_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                if tc_id and tc_id in dependencies:
                    tool_idx = dependencies[tc_id].get('tool_message_index')
                    if tool_idx is not None:
                        required.add(tool_idx)
        
        # If it's a ToolMessage, include its AIMessage
        elif isinstance(msg, ToolMessage) and hasattr(msg, 'tool_call_id'):
            tc_id = msg.tool_call_id
            if tc_id in dependencies:
                ai_idx = dependencies[tc_id].get('ai_message_index')
                if ai_idx is not None:
                    required.add(ai_idx)
                    # Also include all other tool responses for this AIMessage
                    ai_msg = messages[ai_idx]
                    if hasattr(ai_msg, 'tool_calls') and ai_msg.tool_calls:
                        for tc in ai_msg.tool_calls:
                            other_tc_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                            if other_tc_id and other_tc_id in dependencies:
                                other_tool_idx = dependencies[other_tc_id].get('tool_message_index')
                                if other_tool_idx is not None:
                                    required.add(other_tool_idx)
        
        return required
    
    @staticmethod
    def create_atomic_groups(messages: List[BaseMessage]) -> List[List[int]]:
        """
        Group messages into atomic units that must be kept together
        
        Returns:
            List of groups, where each group is a list of message indices
        """
        dependencies = MessageIntegrityValidator.find_tool_dependencies(messages)
        processed = set()
        groups = []
        
        for i, msg in enumerate(messages):
            if i in processed:
                continue
            
            # Get all indices that must be kept with this message
            group_indices = MessageIntegrityValidator.get_required_indices(
                i, messages, dependencies
            )
            
            # Mark all as processed
            processed.update(group_indices)
            
            # Add group (sorted by index)
            groups.append(sorted(group_indices))
        
        return groups
    
    @staticmethod
    def validate_message_list(messages: List[BaseMessage]) -> Tuple[bool, List[str]]:
        """
        Validate that a message list maintains integrity
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        dependencies = MessageIntegrityValidator.find_tool_dependencies(messages)
        
        # Check for incomplete tool pairs
        for tc_id, info in dependencies.items():
            if info['tool_message_index'] is None:
                errors.append(
                    f"AIMessage at index {info['ai_message_index']} has tool_call {tc_id} "
                    f"without corresponding ToolMessage"
                )
        
        # Check for orphaned tool messages
        tool_message_ids = set()
        for i, msg in enumerate(messages):
            if isinstance(msg, ToolMessage) and hasattr(msg, 'tool_call_id'):
                tc_id = msg.tool_call_id
                if tc_id not in dependencies:
                    errors.append(
                        f"ToolMessage at index {i} with tool_call_id {tc_id} "
                        f"has no corresponding AIMessage"
                    )
        
        return len(errors) == 0, errors
    
    @staticmethod
    def ensure_integrity(
        selected_indices: Set[int],
        messages: List[BaseMessage]
    ) -> Set[int]:
        """
        Ensure integrity by adding any missing paired messages
        
        Args:
            selected_indices: Indices currently selected
            messages: Full message list
            
        Returns:
            Updated set of indices with integrity preserved
        """
        dependencies = MessageIntegrityValidator.find_tool_dependencies(messages)
        final_indices = selected_indices.copy()
        
        # Keep adding required indices until no more changes
        changed = True
        while changed:
            changed = False
            indices_to_add = set()
            
            for idx in final_indices:
                required = MessageIntegrityValidator.get_required_indices(
                    idx, messages, dependencies
                )
                new_indices = required - final_indices
                if new_indices:
                    indices_to_add.update(new_indices)
                    changed = True
            
            final_indices.update(indices_to_add)
        
        return final_indices


class IntegrityPreservingMixin:
    """
    Mixin class that adds integrity preservation to any trimming strategy
    
    Usage:
        class MyStrategy(IntegrityPreservingMixin):
            def apply_trimming_logic(self, messages):
                # Your trimming logic here
                return selected_indices
            
            def apply_trimming(self, messages):
                # This method is required by BaseContextHook
                selected_indices = self.apply_trimming_logic(messages)
                # Ensure integrity
                final_indices = self.ensure_message_integrity(selected_indices, messages)
                # Convert to messages
                trimmed_messages = [messages[i] for i in sorted(final_indices)]
                return trimmed_messages, excluded_info
    """
    
    def ensure_message_integrity(
        self,
        selected_indices: Set[int],
        messages: List[BaseMessage]
    ) -> Set[int]:
        """Ensure message integrity is preserved"""
        return MessageIntegrityValidator.ensure_integrity(selected_indices, messages)
    
    def validate_integrity(self, messages: List[BaseMessage]) -> bool:
        """Validate message integrity"""
        is_valid, errors = MessageIntegrityValidator.validate_message_list(messages)
        if not is_valid and hasattr(self, 'verbose') and self.verbose:
            print(f"[{self.__class__.__name__}] Integrity validation failed:")
            for error in errors:
                print(f"  - {error}")
        return is_valid
    
    def get_atomic_groups(self, messages: List[BaseMessage]) -> List[List[int]]:
        """Get atomic message groups"""
        return MessageIntegrityValidator.create_atomic_groups(messages)