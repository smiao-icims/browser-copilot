# Context Management Strategy Consolidation Plan

## Current State

We currently have **8 different strategy implementations** across multiple files, making maintenance difficult and debug output inconsistent.

## Consolidation Goals

1. **Reduce to 4 core strategies** that cover all use cases
2. **Standardize debug output** using the ContextDebugFormatter
3. **Simplify the codebase** for easier maintenance
4. **Improve user experience** with clearer strategy selection

## Recommended Core Strategies

**IMPORTANT**: All strategies (except no-op) now automatically preserve message integrity, ensuring AIMessage/ToolMessage pairs are never broken.

### 1. **no-op** (Baseline)
- **Purpose**: Baseline comparison, no trimming
- **Integrity**: Disabled (returns all messages unchanged)
- **Use Cases**: 
  - Performance benchmarking
  - Debugging
  - Small contexts that don't need trimming
- **Keep Because**: Essential for comparison

### 2. **smart-trim** (Recommended Default)
- **Purpose**: Intelligent trimming based on message size analysis
- **Integrity**: ✅ Automatically preserved
- **Use Cases**:
  - General purpose usage
  - Handles large messages intelligently
  - Your testing shows 25K works well for iCIMS
- **Keep Because**: Best balance of performance and intelligence

### 3. **sliding-window** (Simple & Predictable)
- **Purpose**: Traditional sliding window with preservation rules
- **Integrity**: ✅ Automatically preserved
- **Use Cases**:
  - When predictable behavior is needed
  - Simple applications
  - Fallback option
- **Keep Because**: Well-understood, predictable behavior

### 4. **langchain-enhanced** (LangChain with Integrity)
- **Purpose**: Uses LangChain's trim_messages with automatic integrity preservation
- **Integrity**: ✅ Automatically preserved
- **Use Cases**:
  - When you want LangChain's trimming algorithm
  - Compatibility with LangChain patterns
  - Advanced trimming options
- **Keep Because**: Leverages LangChain's utilities while ensuring correctness

## Strategies to Deprecate

| Strategy | Deprecation Reason | Migration Path |
|----------|-------------------|----------------|
| `langchain-trim` | Replaced by enhanced version | Use `langchain-enhanced` |
| `langchain-trim-advanced` | Overly complex | Use `langchain-enhanced` |
| `reverse-trim` | Superseded | Use `smart-trim` |
| `smart-reverse` | Superseded | Use `smart-trim` |
| `integrity-first` | Now built into all strategies | All strategies have integrity |
| `last-n` | Too simple | Use `sliding-window` with small window |
| Various `_v2`, `_simplified` | Development artifacts | Use core strategies |

## New Architecture: Integrity-First Design

### Key Changes

1. **BaseContextHook** now inherits from `IntegrityPreservingMixin`
2. All strategies automatically preserve message integrity
3. Strategies only need to implement `apply_trimming_logic()` returning indices
4. Base class handles integrity preservation, debug output, and validation

### Implementation Example

```python
class MyCustomStrategy(BaseContextHook):
    def get_strategy_name(self) -> str:
        return "My Custom Strategy"
    
    def apply_trimming_logic(self, messages: List[BaseMessage]) -> Set[int]:
        # Just return indices you want to keep
        # Base class will automatically ensure integrity!
        selected = {0}  # Always keep first
        # ... your logic here
        return selected
```

## Implementation Plan

### Phase 1: Standardize with Base Class (Week 1)
```python
# All strategies inherit from BaseContextHook
class SmartTrimStrategy(BaseContextHook):
    # Automatic features:
    # - Message integrity preservation
    # - Debug formatting
    # - Token counting
    # - Validation
```

### Phase 2: Consolidate Code (Week 2)
1. Create `BaseContextHook` class
2. Migrate core strategies to use base class
3. Move all strategies to use `strategy_registry.py`
4. Remove duplicate code

### Phase 3: Update Documentation (Week 3)
1. Update CLI help text
2. Create migration guide
3. Update examples
4. Add deprecation warnings

### Phase 4: Deprecation Process (Week 4+)
1. Add warnings for deprecated strategies
2. Maintain backward compatibility for 1 version
3. Remove deprecated code in next major version

## Usage After Consolidation

### CLI Usage
```bash
# Simplified strategy selection
browser-copilot test.md --context-strategy smart-trim  # Recommended (with integrity)
browser-copilot test.md --context-strategy sliding-window  # Simple (with integrity)
browser-copilot test.md --context-strategy langchain-enhanced  # LangChain (with integrity)
browser-copilot test.md --context-strategy no-op  # Baseline (no trimming)
```

### Programmatic Usage
```python
from browser_copilot.context_management import strategy_registry

# Get recommended strategies
strategies = strategy_registry.get_recommended_strategies()
# Returns: ['no-op', 'smart-trim', 'sliding-window', 'integrity-first']

# Get strategy with automatic deprecation warning
hook = strategy_registry.get_hook('smart-trim', config, verbose=True)
```

## Benefits of Consolidation

1. **Easier to Choose**: 4 clear options vs 8+ confusing variants
2. **Better Maintenance**: Less code to maintain and test
3. **Consistent Experience**: All strategies use same debug output
4. **Clear Use Cases**: Each strategy has distinct purpose
5. **Performance**: Focus optimization on fewer strategies
6. **Integrity by Default**: No more "Bad Request" errors from broken tool pairs
7. **Simpler Implementation**: Strategies only implement trimming logic, not integrity

## Migration Examples

### Before (Multiple Files)
```python
# Scattered across 8 files
from .react_hooks import create_sliding_window_hook
from .react_hooks_reverse import create_reverse_trim_hook
from .react_hooks_smart import create_smart_trim_hook
# ... many more imports
```

### After (Single Registry)
```python
# Single import, consistent interface
from browser_copilot.context_management import strategy_registry

hook = strategy_registry.get_hook('smart-trim', config)
```

## Metrics to Track

After consolidation, track:
1. **User adoption** of each strategy
2. **Performance metrics** per strategy
3. **Error rates** per strategy
4. **User feedback** on strategy selection

This will help us further optimize and potentially consolidate more in the future.