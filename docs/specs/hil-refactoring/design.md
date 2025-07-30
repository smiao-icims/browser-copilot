# HIL Refactoring - Design Document

## Overview

This design document outlines the refactoring of the Human-in-the-Loop (HIL) implementation to address architectural issues identified in the code review and create a modular, testable, and maintainable system.

## Current Architecture Issues

### Problems with Current Implementation

1. **Global State Management**
   - Global variables for LLM instance and configuration
   - Thread-safety concerns in async environment
   - Difficult to test due to shared state

2. **Tight Coupling**
   - HIL logic embedded in core.py
   - Direct dependency on LangGraph interrupts
   - No abstraction layer for different strategies

3. **Poor Error Handling**
   - Silent failures with print statements
   - No retry mechanisms
   - Loss of error context

## Proposed Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│                    HIL Manager                           │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   Config    │  │   Strategy   │  │    Error      │  │
│  │  Manager    │  │   Factory    │  │   Handler     │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                 Strategy Layer                           │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │     LLM     │  │ Interactive  │  │   Default     │  │
│  │  Strategy   │  │   Strategy   │  │   Strategy    │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                  Tool Layer                              │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  ask_human  │  │   confirm    │  │   Custom      │  │
│  │    tool     │  │   action     │  │   Tools       │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Component Design

### 1. HIL Manager

```python
class HILManager:
    """Central manager for all HIL operations"""

    def __init__(self,
                 config: HILConfig,
                 llm_factory: Optional[LLMFactory] = None,
                 logger: Optional[Logger] = None):
        self.config = config
        self._llm_factory = llm_factory or DefaultLLMFactory()
        self._logger = logger or get_logger(__name__)
        self._strategy_factory = StrategyFactory()
        self._error_handler = HILErrorHandler(config.error_policy)
        self._metrics = HILMetrics()
        self._interaction_count = 0

    async def handle_interrupt(self,
                             interrupt_data: InterruptData) -> Response:
        """Handle an interrupt with appropriate strategy"""
        try:
            # Check limits
            self._check_interaction_limit()

            # Get strategy
            strategy = self._strategy_factory.get_strategy(
                self.config.mode,
                self._llm_factory
            )

            # Process interrupt
            prompt = self._extract_prompt(interrupt_data)
            response = await strategy.get_response(prompt)

            # Update metrics
            self._metrics.record_interaction(prompt, response)
            self._interaction_count += 1

            return response

        except Exception as e:
            return await self._error_handler.handle_error(e, interrupt_data)
```

### 2. Configuration System

```python
@dataclass
class HILConfig:
    """HIL configuration with validation"""

    # Core settings
    enabled: bool = True
    mode: HILMode = HILMode.LLM

    # LLM settings
    provider: str = "openai"
    model: str = "gpt-4"
    temperature: float = 0.3
    max_tokens: int = 100

    # Interaction settings
    max_interactions: int = 50
    interaction_timeout: float = 30.0

    # Error handling
    error_policy: ErrorPolicy = ErrorPolicy.RETRY_WITH_BACKOFF
    max_retries: int = 3

    # UI settings
    show_suggestions: bool = True
    interactive_prompt_style: PromptStyle = PromptStyle.DETAILED

    def __post_init__(self):
        """Validate configuration"""
        if self.max_interactions < 1:
            raise HILConfigurationError("max_interactions must be >= 1")
        if self.temperature < 0 or self.temperature > 2:
            raise HILConfigurationError("temperature must be between 0 and 2")
        if self.interaction_timeout <= 0:
            raise HILConfigurationError("timeout must be positive")

class HILMode(Enum):
    """HIL operation modes"""
    LLM = "llm"  # Use LLM for responses
    INTERACTIVE = "interactive"  # Real human input
    DEFAULT = "default"  # Predefined responses
    MOCK = "mock"  # For testing
```

### 3. Strategy Pattern

```python
from abc import ABC, abstractmethod

class HILStrategy(ABC):
    """Base strategy for HIL responses"""

    @abstractmethod
    async def get_response(self, prompt: HILPrompt) -> HILResponse:
        """Get response for the given prompt"""
        pass

    @abstractmethod
    def supports_mode(self, mode: HILMode) -> bool:
        """Check if strategy supports given mode"""
        pass

class LLMStrategy(HILStrategy):
    """Strategy using LLM for intelligent responses"""

    def __init__(self, llm_factory: LLMFactory):
        self._llm_factory = llm_factory
        self._llm = None
        self._prompt_template = PromptTemplate()

    async def get_response(self, prompt: HILPrompt) -> HILResponse:
        """Generate response using LLM"""
        if not self._llm:
            self._llm = await self._llm_factory.create_llm()

        llm_prompt = self._prompt_template.format(prompt)

        try:
            result = await self._llm.ainvoke(llm_prompt)
            return HILResponse(
                text=result.content,
                confidence=0.9,
                source="llm",
                metadata={"model": self._llm.model_name}
            )
        except Exception as e:
            raise HILStrategyError(f"LLM generation failed: {e}")

class InteractiveStrategy(HILStrategy):
    """Strategy for real human input"""

    def __init__(self, input_handler: AsyncInputHandler):
        self._input_handler = input_handler

    async def get_response(self, prompt: HILPrompt) -> HILResponse:
        """Get response from human user"""
        # Display prompt
        display = InteractiveDisplay()
        display.show_prompt(prompt)

        # Get input with timeout
        try:
            user_input = await self._input_handler.get_input(
                prompt.timeout
            )

            # Check for exit commands
            if self._is_exit_command(user_input):
                raise HILUserExitError("User requested exit")

            return HILResponse(
                text=user_input,
                confidence=1.0,
                source="human",
                metadata={"input_method": "console"}
            )

        except asyncio.TimeoutError:
            raise HILTimeoutError(
                f"User input timed out after {prompt.timeout}s"
            )
```

### 4. Error Handling

```python
class HILErrorHandler:
    """Centralized error handling for HIL"""

    def __init__(self, policy: ErrorPolicy):
        self.policy = policy
        self._retry_manager = RetryManager()

    async def handle_error(self,
                          error: Exception,
                          context: Any) -> HILResponse:
        """Handle errors with configured policy"""

        if isinstance(error, HILUserExitError):
            # Don't retry user exits
            raise

        if isinstance(error, HILLimitExceededError):
            # Don't retry limit errors
            raise

        if self.policy == ErrorPolicy.RETRY_WITH_BACKOFF:
            return await self._retry_manager.retry_with_backoff(
                self._get_fallback_response,
                error,
                context
            )
        elif self.policy == ErrorPolicy.FALLBACK:
            return self._get_fallback_response(context)
        else:
            raise

class RetryManager:
    """Manages retry logic with exponential backoff"""

    def __init__(self,
                 max_attempts: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 30.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay

    async def retry_with_backoff(self,
                                func: Callable,
                                error: Exception,
                                *args, **kwargs):
        """Retry function with exponential backoff"""
        for attempt in range(self.max_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_attempts - 1:
                    raise

                delay = min(
                    self.base_delay * (2 ** attempt),
                    self.max_delay
                )
                await asyncio.sleep(delay)
```

### 5. Tool Integration

```python
def create_hil_tools(manager: HILManager) -> List[Tool]:
    """Create HIL tools with proper dependency injection"""

    @tool
    async def ask_human(question: str,
                       context: Optional[str] = None) -> str:
        """Ask for human input"""
        prompt = HILPrompt(
            type=PromptType.QUESTION,
            text=question,
            context=context
        )

        interrupt_data = InterruptData(
            prompt=prompt,
            tool="ask_human",
            timestamp=datetime.now()
        )

        # Use manager instead of global state
        response = await manager.handle_interrupt(interrupt_data)

        # Still use LangGraph's interrupt for flow control
        human_response = interrupt(response.to_interrupt_format())
        return human_response

    @tool
    async def confirm_action(action: str,
                           details: Optional[str] = None) -> bool:
        """Request confirmation"""
        prompt = HILPrompt(
            type=PromptType.CONFIRMATION,
            text=action,
            context=details
        )

        interrupt_data = InterruptData(
            prompt=prompt,
            tool="confirm_action",
            timestamp=datetime.now()
        )

        response = await manager.handle_interrupt(interrupt_data)

        # Convert to boolean
        return response.to_boolean()

    return [ask_human, confirm_action]
```

## Data Models

```python
@dataclass
class HILPrompt:
    """Structured prompt for HIL"""
    type: PromptType
    text: str
    context: Optional[str] = None
    timeout: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HILResponse:
    """Structured response from HIL"""
    text: str
    confidence: float
    source: str  # "llm", "human", "default"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_interrupt_format(self) -> Dict[str, Any]:
        """Convert to LangGraph interrupt format"""
        return {
            "type": "hil_response",
            "response": self.text,
            "metadata": self.metadata
        }

    def to_boolean(self) -> bool:
        """Convert to boolean for confirmations"""
        affirmative = ["yes", "y", "true", "confirm", "proceed"]
        return self.text.lower().strip() in affirmative

@dataclass
class InterruptData:
    """Data passed through interrupt mechanism"""
    prompt: HILPrompt
    tool: str
    timestamp: datetime
    session_id: Optional[str] = None
```

## Integration with Core

```python
class BrowserCopilot:
    """Main class with HIL integration"""

    def __init__(self, config: Config):
        # ... other initialization ...

        # Create HIL manager with proper dependencies
        self.hil_manager = HILManager(
            config=config.hil,
            llm_factory=LLMFactory(config.llm),
            logger=self.logger
        )

    async def create_agent(self, session: ClientSession) -> Agent:
        """Create agent with HIL tools if enabled"""
        tools = await load_mcp_tools(session)

        if self.config.hil.enabled:
            # Add HIL tools with injected manager
            hil_tools = create_hil_tools(self.hil_manager)
            tools.extend(hil_tools)

        return create_react_agent(
            model=self.llm,
            tools=tools,
            checkpointer=self.checkpointer
        )
```

## Testing Strategy

```python
class MockHILStrategy(HILStrategy):
    """Mock strategy for testing"""

    def __init__(self, responses: List[str]):
        self.responses = responses
        self.call_count = 0

    async def get_response(self, prompt: HILPrompt) -> HILResponse:
        """Return predefined responses"""
        if self.call_count >= len(self.responses):
            response = "default"
        else:
            response = self.responses[self.call_count]

        self.call_count += 1

        return HILResponse(
            text=response,
            confidence=1.0,
            source="mock"
        )

# Example test
async def test_hil_manager():
    """Test HIL manager with mock strategy"""
    config = HILConfig(mode=HILMode.MOCK)
    manager = HILManager(config)

    # Inject mock strategy
    mock_strategy = MockHILStrategy(["blue", "yes"])
    manager._strategy_factory.register_strategy(
        HILMode.MOCK,
        mock_strategy
    )

    # Test interactions
    response1 = await manager.handle_interrupt(
        InterruptData(
            prompt=HILPrompt(
                type=PromptType.QUESTION,
                text="What color?"
            ),
            tool="ask_human",
            timestamp=datetime.now()
        )
    )

    assert response1.text == "blue"
    assert mock_strategy.call_count == 1
```

## Migration Strategy

### Phase 1: Parallel Implementation
- Implement new HIL system alongside existing
- Use feature flag to switch between implementations
- No breaking changes to public API

### Phase 2: Gradual Migration
- Update tools to use new system
- Migrate core.py to use HILManager
- Update tests to use new interfaces

### Phase 3: Cleanup
- Remove old global state code
- Update documentation
- Mark old methods as deprecated

## Benefits

1. **Testability**: Easy to mock and test components
2. **Extensibility**: New strategies without changing core
3. **Maintainability**: Clear separation of concerns
4. **Performance**: Better resource management
5. **Reliability**: Proper error handling and recovery
6. **Thread-Safety**: No global state
