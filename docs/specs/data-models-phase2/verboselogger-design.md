# VerboseLogger Data Model Design

## Current State Analysis

### Problems with Current Implementation

1. **Unstructured Data**: Log entries stored as `dict[str, Any]`
2. **No Type Safety**: Can add any fields to log entries
3. **Difficult Analysis**: Hard to programmatically analyze logs
4. **Inconsistent Format**: Log structure can vary
5. **Manual Serialization**: Custom JSON encoding for different types

### Current Data Structures

```python
# Current untyped storage
self.execution_steps: list[dict[str, Any]] = []
self.tool_calls: list[dict[str, Any]] = []
self.token_metrics: dict[str, Any] = {}
```

## Proposed Model Design

### Core Logging Models

#### ExecutionStep Model
```python
@dataclass
class ExecutionStep(SerializableModel):
    """Represents a single execution step in the test."""
    timestamp: datetime
    type: StepType  # Enum for consistency
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    level: LogLevel = LogLevel.INFO
    duration_ms: Optional[float] = None

    @property
    def formatted_timestamp(self) -> str:
        """ISO format timestamp for consistency."""
        return self.timestamp.isoformat()

    @property
    def elapsed_since(self, start: datetime) -> float:
        """Elapsed time since a reference point."""
        return (self.timestamp - start).total_seconds()
```

#### ToolCall Model
```python
@dataclass
class ToolCall(SerializableModel):
    """Browser tool invocation with timing and results."""
    timestamp: datetime
    tool_name: str
    parameters: Dict[str, Any]
    result: Any
    duration_ms: Optional[float] = None
    success: bool = True
    error: Optional[str] = None

    def get_truncated_result(self, max_length: int = 200) -> Any:
        """Get result suitable for display."""
        if isinstance(self.result, str) and len(self.result) > max_length:
            return self.result[:max_length] + "..."
        # Handle other types
        return self._truncate_value(self.result, max_length)
```

#### LogSession Model
```python
@dataclass
class LogSession(SerializableModel):
    """Complete logging session with all events."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    log_file: Optional[Path] = None
    test_name: Optional[str] = None

    # Event collections
    execution_steps: List[ExecutionStep] = field(default_factory=list)
    tool_calls: List[ToolCall] = field(default_factory=list)
    token_usage_logs: List[TokenUsageLog] = field(default_factory=list)
    errors: List[ErrorLog] = field(default_factory=list)

    @property
    def duration(self) -> Optional[float]:
        """Total session duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def total_tokens(self) -> int:
        """Total tokens used across all LLM calls."""
        return sum(log.total_tokens for log in self.token_usage_logs)

    @property
    def total_cost(self) -> float:
        """Total estimated cost."""
        return sum(
            log.estimated_cost for log in self.token_usage_logs
            if log.estimated_cost
        )

    def get_timeline(self) -> List[Union[ExecutionStep, ToolCall, ErrorLog]]:
        """Get all events in chronological order."""
        events = []
        events.extend(self.execution_steps)
        events.extend(self.tool_calls)
        events.extend(self.errors)
        return sorted(events, key=lambda e: e.timestamp)
```

### Enum Definitions

```python
class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

class StepType(Enum):
    # Browser actions
    NAVIGATION = "navigation"
    INTERACTION = "interaction"
    VERIFICATION = "verification"
    SCREENSHOT = "screenshot"

    # Tool lifecycle
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"

    # LLM interactions
    LLM_CALL = "llm_call"
    LLM_RESPONSE = "llm_response"

    # Test lifecycle
    TEST_START = "test_start"
    TEST_END = "test_end"

    # Other
    CUSTOM = "custom"
```

## Benefits of Structured Logging

### 1. Type Safety
```python
# Before: Error-prone dict access
step = {"timestamp": datetime.now(), "type": "navigaton"}  # Typo!

# After: IDE catches typos
step = ExecutionStep(
    timestamp=datetime.now(),
    type=StepType.NAVIGATION,  # Enum prevents typos
    description="Navigate to login page"
)
```

### 2. Consistent Structure
```python
# All log entries have guaranteed fields
for step in session.execution_steps:
    print(f"{step.formatted_timestamp}: {step.description}")
    # No KeyError possible!
```

### 3. Rich Analysis
```python
# Easy to analyze performance
navigation_steps = [
    s for s in session.execution_steps
    if s.type == StepType.NAVIGATION
]
avg_duration = statistics.mean(s.duration_ms for s in navigation_steps)

# Timeline analysis
timeline = session.get_timeline()
for i, event in enumerate(timeline[:-1]):
    gap = (timeline[i+1].timestamp - event.timestamp).total_seconds()
    if gap > 5:
        print(f"Long gap ({gap}s) after {event}")
```

### 4. Serialization Control
```python
# Consistent JSON output
log_data = session.to_dict()
# Guaranteed structure for log parsing tools
```

## Integration with Existing Code

### Updated VerboseLogger Methods

```python
class VerboseLogger:
    def __init__(self, ...):
        # Create session
        self.session = LogSession(
            session_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            start_time=datetime.now(),
            log_file=self.log_file
        )

    def log_step(self, step_type: str, description: str,
                 details: dict[str, Any] | None = None,
                 level: str = "INFO") -> None:
        """Log an execution step with proper typing."""
        step = ExecutionStep(
            timestamp=datetime.now(),
            type=StepType[step_type.upper()],
            description=description,
            details=details or {},
            level=LogLevel[level]
        )
        self.session.execution_steps.append(step)

        # Still log to file/console
        self._write_log(step)

    def get_execution_summary(self) -> dict[str, Any]:
        """Get structured summary using models."""
        return self.session.get_summary()
```

## Backward Compatibility

### Dual Interface Period

```python
def log_tool_call(self, tool_name: str, parameters: dict[str, Any],
                  result: Any, duration_ms: float | None = None) -> None:
    """Log tool call with backward compatibility."""
    # Create model
    tool_call = ToolCall(
        timestamp=datetime.now(),
        tool_name=tool_name,
        parameters=parameters,
        result=result,
        duration_ms=duration_ms
    )
    self.session.tool_calls.append(tool_call)

    # Also maintain old dict format temporarily
    if self._legacy_mode:
        self.tool_calls.append(tool_call.to_dict())
```

## Log Analysis Tools

### Example Analysis Script

```python
def analyze_log_session(log_file: Path) -> LogAnalysis:
    """Analyze a log file using structured models."""
    with open(log_file) as f:
        data = json.load(f)

    session = LogSession.from_dict(data)

    return LogAnalysis(
        total_duration=session.duration,
        total_steps=len(session.execution_steps),
        total_tokens=session.total_tokens,
        errors=len(session.errors),
        avg_tool_duration=statistics.mean(
            tc.duration_ms for tc in session.tool_calls
            if tc.duration_ms
        )
    )
```

## Migration Strategy

1. **Add Models**: Implement all logging models
2. **Dual Storage**: Store both models and dicts temporarily
3. **Update Consumers**: Update log analysis tools
4. **Remove Legacy**: Remove dict storage after migration

## Performance Considerations

1. **Lazy Loading**: Don't load full log history into memory
2. **Streaming**: Support streaming large log files
3. **Indexing**: Add timestamp indexing for quick searches
4. **Compression**: Compress old log sessions

## Future Enhancements

1. **Log Filtering**: Filter logs by type, level, time range
2. **Log Export**: Export to different formats (CSV, Parquet)
3. **Real-time Analysis**: Analyze logs as they're generated
4. **Distributed Logging**: Support for distributed test execution
