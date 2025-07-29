"""
Refactored context management strategies with integrity preservation

All strategies (except no-op) automatically preserve message integrity.
"""

from typing import Set, List, Optional
from langchain_core.messages import BaseMessage

from .base import ContextConfig
from .base_hook import BaseContextHook
from .debug_formatter import ContextDebugFormatter


class NoOpStrategy(BaseContextHook):
    """No-operation strategy - returns all messages unchanged"""
    
    def get_strategy_name(self) -> str:
        return "No-Op Strategy"
    
    def apply_trimming_logic(self, messages: List[BaseMessage]) -> Set[int]:
        """Keep all messages"""
        return set(range(len(messages)))
    
    def disable_integrity_check(self) -> bool:
        """No-op doesn't need integrity checking"""
        return True


class SmartTrimStrategy(BaseContextHook):
    """Smart trimming based on individual message size analysis"""
    
    def get_strategy_name(self) -> str:
        return "Smart Trim Strategy"
    
    def apply_trimming_logic(self, messages: List[BaseMessage]) -> Set[int]:
        """Apply smart trimming logic"""
        if not messages:
            return set()
        
        # Always include first message
        selected = {0}
        token_count = self._count_tokens(messages[0])
        
        # Analyze message sizes
        message_sizes = [(i, self._count_tokens(msg)) for i, msg in enumerate(messages)]
        
        # Define max size for a single message (10% of budget)
        max_single_message = self.config.window_size // 10
        
        # Work backwards, adding messages that fit
        for i in range(len(messages) - 1, 0, -1):
            if i in selected:
                continue
            
            msg_tokens = message_sizes[i][1]
            
            # Skip very large messages unless they're part of a tool pair
            # (integrity preservation will add them back if needed)
            if msg_tokens > max_single_message:
                if self.verbose:
                    self.formatter.format_warning(
                        f"Skipping large message {i} ({msg_tokens} tokens)"
                    )
                continue
            
            # Check if adding would exceed budget
            if token_count + msg_tokens > self.config.window_size:
                break
            
            selected.add(i)
            token_count += msg_tokens
        
        return selected


class SlidingWindowStrategy(BaseContextHook):
    """Traditional sliding window with preservation rules"""
    
    def get_strategy_name(self) -> str:
        return "Sliding Window Strategy"
    
    def apply_trimming_logic(self, messages: List[BaseMessage]) -> Set[int]:
        """Apply sliding window logic"""
        if not messages:
            return set()
        
        n = len(messages)
        
        # Preserve first N and last M messages
        preserve_first = min(self.config.preserve_first_n, n)
        preserve_last = min(self.config.preserve_last_n, n)
        
        # Start with preserved messages
        selected = set()
        
        # Add first N
        for i in range(preserve_first):
            selected.add(i)
        
        # Add last M
        for i in range(max(preserve_first, n - preserve_last), n):
            selected.add(i)
        
        # Calculate tokens so far
        token_count = self._get_token_count_for_indices(selected, messages)
        
        # Add messages from the middle if we have budget
        for i in range(preserve_first, n - preserve_last):
            if i not in selected:
                msg_tokens = self._count_tokens(messages[i])
                if token_count + msg_tokens <= self.config.window_size:
                    selected.add(i)
                    token_count += msg_tokens
        
        return selected


class LangChainEnhancedStrategy(BaseContextHook):
    """LangChain trim_messages with automatic integrity preservation"""
    
    def get_strategy_name(self) -> str:
        return "LangChain Enhanced Strategy"
    
    def apply_trimming_logic(self, messages: List[BaseMessage]) -> Set[int]:
        """Apply LangChain trimming logic"""
        from langchain_core.messages.utils import trim_messages
        
        if not messages:
            return set()
        
        # Token counter for LangChain
        def token_counter(msgs):
            return sum(len(str(msg.content)) for msg in msgs if msg.content) // 4
        
        # Try LangChain's trim_messages
        try:
            trimmed = trim_messages(
                messages,
                strategy="last",
                max_tokens=self.config.window_size,
                token_counter=token_counter,
                start_on="human",
                end_on=("human", "tool"),
                include_system=True
            )
            
            # Convert to indices
            selected = set()
            for i, msg in enumerate(messages):
                if msg in trimmed:
                    selected.add(i)
            
            return selected
            
        except Exception as e:
            if self.verbose:
                self.formatter.format_warning(f"LangChain trim failed: {e}")
            
            # Fallback to simple last-N
            return self._fallback_trimming(messages)
    
    def _fallback_trimming(self, messages: List[BaseMessage]) -> Set[int]:
        """Simple fallback when LangChain fails"""
        if not messages:
            return set()
        
        # Always keep first message
        selected = {0}
        token_count = self._count_tokens(messages[0])
        
        # Add from the end
        for i in range(len(messages) - 1, 0, -1):
            msg_tokens = self._count_tokens(messages[i])
            if token_count + msg_tokens > self.config.window_size:
                break
            selected.add(i)
            token_count += msg_tokens
        
        return selected


# Factory functions for backward compatibility
def create_no_op_strategy(
    config: Optional[ContextConfig] = None,
    verbose: bool = False,
    formatter: Optional[ContextDebugFormatter] = None
) -> BaseContextHook:
    """Create no-op strategy"""
    # No-op doesn't need config
    config = config or ContextConfig(window_size=float('inf'))
    return NoOpStrategy(config, verbose, formatter)


def create_smart_trim_strategy(
    config: ContextConfig,
    verbose: bool = False,
    formatter: Optional[ContextDebugFormatter] = None
) -> BaseContextHook:
    """Create smart trim strategy with integrity preservation"""
    return SmartTrimStrategy(config, verbose, formatter)


def create_sliding_window_strategy(
    config: ContextConfig,
    verbose: bool = False,
    formatter: Optional[ContextDebugFormatter] = None
) -> BaseContextHook:
    """Create sliding window strategy with integrity preservation"""
    return SlidingWindowStrategy(config, verbose, formatter)


def create_langchain_enhanced_strategy(
    config: ContextConfig,
    verbose: bool = False,
    formatter: Optional[ContextDebugFormatter] = None
) -> BaseContextHook:
    """Create LangChain-based strategy with integrity preservation"""
    return LangChainEnhancedStrategy(config, verbose, formatter)