"""
Base hook implementation with common debug formatting

All context management strategies should use this base for consistent output.
"""

from typing import Any, Dict, List, Tuple, Optional, Set
from abc import ABC, abstractmethod
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage

from .base import ContextConfig
from .debug_formatter import ContextDebugFormatter
from .message_integrity import MessageIntegrityValidator, IntegrityPreservingMixin


class BaseContextHook(IntegrityPreservingMixin, ABC):
    """Base class for context management hooks with debug formatting and integrity preservation"""
    
    def __init__(
        self, 
        config: ContextConfig,
        verbose: bool = False,
        formatter: Optional[ContextDebugFormatter] = None
    ):
        self.config = config
        self.verbose = verbose
        self.formatter = formatter or ContextDebugFormatter(use_rich=False)
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Main hook entry point with consistent debug output and integrity preservation"""
        messages = state.get("messages", [])
        
        if not messages:
            return {}
        
        # Show header if verbose
        if self.verbose:
            self.formatter.format_hook_header(
                self.get_strategy_name(),
                len(messages),
                self.config.window_size
            )
        
        # Analyze messages if verbose
        if self.verbose:
            self.formatter.format_message_analysis(messages)
        
        # Apply strategy-specific trimming
        selected_indices = self.apply_trimming_logic(messages)
        
        # CRITICAL: Ensure message integrity (unless explicitly disabled)
        if not self.disable_integrity_check():
            final_indices = self.ensure_message_integrity(selected_indices, messages)
            if self.verbose and len(final_indices) > len(selected_indices):
                added_count = len(final_indices) - len(selected_indices)
                self.formatter.format_info(
                    f"Added {added_count} messages to preserve tool pair integrity"
                )
        else:
            final_indices = selected_indices
        
        # Convert indices to messages
        trimmed_messages = [messages[i] for i in sorted(final_indices)]
        
        # Calculate excluded messages info
        excluded_info = [
            (i, messages[i], self._count_tokens(messages[i]))
            for i in range(len(messages))
            if i not in final_indices
        ]
        
        # Show results if verbose
        if self.verbose:
            original_tokens = self._count_total_tokens(messages)
            trimmed_tokens = self._count_total_tokens(trimmed_messages)
            
            self.formatter.format_results(
                original_count=len(messages),
                trimmed_count=len(trimmed_messages),
                original_tokens=original_tokens,
                trimmed_tokens=trimmed_tokens,
                excluded_messages=excluded_info
            )
            
            # Validate tool pairs
            is_valid, errors = MessageIntegrityValidator.validate_message_list(trimmed_messages)
            if not is_valid:
                self.formatter.format_tool_pair_validation(False, "; ".join(errors))
            else:
                self.formatter.format_tool_pair_validation(True)
        
        return {"llm_input_messages": trimmed_messages}
    
    @abstractmethod
    def apply_trimming_logic(
        self, 
        messages: List[BaseMessage]
    ) -> Set[int]:
        """
        Apply strategy-specific trimming logic
        
        Returns:
            Set of indices to keep (before integrity preservation)
        """
        pass
    
    def disable_integrity_check(self) -> bool:
        """
        Override to disable integrity checking for specific strategies
        
        Returns:
            True to disable integrity checking (e.g., for no-op strategy)
        """
        return False
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get the display name for this strategy"""
        pass
    
    def _count_total_tokens(self, messages: List[BaseMessage]) -> int:
        """Count total tokens in messages"""
        return sum(self._count_tokens(msg) for msg in messages)
    
    def _count_tokens(self, msg: BaseMessage) -> int:
        """Count tokens in a single message"""
        if msg.content:
            return len(str(msg.content)) // 4
        return 0
    
    def _get_token_count_for_indices(self, indices: Set[int], messages: List[BaseMessage]) -> int:
        """Get total token count for a set of message indices"""
        return sum(self._count_tokens(messages[i]) for i in indices)


def create_hook_wrapper(
    strategy_class: type,
    strategy_name: str
) -> callable:
    """Create a hook factory function for a strategy class"""
    
    def hook_factory(
        config: ContextConfig,
        verbose: bool = False,
        formatter: Optional[ContextDebugFormatter] = None
    ) -> callable:
        """Factory function that creates the hook instance"""
        strategy = strategy_class(config, verbose, formatter)
        return strategy
    
    return hook_factory