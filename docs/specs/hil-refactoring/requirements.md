# HIL Refactoring Plan

Based on critical code review conducted on July 30, 2025.

## Executive Summary

The current HIL implementation works but has significant architectural issues:
- Global state management
- Mixed responsibilities
- Poor error handling
- Lack of abstraction
- Testing difficulties

This plan outlines a systematic refactoring to achieve clean, modular, testable code.

## Critical Issues to Address

### 1. Global State (HIGH PRIORITY)
- `_response_generator` and `_hil_config` are global variables
- Thread-safety concerns
- Hard to test
- Configuration bleeding between runs

### 2. Mixed Responsibilities (HIGH PRIORITY)
- HIL logic embedded in core.py
- UI concerns mixed with business logic
- No clear separation of concerns

### 3. Error Handling (MEDIUM PRIORITY)
- Silent failures with print statements
- No retry mechanisms
- Generic fallbacks losing context

### 4. Lack of Abstraction (MEDIUM PRIORITY)
- Tightly coupled to LangGraph interrupts
- No strategy pattern for different modes
- Hard to extend or modify

## Refactoring Phases

### Phase 1: Extract HIL Manager (Week 1)

#### 1.1 Create HIL Manager Class
```python
# browser_copilot/hil/manager.py
class HILManager:
    """Manages all Human-in-the-Loop interactions"""
    
    def __init__(self, 
                 config: HILConfig,
                 llm_factory: Optional[Callable] = None,
                 logger: Optional[Logger] = None):
        self.config = config
        self._llm_factory = llm_factory
        self._logger = logger or logging.getLogger(__name__)
        self._strategy = self._create_strategy()
        self._interaction_count = 0
    
    async def handle_interrupt(self, 
                             interrupt_data: InterruptData) -> str:
        """Handle an interrupt from the agent"""
        pass
```

#### 1.2 Create Configuration Model
```python
# browser_copilot/hil/config.py
@dataclass
class HILConfig:
    """HIL configuration with validation"""
    enabled: bool = True
    interactive: bool = False
    provider: str = "openai"
    model: str = "gpt-4"
    max_interactions: int = 50
    interaction_timeout: float = 30.0
    
    def __post_init__(self):
        self._validate()
```

#### 1.3 Move Logic from Core
- Extract all HIL handling from core.py
- Create clean interface for interrupt handling
- Maintain backward compatibility

### Phase 2: Implement Strategy Pattern (Week 1-2)

#### 2.1 Define HIL Strategy Interface
```python
# browser_copilot/hil/strategies/base.py
from abc import ABC, abstractmethod

class HILStrategy(ABC):
    """Base strategy for HIL responses"""
    
    @abstractmethod
    async def get_response(self, 
                          prompt: HILPrompt) -> HILResponse:
        """Get response for HIL prompt"""
        pass
```

#### 2.2 Implement Strategies
```python
# browser_copilot/hil/strategies/llm_strategy.py
class LLMStrategy(HILStrategy):
    """Uses LLM for intelligent responses"""
    
# browser_copilot/hil/strategies/interactive_strategy.py
class InteractiveStrategy(HILStrategy):
    """Prompts user for real input"""
    
# browser_copilot/hil/strategies/default_strategy.py
class DefaultStrategy(HILStrategy):
    """Uses predefined responses"""
```

### Phase 3: Improve Error Handling (Week 2)

#### 3.1 Create Exception Hierarchy
```python
# browser_copilot/hil/exceptions.py
class HILError(BrowserCopilotError):
    """Base HIL exception"""
    
class HILTimeoutError(HILError):
    """User input timeout"""
    
class HILLimitExceededError(HILError):
    """Interaction limit exceeded"""
    
class HILConfigurationError(HILError):
    """Invalid HIL configuration"""
```

#### 3.2 Add Retry Logic
```python
# browser_copilot/hil/retry.py
class HILRetryPolicy:
    """Configurable retry policy for HIL operations"""
    max_attempts: int = 3
    backoff_factor: float = 2.0
    max_delay: float = 30.0
```

### Phase 4: Async Input Handling (Week 2)

#### 4.1 Replace Blocking Input
```python
# browser_copilot/hil/input_handler.py
class AsyncInputHandler:
    """Non-blocking input handler"""
    
    async def get_input(self, 
                       prompt: str, 
                       timeout: float) -> str:
        """Get user input with timeout"""
        pass
```

### Phase 5: Testing Infrastructure (Week 3)

#### 5.1 Create Test Fixtures
```python
# tests/hil/conftest.py
@pytest.fixture
def mock_llm():
    """Mock LLM for testing"""
    
@pytest.fixture
def hil_manager():
    """Configured HIL manager for tests"""
```

#### 5.2 Comprehensive Test Suite
- Unit tests for each strategy
- Integration tests for manager
- Error scenario testing
- Performance benchmarks

## Migration Plan

### Step 1: Create New Structure (No Breaking Changes)
1. Create new `browser_copilot/hil/` package
2. Implement HILManager alongside existing code
3. Add comprehensive tests

### Step 2: Gradual Migration
1. Update agent.py to use HILManager optionally
2. Deprecate global configuration
3. Update core.py to delegate to HILManager

### Step 3: Complete Transition
1. Remove old ask_human_tool.py code
2. Update all imports
3. Update documentation

## Success Criteria

### Code Quality Metrics
- Zero global variables
- All functions < 30 lines
- Cyclomatic complexity < 7
- 95% test coverage

### Functional Requirements
- All existing HIL features work
- No performance degradation
- Better error messages
- Easier to extend

### Non-Functional Requirements
- Thread-safe implementation
- Proper async/await usage
- Clean dependency injection
- Comprehensive logging

## Risk Mitigation

### Backward Compatibility
- Maintain existing CLI interface
- Keep same behavior by default
- Deprecate gradually

### Testing Strategy
- Feature flags for new implementation
- A/B testing in dev environment
- Gradual rollout

## Timeline

- **Week 1**: HIL Manager + Configuration
- **Week 2**: Strategy Pattern + Error Handling
- **Week 3**: Async Input + Testing
- **Week 4**: Migration + Documentation

## Benefits

1. **Testability**: Easy to mock and test
2. **Extensibility**: New strategies without changing core
3. **Maintainability**: Clear separation of concerns
4. **Performance**: Better resource management
5. **Reliability**: Proper error handling

This refactoring will transform HIL from a working prototype to production-ready, enterprise-grade code.