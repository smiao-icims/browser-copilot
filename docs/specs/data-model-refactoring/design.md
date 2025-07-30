# Data Model Refactoring Design Document

## 1. Architecture Overview

### 1.1 Current State

```
Dictionary-based Models (Untyped)
├── Test Results (dict[str, Any])
├── Token Metrics (dict[str, Any])
├── Execution Metadata (dict[str, Any])
├── Test Metadata (dict[str, Any])
└── Various Config Dicts
```

### 1.2 Target State

```
Strongly-Typed Data Models
├── models/
│   ├── __init__.py
│   ├── base.py          # Base classes and protocols
│   ├── results.py       # Test result models
│   ├── metrics.py       # Token and performance metrics
│   ├── execution.py     # Execution-related models
│   └── serialization.py # Custom serializers
```

## 2. Data Model Hierarchy

### 2.1 Base Models

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, TypeVar, Generic

T = TypeVar('T')

class SerializableModel(ABC):
    """Base class for all serializable models"""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation"""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        """Create instance from dictionary"""
        pass

class ValidatedModel(SerializableModel):
    """Base class for models with validation"""

    def __post_init__(self) -> None:
        """Validate after construction"""
        self.validate()

    @abstractmethod
    def validate(self) -> None:
        """Validate model constraints"""
        pass
```

### 2.2 Core Data Models

#### 2.2.1 Test Result Models

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class ExecutionTiming:
    """Detailed execution timing information"""
    start: datetime
    end: datetime
    duration_seconds: float
    timezone: str = "UTC"

    def to_dict(self) -> dict[str, Any]:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "duration_seconds": self.duration_seconds,
            "timezone": self.timezone,
        }

@dataclass
class BrowserTestResult(ValidatedModel):
    """Complete browser test result"""

    # Core results
    success: bool
    test_name: str
    duration: float
    steps_executed: int
    report: str = ""

    # Provider information
    provider: Optional[str] = None
    model: Optional[str] = None
    browser: Optional[str] = None

    # Browser configuration
    headless: bool = False
    viewport_size: str = "1920,1080"

    # Detailed metrics (using nested models)
    execution_time: Optional[ExecutionTiming] = None
    environment: dict[str, Any] = field(default_factory=dict)
    token_usage: Optional['TokenMetrics'] = None
    metrics: dict[str, Any] = field(default_factory=dict)

    # Optional fields
    error: Optional[str] = None
    steps: list[dict[str, Any]] = field(default_factory=list)
    verbose_log: Optional[dict[str, Any]] = None

    # Backward compatibility
    @property
    def duration_seconds(self) -> float:
        """Alias for backward compatibility"""
        return self.duration

    def validate(self) -> None:
        """Validate test result constraints"""
        if self.duration < 0:
            raise ValueError("Duration cannot be negative")
        if self.steps_executed < 0:
            raise ValueError("Steps executed cannot be negative")
        if not self.test_name:
            raise ValueError("Test name cannot be empty")

        # Validate viewport format
        if not re.match(r'^\d+,\d+$', self.viewport_size):
            raise ValueError(f"Invalid viewport size format: {self.viewport_size}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to legacy dictionary format"""
        result = {
            "success": self.success,
            "test_name": self.test_name,
            "duration": self.duration,
            "duration_seconds": self.duration,  # Backward compat
            "steps_executed": self.steps_executed,
            "report": self.report,
            "provider": self.provider,
            "model": self.model,
            "browser": self.browser,
            "headless": self.headless,
            "viewport_size": self.viewport_size,
            "environment": self.environment,
            "metrics": self.metrics,
            "steps": self.steps,
        }

        # Add optional fields if present
        if self.execution_time:
            result["execution_time"] = self.execution_time.to_dict()
        if self.token_usage:
            result["token_usage"] = self.token_usage.to_dict()
        if self.error:
            result["error"] = self.error
        if self.verbose_log:
            result["verbose_log"] = self.verbose_log

        return result
```

#### 2.2.2 Token Metrics Models

```python
@dataclass
class OptimizationSavings:
    """Token optimization savings details"""
    original_tokens: int
    optimized_tokens: int
    reduction_percentage: float
    strategies_applied: list[str]
    estimated_savings: Optional[float] = None

    def validate(self) -> None:
        if self.original_tokens < self.optimized_tokens:
            raise ValueError("Original tokens cannot be less than optimized")
        if not 0 <= self.reduction_percentage <= 100:
            raise ValueError("Reduction percentage must be between 0 and 100")

@dataclass
class TokenMetrics(ValidatedModel):
    """Token usage and cost metrics"""

    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    estimated_cost: Optional[float] = None
    cost_source: str = "telemetry"

    # Context usage
    context_length: Optional[int] = None
    max_context_length: Optional[int] = None
    context_usage_percentage: Optional[float] = None

    # Optimization
    optimization_savings: Optional[OptimizationSavings] = None

    def validate(self) -> None:
        """Validate token metrics"""
        if self.total_tokens < 0:
            raise ValueError("Token counts cannot be negative")
        if self.total_tokens != self.prompt_tokens + self.completion_tokens:
            raise ValueError("Total tokens must equal prompt + completion tokens")
        if self.context_usage_percentage is not None:
            if not 0 <= self.context_usage_percentage <= 100:
                raise ValueError("Context usage must be between 0 and 100")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary format"""
        result = {
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cost_source": self.cost_source,
        }

        # Add optional fields
        if self.estimated_cost is not None:
            result["estimated_cost"] = self.estimated_cost
        if self.context_length is not None:
            result["context_length"] = self.context_length
        if self.max_context_length is not None:
            result["max_context_length"] = self.max_context_length
        if self.context_usage_percentage is not None:
            result["context_usage_percentage"] = self.context_usage_percentage
        if self.optimization_savings:
            result["optimization"] = dataclasses.asdict(self.optimization_savings)

        return result
```

#### 2.2.3 Execution Models

```python
@dataclass
class ExecutionStep:
    """Single execution step with enhanced typing"""

    type: Literal["tool_call", "agent_message"]
    name: Optional[str]
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "name": self.name,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

@dataclass
class ExecutionMetadata:
    """Metadata about test execution"""

    test_name: str
    provider: str
    model: str
    browser_options: BrowserOptions

    # Flags
    token_optimization_enabled: bool = False
    compression_level: str = "medium"
    verbose_enabled: bool = False

    # Additional metadata
    session_id: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    custom_data: dict[str, Any] = field(default_factory=dict)
```

### 2.3 Factory Classes

```python
class ResultFactory:
    """Factory for creating result objects"""

    @staticmethod
    def create_browser_test_result(
        execution_result: ExecutionResult,
        metadata: ExecutionMetadata,
        token_metrics: Optional[TokenMetrics] = None,
    ) -> BrowserTestResult:
        """Create a complete browser test result"""

        # Calculate timing
        execution_time = ExecutionTiming(
            start=metadata.start_time,
            end=datetime.now(UTC),
            duration_seconds=execution_result.duration,
        )

        # Build environment info
        environment = {
            "token_optimization_enabled": metadata.token_optimization_enabled,
            "compression_level": metadata.compression_level,
            "session_id": metadata.session_id,
        }

        return BrowserTestResult(
            success=execution_result.success,
            test_name=metadata.test_name,
            duration=execution_result.duration,
            steps_executed=len(execution_result.steps),
            report=execution_result.final_response.content if execution_result.final_response else "",
            provider=metadata.provider,
            model=metadata.model,
            browser=metadata.browser_options.browser,
            headless=metadata.browser_options.headless,
            viewport_size=f"{metadata.browser_options.viewport_width},{metadata.browser_options.viewport_height}",
            execution_time=execution_time,
            environment=environment,
            token_usage=token_metrics,
            metrics=self._build_metrics(execution_result),
        )
```

### 2.4 Serialization Strategy

```python
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import json

class ModelEncoder(json.JSONEncoder):
    """Custom JSON encoder for data models"""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Path):
            return str(obj)
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif dataclasses.is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)

class ModelSerializer:
    """Serialization utilities for data models"""

    @staticmethod
    def to_json(model: SerializableModel) -> str:
        """Serialize model to JSON"""
        return json.dumps(model.to_dict(), cls=ModelEncoder, indent=2)

    @staticmethod
    def from_json(json_str: str, model_class: type[T]) -> T:
        """Deserialize model from JSON"""
        data = json.loads(json_str)
        return model_class.from_dict(data)
```

## 3. Migration Strategy

### 3.1 Compatibility Layer

```python
# In core.py
def run_test_suite(self, ...) -> dict[str, Any]:
    """Execute test suite - maintains dict return type"""

    # Internal code uses data models
    result = self._execute_test_internal(...)  # Returns BrowserTestResult

    # Convert to dict for backward compatibility
    return result.to_dict()

def _execute_test_internal(self, ...) -> BrowserTestResult:
    """Internal method using data models"""
    # ... implementation using typed models ...
```

### 3.2 Gradual Migration Path

1. **Phase 1**: Add models alongside existing code
   ```python
   # Old code still works
   result_dict = {"success": True, ...}

   # New code can use models
   result_model = BrowserTestResult.from_dict(result_dict)
   ```

2. **Phase 2**: Update internals to use models
   ```python
   # Components return models
   def analyze(self, ...) -> TestResult:  # Changed from dict
       return TestResult(...)
   ```

3. **Phase 3**: Add compatibility warnings
   ```python
   def get_result_dict(self) -> dict[str, Any]:
       warnings.warn(
           "get_result_dict() is deprecated, use get_result() for typed access",
           DeprecationWarning,
           stacklevel=2
       )
       return self.get_result().to_dict()
   ```

## 4. Validation Strategy

### 4.1 Validation Levels

1. **Construction Time**: Basic type validation (automatic with dataclasses)
2. **Post-Init**: Business rule validation (in validate() method)
3. **Pre-Serialization**: Output format validation
4. **Runtime**: Optional stricter validation with Pydantic

### 4.2 Validation Examples

```python
@dataclass
class StrictTokenMetrics(BaseModel):  # Pydantic for strict validation
    """Token metrics with strict validation"""

    total_tokens: int = Field(ge=0, description="Total token count")
    prompt_tokens: int = Field(ge=0, description="Prompt token count")
    completion_tokens: int = Field(ge=0, description="Completion token count")
    estimated_cost: Optional[float] = Field(ge=0, description="Estimated cost in USD")

    @validator('total_tokens')
    def validate_total(cls, v, values):
        prompt = values.get('prompt_tokens', 0)
        completion = values.get('completion_tokens', 0)
        if v != prompt + completion:
            raise ValueError('Total must equal prompt + completion')
        return v

    class Config:
        # Pydantic config
        validate_assignment = True
        use_enum_values = True
```

## 5. Testing Strategy

### 5.1 Model Testing

```python
import pytest
from hypothesis import given, strategies as st

class TestBrowserTestResult:
    """Tests for BrowserTestResult model"""

    def test_construction_valid(self):
        """Test valid model construction"""
        result = BrowserTestResult(
            success=True,
            test_name="Test",
            duration=10.5,
            steps_executed=5,
        )
        assert result.duration_seconds == 10.5  # Test compat property

    def test_validation_negative_duration(self):
        """Test validation rejects negative duration"""
        with pytest.raises(ValueError, match="Duration cannot be negative"):
            BrowserTestResult(
                success=True,
                test_name="Test",
                duration=-1,
                steps_executed=5,
            )

    @given(
        duration=st.floats(min_value=0, max_value=3600),
        steps=st.integers(min_value=0, max_value=1000),
    )
    def test_property_based_validation(self, duration, steps):
        """Property-based testing for model validation"""
        result = BrowserTestResult(
            success=True,
            test_name="Test",
            duration=duration,
            steps_executed=steps,
        )
        assert result.duration >= 0
        assert result.steps_executed >= 0

    def test_serialization_roundtrip(self):
        """Test serialization round trip"""
        original = BrowserTestResult(
            success=True,
            test_name="Test",
            duration=10.5,
            steps_executed=5,
            token_usage=TokenMetrics(
                total_tokens=100,
                prompt_tokens=80,
                completion_tokens=20,
            )
        )

        # Serialize and deserialize
        json_str = ModelSerializer.to_json(original)
        restored = ModelSerializer.from_json(json_str, BrowserTestResult)

        assert restored == original
```

## 6. Performance Considerations

### 6.1 Optimization Techniques

1. **Use __slots__ for frequently created objects**:
   ```python
   @dataclass
   class ExecutionStep:
       __slots__ = ('type', 'name', 'content', 'timestamp')
       type: str
       name: Optional[str]
       content: str
       timestamp: datetime
   ```

2. **Lazy property computation**:
   ```python
   @dataclass
   class TokenMetrics:
       _cost_per_token: Optional[float] = field(default=None, init=False)

       @property
       def cost_per_token(self) -> float:
           if self._cost_per_token is None:
               self._cost_per_token = self.estimated_cost / self.total_tokens
           return self._cost_per_token
   ```

3. **Caching serialization results**:
   ```python
   @dataclass
   class CachedModel:
       _dict_cache: Optional[dict] = field(default=None, init=False, compare=False)

       def to_dict(self) -> dict[str, Any]:
           if self._dict_cache is None:
               self._dict_cache = self._compute_dict()
           return self._dict_cache
   ```

## 7. Documentation Integration

### 7.1 Auto-generated Documentation

```python
@dataclass
class BrowserTestResult:
    """
    Complete browser test result.

    This model represents the full outcome of a browser-based test execution,
    including success status, timing information, and detailed metrics.

    Attributes:
        success: Whether the test passed
        test_name: Name of the test scenario
        duration: Test execution time in seconds
        steps_executed: Number of steps executed
        report: Detailed test report in markdown format

    Example:
        >>> result = BrowserTestResult(
        ...     success=True,
        ...     test_name="Login Test",
        ...     duration=10.5,
        ...     steps_executed=5,
        ...     report="Test completed successfully"
        ... )
        >>> result.duration_seconds  # Backward compatible
        10.5
    """
```

### 7.2 Type Stubs for External Use

```python
# browser_copilot/models/__init__.pyi
from typing import Optional, Any
from datetime import datetime

class BrowserTestResult:
    success: bool
    test_name: str
    duration: float
    steps_executed: int
    report: str
    # ... other fields ...

    def to_dict(self) -> dict[str, Any]: ...

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BrowserTestResult: ...

    @property
    def duration_seconds(self) -> float: ...
```
