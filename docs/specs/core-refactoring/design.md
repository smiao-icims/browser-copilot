# Core.py Refactoring Design Document

## 1. Architecture Overview

### 1.1 Current Architecture

```
BrowserPilot (790+ lines)
├── LLM initialization
├── MCP server configuration
├── Test execution
├── Prompt building
├── Token tracking
├── Result analysis
└── Logging/telemetry
```

### 1.2 Proposed Architecture

```
BrowserPilot (Orchestrator, ~150 lines)
├── LLMManager
├── BrowserConfigBuilder
├── TestExecutor
├── PromptBuilder
├── ResultAnalyzer
├── TokenMetricsCollector
└── Component interfaces
```

## 2. Component Design

### 2.1 LLMManager

**Purpose**: Encapsulate LLM initialization and configuration

```python
class LLMManager:
    """Manages LLM lifecycle and configuration"""

    def __init__(self, provider: str, model: str, config: ConfigManager):
        self.provider = provider
        self.model = model
        self.config = config
        self.registry = ModelForgeRegistry()

    def create_llm(self, callbacks: list[Any]) -> Any:
        """Create and configure LLM instance"""

    def get_model_metadata(self) -> ModelMetadata:
        """Retrieve model capabilities and limits"""

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate token costs"""
```

**Responsibilities**:
- Initialize ModelForge registry
- Configure LLM with callbacks
- Handle provider-specific setup
- Expose model metadata

### 2.2 BrowserConfigBuilder

**Purpose**: Handle browser configuration and MCP server setup

```python
@dataclass
class BrowserOptions:
    browser: str = "chromium"
    headless: bool = False
    viewport_width: int = 1920
    viewport_height: int = 1080
    device: str | None = None
    user_agent: str | None = None
    proxy_server: str | None = None
    # ... other options

class BrowserConfigBuilder:
    """Builds MCP server configuration for browser automation"""

    VALID_BROWSERS = ["chromium", "chrome", "firefox", "webkit", "safari", "edge"]
    BROWSER_ALIASES = {"chrome": "chromium", "edge": "msedge", "safari": "webkit"}

    def validate_browser(self, browser: str) -> str:
        """Validate and normalize browser name"""

    def build_mcp_args(self, options: BrowserOptions) -> list[str]:
        """Build MCP server command arguments"""

    def create_session_directory(self, test_name: str, base_dir: Path) -> Path:
        """Create directory for test session artifacts"""

    def get_server_params(self, options: BrowserOptions) -> StdioServerParameters:
        """Get complete server parameters"""
```

**Responsibilities**:
- Validate browser selection
- Build MCP command arguments
- Handle session directories
- Manage browser-specific options

### 2.3 TestExecutor

**Purpose**: Execute tests and manage agent interaction

```python
@dataclass
class ExecutionResult:
    steps: list[ExecutionStep]
    final_response: Any
    duration: float
    success: bool

class TestExecutor:
    """Handles test execution through agent interaction"""

    def __init__(self, stream_handler: StreamHandler, verbose: bool = False):
        self.stream = stream_handler
        self.verbose = verbose

    async def execute(
        self,
        agent: Any,
        prompt: str,
        timeout: int | None = None
    ) -> ExecutionResult:
        """Execute test through agent"""

    def _process_chunk(self, chunk: dict, step_num: int) -> ExecutionStep:
        """Process individual execution chunk"""

    def _extract_steps(self, raw_steps: list) -> list[ExecutionStep]:
        """Convert raw agent output to structured steps"""
```

**Responsibilities**:
- Stream agent execution
- Process execution chunks
- Extract structured steps
- Handle timeouts

### 2.4 PromptBuilder

**Purpose**: Build and optimize test prompts

```python
class PromptBuilder:
    """Constructs prompts for test execution"""

    DEFAULT_INSTRUCTIONS = """
    IMPORTANT INSTRUCTIONS:
    1. Execute each test step methodically using the browser automation tools
    2. Use browser_snapshot before interacting with elements
    3. Take screenshots at key points using browser_take_screenshot
    ...
    """

    def __init__(self, optimizer: TokenOptimizer | None = None):
        self.optimizer = optimizer

    def build(
        self,
        test_content: str,
        system_prompt: str | None = None,
        browser: str = "unknown"
    ) -> str:
        """Build complete prompt from test content"""

    def optimize(self, prompt: str) -> tuple[str, OptimizationMetrics]:
        """Optimize prompt if optimizer available"""

    def extract_test_name(self, test_content: str) -> str:
        """Extract test name from content"""
```

**Responsibilities**:
- Construct test prompts
- Apply token optimization
- Extract test metadata
- Maintain prompt templates

### 2.5 ResultAnalyzer

**Purpose**: Analyze test results and determine success

```python
@dataclass
class TestResult:
    success: bool
    test_name: str
    duration: float
    steps_executed: int
    report: str
    token_usage: dict[str, Any]
    metrics: dict[str, Any]
    error: str | None = None

class ResultAnalyzer:
    """Analyzes test execution results"""

    SUCCESS_PATTERNS = [
        r"overall status[:\*]*\s*passed",
        r"status[:\*]*\s*passed",
        r"all tests passed",
        r"test passed successfully",
    ]

    FAILURE_PATTERNS = [
        r"overall status[:\*]*\s*failed",
        r"status[:\*]*\s*failed",
        r"test failed",
    ]

    def analyze(
        self,
        execution_result: ExecutionResult,
        test_metadata: dict[str, Any]
    ) -> TestResult:
        """Analyze execution result and build test result"""

    def check_success(self, report_content: str) -> bool:
        """Determine if test passed based on report"""

    def _has_valid_report(self, content: str) -> bool:
        """Check if content contains valid test report"""
```

**Responsibilities**:
- Parse execution reports
- Determine test success/failure
- Build result structures
- Extract metrics

### 2.6 TokenMetricsCollector

**Purpose**: Collect and calculate token usage metrics

```python
@dataclass
class TokenMetrics:
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    estimated_cost: float | None
    context_usage_percentage: float | None
    optimization_savings: dict[str, Any] | None

class TokenMetricsCollector:
    """Collects token usage and cost metrics"""

    def __init__(self, telemetry: TelemetryCallback, llm_manager: LLMManager):
        self.telemetry = telemetry
        self.llm_manager = llm_manager

    def collect(self, optimizer: TokenOptimizer | None = None) -> TokenMetrics:
        """Collect token metrics from execution"""

    def _extract_from_telemetry(self) -> dict[str, Any]:
        """Extract base metrics from telemetry"""

    def _calculate_context_usage(self, prompt_tokens: int) -> dict[str, float]:
        """Calculate context utilization"""

    def _calculate_optimization_savings(
        self,
        base_metrics: dict,
        optimizer: TokenOptimizer
    ) -> dict[str, Any]:
        """Calculate savings from optimization"""
```

**Responsibilities**:
- Extract telemetry data
- Calculate token costs
- Track context usage
- Measure optimization impact

### 2.7 Refactored BrowserPilot

**Purpose**: Orchestrate components for test execution

```python
class BrowserPilot:
    """Orchestrates AI-powered browser test automation"""

    def __init__(
        self,
        provider: str,
        model: str,
        system_prompt: str | None = None,
        config: ConfigManager | None = None,
        stream: StreamHandler | None = None,
    ):
        # Initialize configuration
        self.config = config or ConfigManager()
        self.stream = stream or StreamHandler()

        # Initialize components
        self.llm_manager = LLMManager(provider, model, self.config)
        self.browser_config = BrowserConfigBuilder()
        self.prompt_builder = self._create_prompt_builder()
        self.executor = TestExecutor(self.stream, self.config.get("verbose", False))
        self.analyzer = ResultAnalyzer()

        # Create telemetry and logging
        self.telemetry = TelemetryCallback(provider=provider, model=model)
        self._setup_logging()

    async def run_test_suite(
        self,
        test_suite_content: str,
        **options
    ) -> dict[str, Any]:
        """Execute test suite with browser automation"""

        # Phase 1: Configuration
        browser_options = self._build_browser_options(**options)
        server_params = self.browser_config.get_server_params(browser_options)

        # Phase 2: Setup
        test_name = self.prompt_builder.extract_test_name(test_suite_content)
        prompt = self.prompt_builder.build(test_suite_content, self.system_prompt)

        # Phase 3: Execution
        async with self._create_mcp_session(server_params) as session:
            agent = await self._create_agent(session)
            result = await self.executor.execute(agent, prompt, options.get("timeout"))

        # Phase 4: Analysis
        metrics_collector = TokenMetricsCollector(self.telemetry, self.llm_manager)
        token_metrics = metrics_collector.collect(self.prompt_builder.optimizer)

        return self.analyzer.analyze(result, {
            "test_name": test_name,
            "provider": self.provider,
            "model": self.model,
            "browser_options": browser_options,
            "token_metrics": token_metrics,
        })
```

## 3. Interface Design

### 3.1 Component Interfaces

```python
from abc import ABC, abstractmethod
from typing import Protocol

class LLMProvider(Protocol):
    """Protocol for LLM providers"""
    def create_llm(self, callbacks: list[Any]) -> Any: ...
    def get_metadata(self) -> dict[str, Any]: ...

class TestExecutorProtocol(Protocol):
    """Protocol for test executors"""
    async def execute(self, agent: Any, prompt: str) -> ExecutionResult: ...

class ResultAnalyzerProtocol(Protocol):
    """Protocol for result analyzers"""
    def analyze(self, result: ExecutionResult, metadata: dict) -> TestResult: ...
```

### 3.2 Data Models

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass
class ExecutionStep:
    """Represents a single execution step"""
    type: str  # "tool_call" | "agent_message"
    name: str | None
    content: str
    timestamp: datetime

@dataclass
class ModelMetadata:
    """Model capability information"""
    context_length: int
    supports_streaming: bool
    supports_tools: bool
    cost_per_1k_prompt: float | None
    cost_per_1k_completion: float | None

@dataclass
class OptimizationMetrics:
    """Token optimization metrics"""
    original_tokens: int
    optimized_tokens: int
    reduction_percentage: float
    strategies_applied: list[str]
```

## 4. Error Handling

### 4.1 Exception Hierarchy

```python
class BrowserPilotError(Exception):
    """Base exception for Browser Pilot"""

class ConfigurationError(BrowserPilotError):
    """Configuration-related errors"""

class BrowserSetupError(BrowserPilotError):
    """Browser setup failures"""

class ExecutionError(BrowserPilotError):
    """Test execution failures"""

class AnalysisError(BrowserPilotError):
    """Result analysis failures"""
```

### 4.2 Error Handling Strategy

- Each component handles its specific errors
- Errors bubble up with context
- Orchestrator provides fallback behavior
- User-friendly error messages

## 5. Configuration Flow

```
ConfigManager
    ↓
BrowserPilot.__init__
    ├→ LLMManager (provider config)
    ├→ PromptBuilder (optimization config)
    ├→ TestExecutor (verbose config)
    └→ Logging setup

BrowserPilot.run_test_suite
    ├→ BrowserConfigBuilder (browser options)
    ├→ MCP Session (server params)
    └→ Agent creation (LLM + tools)
```

## 6. Testing Strategy

### 6.1 Unit Tests

Each component will have dedicated unit tests:

```python
# test_llm_manager.py
class TestLLMManager:
    def test_create_llm_with_callbacks(self)
    def test_get_model_metadata(self)
    def test_invalid_provider_handling(self)

# test_browser_config.py
class TestBrowserConfigBuilder:
    def test_validate_browser_names(self)
    def test_build_mcp_args(self)
    def test_session_directory_creation(self)

# Similar for other components...
```

### 6.2 Integration Tests

```python
# test_integration.py
class TestBrowserPilotIntegration:
    async def test_full_execution_flow(self)
    async def test_error_propagation(self)
    async def test_component_interaction(self)
```

## 7. Migration Path

### Phase 1: Extract without breaking changes
1. Create new component files
2. Move logic from core.py
3. Update BrowserPilot to use components
4. Ensure all tests pass

### Phase 2: Optimize and enhance
1. Add component-specific optimizations
2. Improve error handling
3. Add new features to components
4. Update documentation

### Phase 3: Deprecate old patterns
1. Mark internal methods as private
2. Add deprecation warnings
3. Update consumer code
4. Remove deprecated code

## 8. Performance Considerations

- Lazy initialization where possible
- Reuse expensive objects (LLM, telemetry)
- Stream processing for large outputs
- Efficient prompt optimization
- Minimal overhead from abstraction

## 9. Future Extensibility

The modular design enables:
- Alternative test executors (parallel, distributed)
- Different result analyzers (ML-based, heuristic)
- Custom prompt builders (template-based, dynamic)
- Pluggable token optimizers
- New browser configurations
- Additional metrics collectors
