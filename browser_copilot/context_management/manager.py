"""
Context manager implementation
"""

from datetime import datetime, UTC
from typing import Any, Optional

from .analyzer import MessageAnalyzer
from .base import ContextConfig, ContextManager, Message
from .metrics import ContextMetrics
from .strategies import NoOpStrategy, SlidingWindowStrategy


class BrowserCopilotContextManager(ContextManager):
    """
    Context manager for Browser Copilot that uses pluggable strategies
    """
    
    def __init__(
        self, 
        config: Optional[ContextConfig] = None,
        strategy: str = "sliding-window",
        model: str = "gpt-4"
    ):
        """
        Initialize the context manager
        
        Args:
            config: Context configuration (uses defaults if not provided)
            strategy: Strategy to use ("no-op", "sliding-window")
            model: Model name for token counting
        """
        super().__init__(config or ContextConfig())
        
        # Initialize components
        self.analyzer = MessageAnalyzer(model=model)
        self.metrics = ContextMetrics(strategy_name=strategy)
        
        # Select strategy
        self.strategy = self._create_strategy(strategy)
        
        # Track message history
        self._raw_messages: list[Message] = []
        self._processed_messages: list[Message] = []
    
    def _create_strategy(self, strategy_name: str):
        """Create the specified strategy instance"""
        from .strategies.langchain_trim import LangChainTrimStrategy, AdvancedLangChainTrimStrategy
        
        strategies = {
            "no-op": NoOpStrategy,
            "sliding-window": SlidingWindowStrategy,
            "langchain-trim": LangChainTrimStrategy,
            "langchain-trim-advanced": AdvancedLangChainTrimStrategy,
        }
        
        strategy_class = strategies.get(strategy_name)
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        return strategy_class()
    
    def add_message(self, message: Message) -> None:
        """
        Add a message to the context
        
        Args:
            message: Message to add
        """
        # Analyze message first
        analyzed_message = self.analyzer.analyze_message(message)
        
        # Add to raw history
        self._raw_messages.append(analyzed_message)
        
        # Update total tokens
        self._total_tokens += analyzed_message.token_count
        
        # Update metrics
        if analyzed_message.token_count > self.metrics.max_message_tokens:
            self.metrics.max_message_tokens = analyzed_message.token_count
    
    def get_context(self) -> list[Message]:
        """
        Get the current context after processing
        
        Returns:
            Processed list of messages
        """
        if not self._raw_messages:
            return []
        
        # Process messages through strategy
        start_time = datetime.now(UTC)
        
        self._processed_messages = self.strategy.process_messages(
            self._raw_messages.copy(), self.config
        )
        
        # Update metrics
        processing_time = (datetime.now(UTC) - start_time).total_seconds() * 1000
        self._update_metrics(processing_time)
        
        return self._processed_messages
    
    def _update_metrics(self, processing_time_ms: float) -> None:
        """Update context manager metrics"""
        self.metrics.original_messages = len(self._raw_messages)
        self.metrics.original_tokens = self._total_tokens
        self.metrics.processed_messages = len(self._processed_messages)
        self.metrics.processed_tokens = sum(
            msg.token_count for msg in self._processed_messages
        )
        self.metrics.processing_time_ms = processing_time_ms
        self.metrics.calculate_savings()
        
        # Get strategy-specific metrics
        if hasattr(self.strategy, 'get_metrics'):
            strategy_metrics = self.strategy.get_metrics()
            # Merge relevant metrics
            if 'message_metrics' in strategy_metrics:
                msg_metrics = strategy_metrics['message_metrics']
                self.metrics.messages_preserved = msg_metrics.get('preserved', 0)
                self.metrics.critical_messages_kept = msg_metrics.get('critical_kept', 0)
    
    def get_metrics(self) -> dict[str, Any]:
        """
        Get context management metrics
        
        Returns:
            Dictionary of metrics
        """
        return self.metrics.to_dict()
    
    def add_messages(self, messages: list[Message]) -> None:
        """
        Add multiple messages at once
        
        Args:
            messages: List of messages to add
        """
        for message in messages:
            self.add_message(message)
    
    def clear_context(self) -> None:
        """Clear all messages and reset state"""
        self._raw_messages.clear()
        self._processed_messages.clear()
        self._total_tokens = 0
        self.metrics = ContextMetrics(strategy_name=self.metrics.strategy_name)
    
    def get_summary(self) -> str:
        """
        Get a summary of the current context state
        
        Returns:
            Human-readable summary
        """
        if not self._raw_messages:
            return "Context is empty"
        
        processed = self.get_context()
        
        summary = f"""Context Summary:
- Strategy: {self.metrics.strategy_name}
- Original: {len(self._raw_messages)} messages ({self._total_tokens:,} tokens)
- Processed: {len(processed)} messages ({self.metrics.processed_tokens:,} tokens)
- Reduction: {self.metrics.reduction_percentage:.1f}% ({self.metrics.tokens_saved:,} tokens saved)
- Processing time: {self.metrics.processing_time_ms:.1f}ms
"""
        
        if self.metrics.critical_messages_kept > 0:
            summary += f"- Critical messages preserved: {self.metrics.critical_messages_kept}\n"
        
        return summary