"""
Pre-model hooks for ReAct agents to manage message history
"""

from typing import Any, Dict, List
from datetime import datetime, UTC

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage, SystemMessage
try:
    from langchain_core.messages import RemoveMessage
except ImportError:
    # For older versions, create a simple RemoveMessage class
    class RemoveMessage:
        def __init__(self, id: str):
            self.id = id

from .base import Message, MessageType, ContextConfig
from .manager import BrowserCopilotContextManager
from .true_sliding_window import create_true_sliding_window_hook


def create_sliding_window_hook(
    config: ContextConfig,
    verbose: bool = False
) -> callable:
    """
    Create a pre-model hook that applies sliding window context management
    
    Args:
        config: Context configuration
        verbose: Enable verbose logging
        
    Returns:
        Pre-model hook function
    """
    # DON'T create manager here - it needs to work directly with the messages
    
    def sliding_window_pre_model_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-model hook that manages message history with sliding window
        
        Args:
            state: Current graph state with messages
            
        Returns:
            Updated state with managed messages
        """
        messages = state.get("messages", [])
        
        if not messages:
            return {}
        
        # CRITICAL: We must preserve AIMessage/ToolMessage pairs
        # If an AIMessage has tool_calls, the corresponding ToolMessages must be kept
        # together to avoid "Bad Request" errors
        
        if verbose:
            print(f"\n[Sliding Window Hook] Processing {len(messages)} messages")
            # Calculate full state tokens
            full_state_tokens = sum(len(str(msg.content)) for msg in messages) // 4
            print(f"[Sliding Window Hook] Full state tokens: {full_state_tokens:,}")
            print(f"[Sliding Window Hook] Max window size: {config.window_size:,}")
            
            # Debug: Check what the strategy sees
            total_tokens_in_manager = sum(len(str(msg.content)) // 4 for msg in messages)
            print(f"[Sliding Window Hook] DEBUG: Total tokens being added to manager: {total_tokens_in_manager:,}")
        
        # Build tool call dependency map
        tool_call_pairs = {}  # Maps AIMessage index to ToolMessage indices
        tool_call_to_ai = {}  # Maps tool_call_id to AIMessage index
        
        for i, msg in enumerate(messages):
            if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_call_id = tool_call.get('id') if isinstance(tool_call, dict) else getattr(tool_call, 'id', None)
                    if tool_call_id:
                        tool_call_to_ai[tool_call_id] = i
                        if i not in tool_call_pairs:
                            tool_call_pairs[i] = []
            elif isinstance(msg, ToolMessage):
                tool_call_id = getattr(msg, 'tool_call_id', None)
                if tool_call_id and tool_call_id in tool_call_to_ai:
                    ai_idx = tool_call_to_ai[tool_call_id]
                    if ai_idx not in tool_call_pairs:
                        tool_call_pairs[ai_idx] = []
                    tool_call_pairs[ai_idx].append(i)
        
        if verbose and tool_call_pairs:
            print(f"[Sliding Window Hook] Found {len(tool_call_pairs)} AIMessage/ToolMessage pairs")
        
        # Clear context manager and add all messages
        manager.clear_context()
        
        # Convert LangChain messages to our format and add to manager
        # Store original messages for later reconstruction
        original_messages_map = {}
        
        for i, msg in enumerate(messages):
            msg_type = MessageType.USER  # Default
            content = str(msg.content) if hasattr(msg, 'content') else str(msg)
            tool_name = None
            
            if isinstance(msg, SystemMessage):
                msg_type = MessageType.SYSTEM
            elif isinstance(msg, AIMessage):
                msg_type = MessageType.ASSISTANT
            elif isinstance(msg, ToolMessage):
                msg_type = MessageType.TOOL_RESPONSE
                tool_name = getattr(msg, 'name', None)
            elif isinstance(msg, HumanMessage):
                msg_type = MessageType.USER
            
            # Store original message for reconstruction
            original_messages_map[i] = msg
            
            # Mark messages that are part of tool call pairs as critical
            preserve = False
            if i in tool_call_pairs or any(i in indices for indices in tool_call_pairs.values()):
                preserve = True
                
            # Calculate token count for this message
            token_count = len(content) // 4  # Simple approximation: 4 chars per token
            
            manager.add_message(Message(
                type=msg_type,
                content=content,
                timestamp=datetime.now(UTC),
                token_count=token_count,  # CRITICAL: Set token count!
                tool_name=tool_name,
                metadata={'original_index': i},  # Track original position
                preserve=preserve  # Preserve tool call pairs
            ))
        
        # Get processed messages
        processed = manager.get_context()
        
        if verbose:
            print(f"[Sliding Window Hook] DEBUG: Manager returned {len(processed)} messages")
            if hasattr(manager.strategy, 'metrics'):
                metrics = manager.strategy.metrics
                print(f"[Sliding Window Hook] DEBUG: Strategy metrics - original: {metrics.original_messages}, processed: {metrics.processed_messages}")
        
        # Convert back to LangChain messages first (needed for verbose output)
        new_messages = []
        for msg in processed:
            # Try to use original message if available
            if hasattr(msg, 'metadata') and msg.metadata and 'original_index' in msg.metadata:
                orig_idx = msg.metadata['original_index']
                if orig_idx in original_messages_map:
                    # Use the original message to preserve all attributes
                    original_msg = original_messages_map[orig_idx]
                    new_messages.append(original_msg)
                    continue
            
            # Fallback to creating new messages
            # This should rarely happen, but we need safe fallbacks
            if verbose:
                print(f"[Sliding Window Hook] WARNING: Creating new message for {msg.type}")
            
            if msg.type == MessageType.SYSTEM:
                new_messages.append(SystemMessage(content=msg.content))
            elif msg.type == MessageType.ASSISTANT:
                new_messages.append(AIMessage(content=msg.content))
            elif msg.type == MessageType.TOOL_RESPONSE:
                # For tool responses without original, we need to handle carefully
                # Check if this is a critical issue
                if verbose:
                    print(f"[Sliding Window Hook] ERROR: ToolMessage without original - this may cause Bad Request")
                # Convert to AIMessage to avoid invalid tool_call_id
                new_messages.append(AIMessage(
                    content=f"[Tool Response] {msg.content}",
                    additional_kwargs={"note": "Converted from ToolMessage due to missing tool_call_id"}
                ))
            else:
                new_messages.append(HumanMessage(content=msg.content))
        
        if verbose:
            metrics = manager.get_metrics()
            # Calculate tokens for comparison
            original_tokens = sum(len(str(msg.content)) for msg in messages) // 4
            processed_tokens = sum(len(str(msg.content)) for msg in new_messages) // 4
            
            print(f"[Sliding Window Hook] === RESULTS ===")
            print(f"[Sliding Window Hook] State messages: {len(messages)} → LLM messages: {len(new_messages)}")
            print(f"[Sliding Window Hook] State tokens: {original_tokens:,} → LLM tokens: {processed_tokens:,}")
            print(f"[Sliding Window Hook] Message reduction: {((len(messages) - len(new_messages)) / len(messages) * 100):.1f}% ({len(messages) - len(new_messages)} messages removed)")
            print(f"[Sliding Window Hook] Token reduction: {metrics['token_metrics']['reduction_percentage']:.1f}% ({original_tokens - processed_tokens:,} tokens saved)")
            
            # Debug: Show message types being processed
            msg_types = {}
            for msg in messages:
                msg_type = type(msg).__name__
                msg_types[msg_type] = msg_types.get(msg_type, 0) + 1
            print(f"[Sliding Window Hook] Original message types: {msg_types}")
            
            # Check if we're preserving all original messages
            preserved_count = sum(1 for msg in processed if hasattr(msg, 'metadata') and msg.metadata and 'original_index' in msg.metadata)
            print(f"[Sliding Window Hook] Preserved {preserved_count}/{len(processed)} original messages")
            
            # Check which messages were dropped
            if len(processed) < len(messages):
                preserved_indices = {msg.metadata.get('original_index') for msg in processed if hasattr(msg, 'metadata') and msg.metadata}
                dropped_indices = []
                for i in range(len(messages)):
                    if i not in preserved_indices:
                        dropped_indices.append(i)
                        msg = messages[i]
                        print(f"[Sliding Window Hook] DROPPED message {i}: {type(msg).__name__}")
                        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                            print(f"  WARNING: Dropped AIMessage with tool_calls!")
                        elif isinstance(msg, ToolMessage):
                            print(f"  WARNING: Dropped ToolMessage with tool_call_id={getattr(msg, 'tool_call_id', 'N/A')}")
        
        # Validate messages before returning
        if verbose:
            # Check for any potential issues
            for i, msg in enumerate(new_messages):
                if isinstance(msg, ToolMessage):
                    if not hasattr(msg, 'tool_call_id') or not msg.tool_call_id:
                        print(f"[Sliding Window Hook] ERROR: ToolMessage at index {i} has invalid tool_call_id: {getattr(msg, 'tool_call_id', 'MISSING')}")
        
        # Return the new messages directly using llm_input_messages
        # This provides the trimmed messages to the LLM without modifying state
        return {
            "llm_input_messages": new_messages
        }
    
    # Store manager reference for metrics access
    sliding_window_pre_model_hook.context_manager = manager
    
    return sliding_window_pre_model_hook


def create_no_op_hook() -> callable:
    """
    Create a no-op pre-model hook that doesn't modify messages
    
    Returns:
        Pre-model hook function that returns state unchanged
    """
    def no_op_pre_model_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """No-op hook that doesn't modify messages"""
        # Return empty dict to keep messages unchanged
        return {}
    
    return no_op_pre_model_hook


def create_langchain_trim_hook(
    config: ContextConfig,
    verbose: bool = False
) -> callable:
    """
    Create a pre-model hook using LangChain's trim_messages
    
    This is a simpler approach that directly uses LangChain's
    built-in message trimming without our complex conversion.
    
    Args:
        config: Context configuration
        verbose: Enable verbose logging
        
    Returns:
        Pre-model hook function
    """
    from langchain_core.messages.utils import trim_messages
    
    def langchain_trim_hook(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-model hook using LangChain's trim_messages directly
        """
        messages = state.get("messages", [])
        
        if verbose:
            print(f"\n[LangChain Trim Hook] Processing {len(messages)} messages")
            print(f"[LangChain Trim Hook] Max tokens: {config.window_size}")
            # Calculate actual token count
            total_tokens = sum(len(str(msg.content)) for msg in messages) // 4
            print(f"[LangChain Trim Hook] Full state tokens: {total_tokens:,}")
        
        # Use LangChain's trim_messages directly
        # Import the token counter from langchain
        from langchain_core.messages.utils import message_chunk_to_message
        
        # Define a simple token counter (approximate)
        def token_counter(messages):
            # Simple approximation: ~4 chars per token
            total_chars = sum(len(str(msg.content)) for msg in messages)
            return total_chars // 4
        
        # Try trimming with constraints first
        try:
            trimmed_messages = trim_messages(
                messages,
                strategy="last",  # Keep most recent messages
                max_tokens=config.window_size,
                token_counter=token_counter,
                # Ensure we start with human message
                start_on="human",
                # End on human or tool to preserve complete interactions
                end_on=("human", "tool"),
            )
        except Exception as e:
            if verbose:
                print(f"[LangChain Trim Hook] trim_messages with constraints failed: {e}")
            trimmed_messages = []
        
        # If constraints were too restrictive, try without them
        if not trimmed_messages and messages:
            if verbose:
                print(f"[LangChain Trim Hook] Retrying without start/end constraints")
            try:
                trimmed_messages = trim_messages(
                    messages,
                    strategy="last",
                    max_tokens=config.window_size,
                    token_counter=token_counter,
                    # No start_on or end_on constraints
                )
            except Exception as e:
                if verbose:
                    print(f"[LangChain Trim Hook] trim_messages without constraints also failed: {e}")
                trimmed_messages = []
        
        # CRITICAL: If trim_messages returns empty list, we need to provide some context
        if not trimmed_messages and messages:
            if verbose:
                print(f"[LangChain Trim Hook] WARNING: trim_messages returned empty list!")
                print(f"[LangChain Trim Hook] Falling back to tool-pair-aware selection")
            
            # Fallback: Keep messages while preserving tool pairs
            # First, identify all tool call pairs
            tool_call_to_ai = {}  # Maps tool_call_id to AIMessage index
            
            for i, msg in enumerate(messages):
                if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_call_id = tool_call.get('id') if isinstance(tool_call, dict) else getattr(tool_call, 'id', None)
                        if tool_call_id:
                            tool_call_to_ai[tool_call_id] = i
            
            # Start with the first message (original prompt)
            fallback_messages = [messages[0]] if messages else []
            included_indices = {0} if messages else set()
            
            # Work backwards from the end, keeping complete tool pairs
            target_count = min(6, len(messages))  # Try to keep ~6 messages total
            
            for i in range(len(messages) - 1, 0, -1):  # Skip first message (already included)
                if len(fallback_messages) >= target_count:
                    break
                
                msg = messages[i]
                
                # If this is a ToolMessage, we need its corresponding AIMessage
                if isinstance(msg, ToolMessage) and hasattr(msg, 'tool_call_id'):
                    tool_call_id = msg.tool_call_id
                    if tool_call_id in tool_call_to_ai:
                        ai_idx = tool_call_to_ai[tool_call_id]
                        # Add the AIMessage first if not already included
                        if ai_idx not in included_indices:
                            fallback_messages.insert(1, messages[ai_idx])  # Insert after first message
                            included_indices.add(ai_idx)
                
                # Add this message if not already included
                if i not in included_indices:
                    fallback_messages.append(msg)
                    included_indices.add(i)
            
            trimmed_messages = fallback_messages
            
            # CRITICAL: Validate that all tool pairs are complete
            # If an AIMessage has tool_calls, ensure all corresponding ToolMessages are present
            if verbose:
                print(f"[LangChain Trim Hook] Validating tool pairs in fallback messages")
            
            # Build a map of what we have
            included_tool_ids = set()
            for msg in trimmed_messages:
                if isinstance(msg, ToolMessage) and hasattr(msg, 'tool_call_id'):
                    included_tool_ids.add(msg.tool_call_id)
            
            # Check for incomplete pairs and remove AIMessages with missing tool responses
            validated_messages = []
            for msg in trimmed_messages:
                if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                    # Check if all tool calls have responses
                    missing_responses = False
                    for tc in msg.tool_calls:
                        tc_id = tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', None)
                        if tc_id and tc_id not in included_tool_ids:
                            missing_responses = True
                            if verbose:
                                print(f"[LangChain Trim Hook] WARNING: Removing AIMessage with unmatched tool_call_id: {tc_id}")
                            break
                    
                    if not missing_responses:
                        validated_messages.append(msg)
                else:
                    validated_messages.append(msg)
            
            trimmed_messages = validated_messages
        
        if verbose:
            trimmed_tokens = sum(len(str(msg.content)) for msg in trimmed_messages) // 4
            original_tokens = sum(len(str(msg.content)) for msg in messages) // 4
            
            print(f"[LangChain Trim Hook] === RESULTS ===")
            print(f"[LangChain Trim Hook] State messages: {len(messages)} → LLM messages: {len(trimmed_messages)}")
            print(f"[LangChain Trim Hook] State tokens: {original_tokens:,} → LLM tokens: {trimmed_tokens:,}")
            
            msg_reduction = ((len(messages) - len(trimmed_messages)) / len(messages) * 100) if messages else 0
            token_reduction = ((original_tokens - trimmed_tokens) / original_tokens * 100) if original_tokens else 0
            
            print(f"[LangChain Trim Hook] Message reduction: {msg_reduction:.1f}% ({len(messages) - len(trimmed_messages)} messages removed)")
            print(f"[LangChain Trim Hook] Token reduction: {token_reduction:.1f}% ({original_tokens - trimmed_tokens:,} tokens saved)")
        
        return {"llm_input_messages": trimmed_messages}
    
    return langchain_trim_hook