# Data Models Phase 2 - Design

## Architecture Overview

This design extends the model architecture established in Phase 1, applying the same patterns to configuration, logging, optimization, and reporting components.

## Component Designs

### 1. ConfigManager Models

#### Core Configuration Models

```python
# browser_copilot/models/config.py

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from pathlib import Path

@dataclass
class ViewportConfig(SerializableModel):
    """Browser viewport configuration"""
    width: int = 1920
    height: int = 1080

    def validate(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Viewport dimensions must be positive")

@dataclass
class BrowserConfig(SerializableModel):
    """Browser-specific configuration"""
    browser: str = "chromium"
    headless: bool = True
    viewport: ViewportConfig = field(default_factory=ViewportConfig)
    timeout: int = 30
    locale: str = "en-US"
    timezone: str = "America/New_York"

    def validate(self) -> None:
        if self.browser not in ["chromium", "firefox", "webkit"]:
            raise ValueError(f"Unsupported browser: {self.browser}")
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")

@dataclass
class ProviderConfig(SerializableModel):
    """LLM provider configuration"""
    provider: str
    model: str
    api_key: Optional[str] = None
    github_token: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.0
    max_tokens: Optional[int] = None

    def validate(self) -> None:
        if not self.provider:
            raise ValueError("Provider is required")
        if not self.model:
            raise ValueError("Model is required")

@dataclass
class OptimizationConfig(SerializableModel):
    """Token optimization configuration"""
    enabled: bool = True
    compression_level: str = "medium"
    max_context_length: int = 4000
    preserve_recent: int = 1000
    skip_screenshots: bool = False

    def validate(self) -> None:
        if self.compression_level not in ["none", "low", "medium", "high"]:
            raise ValueError(f"Invalid compression level: {self.compression_level}")

@dataclass
class ExecutionConfig(SerializableModel):
    """Test execution configuration"""
    retry_count: int = 0
    retry_delay: int = 5
    continue_on_error: bool = False
    verbose: bool = False
    debug: bool = False

@dataclass
class StorageConfig(SerializableModel):
    """Storage configuration"""
    output_dir: str = "reports"
    screenshots_dir: str = "screenshots"
    logs_dir: str = "logs"
    keep_artifacts: bool = True
    max_artifacts_age_days: int = 30

@dataclass
class AppConfig(SerializableModel):
    """Complete application configuration"""
    provider: ProviderConfig
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    system_prompt: Optional[str] = None

    @classmethod
    def from_layers(cls,
                   cli_args: Dict[str, Any],
                   env_vars: Dict[str, Any],
                   config_file: Dict[str, Any],
                   defaults: Dict[str, Any]) -> 'AppConfig':
        """Create config from multiple layers with priority"""
        # Implementation will merge layers with proper precedence
        pass
```

#### ConfigManager Updates

```python
class ConfigManager:
    def __init__(self):
        self._config: Optional[AppConfig] = None
        self._legacy_mode: bool = False

    def load(self) -> AppConfig:
        """Load configuration from all sources"""
        # Internally uses AppConfig
        pass

    def get(self, key: str, default: Any = None) -> Any:
        """Legacy dict-like interface"""
        # Maps to config model attributes
        pass
```

### 2. VerboseLogger Models

```python
# browser_copilot/models/logging.py

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pathlib import Path

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

class StepType(Enum):
    NAVIGATION = "navigation"
    INTERACTION = "interaction"
    VERIFICATION = "verification"
    SCREENSHOT = "screenshot"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    LLM_CALL = "llm_call"
    LLM_RESPONSE = "llm_response"

@dataclass
class ExecutionStep(SerializableModel):
    """Represents a single execution step"""
    timestamp: datetime
    type: StepType
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    level: LogLevel = LogLevel.INFO
    duration_ms: Optional[float] = None

    @property
    def formatted_timestamp(self) -> str:
        return self.timestamp.isoformat()

@dataclass
class ToolCall(SerializableModel):
    """Represents a browser tool invocation"""
    timestamp: datetime
    tool_name: str
    parameters: Dict[str, Any]
    result: Any
    duration_ms: Optional[float] = None
    success: bool = True
    error: Optional[str] = None

    def get_truncated_result(self, max_length: int = 200) -> Any:
        """Get result truncated for display"""
        # Implementation
        pass

@dataclass
class TokenUsageLog(SerializableModel):
    """Token usage for a specific LLM call"""
    timestamp: datetime
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: Optional[float] = None
    model: Optional[str] = None

@dataclass
class ErrorLog(SerializableModel):
    """Structured error information"""
    timestamp: datetime
    error_type: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    recoverable: bool = True
    stack_trace: Optional[str] = None

@dataclass
class LogSession(SerializableModel):
    """Complete logging session data"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    log_file: Optional[Path] = None
    execution_steps: List[ExecutionStep] = field(default_factory=list)
    tool_calls: List[ToolCall] = field(default_factory=list)
    token_usage_logs: List[TokenUsageLog] = field(default_factory=list)
    errors: List[ErrorLog] = field(default_factory=list)

    @property
    def duration(self) -> Optional[float]:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def total_token_usage(self) -> TokenMetrics:
        """Aggregate token usage across all calls"""
        # Implementation
        pass

    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary"""
        # Implementation
        pass
```

### 3. TokenOptimizer Models

```python
# browser_copilot/models/optimization.py

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any

class OptimizationStrategy(Enum):
    WHITESPACE = "whitespace"
    PUNCTUATION = "punctuation"
    PHRASES = "phrases"
    REDUNDANCY = "redundancy"
    NUMBERS = "numbers"
    FILLERS = "fillers"
    ABBREVIATIONS = "abbreviations"
    COMPRESSION = "compression"

@dataclass
class OptimizationMetrics(SerializableModel):
    """Metrics for token optimization"""
    original_tokens: int = 0
    optimized_tokens: int = 0
    strategies_applied: List[OptimizationStrategy] = field(default_factory=list)

    @property
    def reduction_percentage(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return ((self.original_tokens - self.optimized_tokens) / self.original_tokens) * 100

    @property
    def tokens_saved(self) -> int:
        return self.original_tokens - self.optimized_tokens

@dataclass
class CostAnalysis(SerializableModel):
    """Cost analysis for optimization"""
    original_cost: float
    optimized_cost: float
    cost_per_1k_tokens: float

    @property
    def savings(self) -> float:
        return self.original_cost - self.optimized_cost

    @property
    def savings_percentage(self) -> float:
        if self.original_cost == 0:
            return 0.0
        return (self.savings / self.original_cost) * 100

@dataclass
class OptimizationResult(SerializableModel):
    """Complete optimization result"""
    original_text: str
    optimized_text: str
    metrics: OptimizationMetrics
    cost_analysis: Optional[CostAnalysis] = None
    optimization_level: str = "medium"

    def get_summary(self) -> Dict[str, Any]:
        """Get optimization summary for reporting"""
        return {
            "tokens_saved": self.metrics.tokens_saved,
            "reduction_percentage": self.metrics.reduction_percentage,
            "strategies": [s.value for s in self.metrics.strategies_applied],
            "cost_savings": self.cost_analysis.savings if self.cost_analysis else None
        }
```

### 4. Reporter Model Updates

```python
# Updates to use existing BrowserTestResult model

class Reporter:
    """Updated to work with BrowserTestResult model"""

    def print_results(self, result: BrowserTestResult, no_color: bool = False) -> None:
        """Print test results using model properties"""
        # Use result.success, result.duration, etc.
        pass

    def save_results(self, result: BrowserTestResult, output_dir: str = "reports") -> Dict[str, Path]:
        """Save results using model serialization"""
        # Use result.to_dict() for JSON serialization
        pass

    def generate_html_report(self, result: BrowserTestResult) -> str:
        """Generate HTML using model structure"""
        # Access typed properties instead of dict keys
        pass
```

### 5. WizardState Enhancements

```python
# browser_copilot/models/wizard.py

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class WizardHistoryEntry(SerializableModel):
    """Single history entry in wizard navigation"""
    step: int
    timestamp: datetime
    provider: Optional[str] = None
    model: Optional[str] = None
    browser: str = "chromium"
    headless: bool = True
    compression_level: str = "medium"

@dataclass
class WizardConfig(SerializableModel):
    """Typed configuration output from wizard"""
    provider: ProviderConfig
    browser: BrowserConfig
    optimization: OptimizationConfig
    execution: ExecutionConfig

    def to_cli_args(self) -> List[str]:
        """Convert to CLI arguments"""
        # Implementation
        pass

# Update WizardState
@dataclass
class WizardState:
    # ... existing fields ...
    history: List[WizardHistoryEntry] = field(default_factory=list)

    def to_config(self) -> WizardConfig:
        """Return typed configuration"""
        # Implementation
        pass
```

## Migration Strategy

### Backward Compatibility

1. **Dual Interfaces**: Support both dict and model APIs
2. **Automatic Conversion**: Convert between formats transparently
3. **Deprecation Warnings**: Warn when using legacy dict interface
4. **Grace Period**: Maintain compatibility for 2-3 releases

### Implementation Phases

#### Phase 1: ConfigManager (Week 1)
- Implement config models
- Update ConfigManager internally
- Maintain dict compatibility layer
- Comprehensive testing

#### Phase 2: VerboseLogger (Week 2)
- Implement logging models
- Update logger to use models
- Migrate existing log parsing
- Test with various scenarios

#### Phase 3: TokenOptimizer (Week 3)
- Implement optimization models
- Update optimizer methods
- Ensure metric consistency
- Performance testing

#### Phase 4: Reporter & WizardState (Week 4)
- Update Reporter to use models
- Enhance WizardState
- Integration testing
- Documentation updates

## Testing Strategy

### Unit Tests
- Model construction
- Validation logic
- Serialization/deserialization
- Property calculations

### Integration Tests
- Component interaction
- Backward compatibility
- Migration scenarios
- End-to-end workflows

### Property-Based Tests
- Use Hypothesis for model properties
- Invariant testing
- Round-trip serialization
- Edge case discovery

## Performance Considerations

1. **Lazy Loading**: Only create models when needed
2. **Caching**: Cache computed properties
3. **Efficient Serialization**: Use optimized JSON encoding
4. **Memory Management**: Avoid circular references

## Documentation Updates

1. **API Documentation**: Update all docstrings
2. **Migration Guide**: Help users transition
3. **Examples**: Show both old and new usage
4. **Type Stubs**: Ensure proper type hints
