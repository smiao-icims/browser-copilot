"""
Context Management Strategy Registry

Centralized registry for all context management strategies.
This replaces the scattered implementation across multiple files.
"""

from typing import Dict, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .base import ContextConfig
from .debug_formatter import ContextDebugFormatter


class StrategyType(Enum):
    """Available context management strategies"""
    NO_OP = "no-op"
    SMART_TRIM = "smart-trim"
    SLIDING_WINDOW = "sliding-window"
    INTEGRITY_FIRST = "integrity-first"
    
    # Deprecated strategies (kept for backward compatibility)
    LANGCHAIN_TRIM = "langchain-trim"
    REVERSE_TRIM = "reverse-trim"
    SMART_REVERSE = "smart-reverse"
    LAST_N = "last-n"


@dataclass
class StrategyInfo:
    """Information about a context strategy"""
    name: str
    description: str
    hook_factory: Callable
    recommended: bool
    use_cases: list[str]
    deprecated: bool = False
    deprecation_reason: Optional[str] = None


class StrategyRegistry:
    """Registry for context management strategies"""
    
    def __init__(self):
        self._strategies: Dict[str, StrategyInfo] = {}
        self._register_core_strategies()
    
    def _register_core_strategies(self):
        """Register the core recommended strategies"""
        
        # Import only the strategies we're keeping
        from .strategies.noop import create_no_op_hook
        from .react_hooks_smart import create_smart_trim_hook
        from .react_hooks import create_sliding_window_hook
        from .react_hooks_integrity import create_integrity_first_hook
        
        # No-op strategy
        self.register(
            StrategyType.NO_OP.value,
            StrategyInfo(
                name="No Operation",
                description="Baseline strategy that performs no trimming",
                hook_factory=create_no_op_hook,
                recommended=True,
                use_cases=["baseline comparison", "debugging", "small contexts"]
            )
        )
        
        # Smart trim strategy
        self.register(
            StrategyType.SMART_TRIM.value,
            StrategyInfo(
                name="Smart Trim",
                description="Intelligent trimming based on message size analysis",
                hook_factory=create_smart_trim_hook,
                recommended=True,
                use_cases=["general purpose", "large message handling", "balanced performance"]
            )
        )
        
        # Sliding window strategy
        self.register(
            StrategyType.SLIDING_WINDOW.value,
            StrategyInfo(
                name="Sliding Window",
                description="Traditional sliding window with preservation rules",
                hook_factory=create_sliding_window_hook,
                recommended=True,
                use_cases=["predictable behavior", "simple use cases", "fallback option"]
            )
        )
        
        # Integrity first strategy
        self.register(
            StrategyType.INTEGRITY_FIRST.value,
            StrategyInfo(
                name="Integrity First",
                description="Prioritizes message integrity over token limits",
                hook_factory=create_integrity_first_hook,
                recommended=True,
                use_cases=["critical workflows", "tool-heavy interactions", "debugging"]
            )
        )
    
    def register(self, key: str, strategy: StrategyInfo):
        """Register a strategy"""
        self._strategies[key] = strategy
    
    def get_strategy(self, key: str) -> Optional[StrategyInfo]:
        """Get a strategy by key"""
        strategy = self._strategies.get(key)
        
        if strategy and strategy.deprecated:
            print(f"⚠️  Warning: Strategy '{key}' is deprecated. {strategy.deprecation_reason}")
            print(f"   Recommended alternatives: {self.get_recommended_strategies()}")
        
        return strategy
    
    def get_hook(
        self, 
        strategy_key: str, 
        config: ContextConfig,
        verbose: bool = False,
        use_rich: Optional[bool] = None
    ) -> Callable:
        """Get a configured hook for the strategy"""
        strategy = self.get_strategy(strategy_key)
        
        if not strategy:
            raise ValueError(f"Unknown strategy: {strategy_key}")
        
        # Create debug formatter (shared across all strategies)
        if use_rich is None:
            import os
            use_rich = os.isatty(1) and not os.getenv('CI')
        
        formatter = ContextDebugFormatter(use_rich=use_rich)
        
        # Create hook with formatter
        if strategy_key == StrategyType.NO_OP.value:
            return strategy.hook_factory()
        else:
            # All other strategies support verbose and formatter
            return strategy.hook_factory(config, verbose, formatter)
    
    def get_recommended_strategies(self) -> list[str]:
        """Get list of recommended strategies"""
        return [
            key for key, info in self._strategies.items() 
            if info.recommended and not info.deprecated
        ]
    
    def list_strategies(self, include_deprecated: bool = False) -> Dict[str, StrategyInfo]:
        """List all available strategies"""
        if include_deprecated:
            return self._strategies.copy()
        
        return {
            key: info for key, info in self._strategies.items()
            if not info.deprecated
        }


# Global registry instance
strategy_registry = StrategyRegistry()


def register_deprecated_strategies():
    """Register deprecated strategies for backward compatibility"""
    
    # Import deprecated strategies
    from .react_hooks import create_langchain_trim_hook
    from .react_hooks_reverse import create_reverse_trim_hook, create_smart_reverse_hook
    from .react_hooks_safe import create_last_n_hook
    
    # Register with deprecation warnings
    strategy_registry.register(
        StrategyType.LANGCHAIN_TRIM.value,
        StrategyInfo(
            name="LangChain Trim",
            description="Uses LangChain's trim_messages utility",
            hook_factory=create_langchain_trim_hook,
            recommended=False,
            deprecated=True,
            deprecation_reason="Use 'smart-trim' instead - handles edge cases better",
            use_cases=[]
        )
    )
    
    strategy_registry.register(
        StrategyType.REVERSE_TRIM.value,
        StrategyInfo(
            name="Reverse Trim",
            description="Builds context from most recent messages",
            hook_factory=create_reverse_trim_hook,
            recommended=False,
            deprecated=True,
            deprecation_reason="Use 'smart-trim' instead - more intelligent selection",
            use_cases=[]
        )
    )