# Context Management Architecture

## Overview

The context management system uses the **Strategy Pattern** to provide different approaches for managing message history in ReAct agents. This design allows for clean separation of concerns and easy addition of new strategies.

## Directory Structure

```
context_management/
├── __init__.py           # Package exports
├── base.py               # Core data structures (ContextConfig, etc.)
├── hooks.py              # Factory for creating pre-model hooks
├── strategies/           # Strategy implementations
│   ├── __init__.py
│   ├── base.py          # Abstract base class for strategies
│   ├── no_op.py         # No-operation strategy
│   ├── sliding_window.py # True sliding window strategy
│   └── smart_trim.py     # Smart trimming strategy
├── analyzer.py          # Message analysis utilities
├── metrics.py           # Context metrics tracking
└── debug_formatter.py   # Debug output formatting
```

## Architecture

### Strategy Pattern Implementation

1. **Base Strategy** (`strategies/base.py`):
   - Defines the `ContextStrategy` abstract base class
   - All strategies must implement:
     - `create_hook()` - Returns a pre-model hook function
     - `get_name()` - Returns the strategy name
     - `get_description()` - Returns a description
   - Provides common utilities like `count_tokens()`

2. **Concrete Strategies**:
   - **NoOpStrategy**: Passes messages through unchanged
   - **SlidingWindowStrategy**: Preserves first N Human/System messages + last N messages + middle filling
   - **SmartTrimStrategy**: Analyzes message importance and size

3. **Hook Factory** (`hooks.py`):
   - `create_context_hook()` - Main factory function
   - `get_strategy_info()` - Get information about a strategy
   - `list_strategies()` - List all available strategies

### Usage in Agent

```python
from browser_copilot.context_management import create_context_hook, ContextConfig

# Create configuration
config = ContextConfig(
    window_size=25000,
    preserve_first_n=2
)

# Create hook
hook = create_context_hook(
    strategy="sliding-window",
    config=config,
    verbose=True
)

# Use with ReAct agent
agent = create_react_agent(llm, tools, pre_model_hook=hook)
```

## Adding New Strategies

To add a new strategy:

1. Create a new file in `strategies/` (e.g., `strategies/my_strategy.py`)
2. Implement the `ContextStrategy` interface:

```python
from .base import ContextStrategy, PreModelHook

class MyStrategy(ContextStrategy):
    def create_hook(self) -> PreModelHook:
        def my_hook(state: Dict[str, Any]) -> Dict[str, Any]:
            # Your logic here
            return {"llm_input_messages": trimmed_messages}
        return my_hook

    def get_name(self) -> str:
        return "my-strategy"

    def get_description(self) -> str:
        return "Description of what this strategy does"
```

3. Add to `strategies/__init__.py`:
```python
from .my_strategy import MyStrategy
```

4. Add to the factory in `hooks.py`:
```python
strategy_classes = {
    # ... existing strategies ...
    "my-strategy": MyStrategy,
}
```

## Design Decisions

1. **Strategy Pattern**: Provides clear separation between different approaches
2. **Factory Pattern**: Centralizes strategy creation and validation
3. **Protocol for Hooks**: Uses Python's `Protocol` for type safety
4. **Stateless Hooks**: Each hook invocation is independent
5. **Configuration Validation**: Strategies validate their own config

## Benefits

- **Extensibility**: Easy to add new strategies
- **Testability**: Each strategy can be tested independently
- **Maintainability**: Clear separation of concerns
- **Type Safety**: Uses protocols and type hints throughout
- **Performance**: Minimal overhead from the pattern
