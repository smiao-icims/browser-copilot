# Core.py Data Model Migration Plan

## Overview

This document outlines the plan for migrating core.py from dictionary-based data structures to strongly-typed models while maintaining backward compatibility.

## Current State Analysis

### Dictionary Structure in core.py

The `run_test_suite` method currently returns a dictionary with the following structure:

```python
{
    # Basic info
    "success": bool,
    "provider": str,
    "model": str,
    "browser": str,
    "headless": bool,
    "viewport_size": str,  # "1920x1080"
    "test_name": str,

    # Execution timing
    "execution_time": {
        "start": str,  # ISO format
        "end": str,    # ISO format
        "duration_seconds": float,
        "timezone": str
    },
    "duration": float,  # Same as duration_seconds
    "duration_seconds": float,  # Backward compatibility

    # Environment info
    "environment": {
        "token_optimization": bool,
        "compression_level": str
    },

    # Execution details
    "steps_executed": int,
    "steps": [
        {
            "type": "tool_call" | "agent_message",
            "name": str | None,  # Tool name
            "content": str
        }
    ],

    # Results
    "report": str,
    "error": str | None,  # Only if failed

    # Token usage
    "token_usage": {
        "total_tokens": int,
        "prompt_tokens": int,
        "completion_tokens": int,
        "estimated_cost": float,
        "context_length": int,
        "max_context_length": int,
        "context_usage_percentage": float,
        "optimization": {
            "original_tokens": int,
            "optimized_tokens": int,
            "reduction_percentage": float,
            "strategies_applied": list[str],
            "estimated_savings": float
        }
    },

    # Metrics
    "metrics": {
        "total_steps": int,
        "execution_time_ms": float,
        "avg_step_time_ms": float
    },

    # Optional verbose log
    "verbose_log": {
        "log_file": str,
        "summary": dict
    }
}
```

## Migration Strategy

### Phase 1: Internal Model Usage (Maintain Dict API)

1. **Create models internally** in `run_test_suite`
2. **Use models throughout execution** for type safety
3. **Convert to dict at the end** to maintain API compatibility
4. **No breaking changes** for consumers

### Phase 2: Gradual API Migration

1. **Add new method** `run_test_suite_typed()` that returns models
2. **Deprecate dict return** with warnings
3. **Provide migration guide** for consumers
4. **Remove dict API** in next major version

## Implementation Steps

### Step 1: Update Imports

```python
from .models.execution import ExecutionStep, ExecutionMetadata, ExecutionTiming
from .models.metrics import TokenMetrics, OptimizationSavings
from .models.results import BrowserTestResult
```

### Step 2: Create ExecutionMetadata Early

```python
# In run_test_suite, after parameter validation
metadata = ExecutionMetadata(
    test_name=test_name,
    provider=self.provider,
    model=self.model,
    browser=browser,
    headless=headless,
    viewport_width=viewport_width,
    viewport_height=viewport_height,
    token_optimization_enabled=self.token_optimizer is not None,
    compression_level=self.config.get("compression_level", "medium"),
    verbose_enabled=self.verbose_logger is not None,
    session_id=kwargs.get("_session_dir", str(uuid.uuid4()))
)
```

### Step 3: Track ExecutionSteps

```python
# Replace steps list with typed steps
execution_steps: List[ExecutionStep] = []

# In the streaming loop
for tool_msg in chunk.get("tools", {}).get("messages", []):
    if hasattr(tool_msg, "name") and hasattr(tool_msg, "content"):
        step = ExecutionStep(
            type="tool_call",
            name=tool_msg.name,
            content=str(tool_msg.content)
        )
        execution_steps.append(step)
```

### Step 4: Build TokenMetrics

```python
# In _get_token_usage, return TokenMetrics instead of dict
def _get_token_usage(self) -> Optional[TokenMetrics]:
    if not self.telemetry:
        return None

    # ... existing logic ...

    optimization = None
    if self.token_optimizer and opt_metrics["original_tokens"] > 0:
        optimization = OptimizationSavings(
            original_tokens=opt_metrics["original_tokens"],
            optimized_tokens=opt_metrics["optimized_tokens"],
            reduction_percentage=opt_metrics["reduction_percentage"],
            strategies_applied=opt_metrics["strategies_applied"],
            estimated_savings=savings
        )

    return TokenMetrics(
        total_tokens=total,
        prompt_tokens=prompt,
        completion_tokens=completion,
        estimated_cost=cost,
        context_length=context_length,
        max_context_length=max_context,
        context_usage_percentage=usage_percent,
        optimization=optimization
    )
```

### Step 5: Create BrowserTestResult

```python
# After execution completes
timing = ExecutionTiming(
    start=start_time,
    end=end_time,
    duration_seconds=duration,
    timezone="UTC"
)

result = BrowserTestResult(
    success=self._check_success(report_content),
    test_name=test_name,
    duration=duration,
    report=report_content if success else None,
    error=None if success else "Test failed",
    steps=execution_steps,
    execution_time=timing,
    metrics=metrics,
    token_usage=token_metrics,
    environment={
        "token_optimization": self.token_optimizer is not None,
        "compression_level": self.config.get("compression_level", "medium")
    },
    verbose_log=verbose_log if self.verbose_logger else None,
    # Browser-specific fields
    provider=self.provider,
    model=self.model,
    browser=browser,
    headless=headless,
    viewport_size=viewport_size
)

# Convert to dict for backward compatibility
return result.to_dict()
```

### Step 6: Update Helper Methods

```python
def _extract_steps(self, steps: list) -> List[ExecutionStep]:
    """Extract typed steps from agent execution"""
    execution_steps = []

    for step in steps:
        # ... existing logic but create ExecutionStep instances

    return execution_steps

def _check_success(self, report_content: str) -> bool:
    # No changes needed - already returns bool
    pass
```

## Benefits of Migration

1. **Type Safety**: Catch errors at development time
2. **Validation**: Automatic validation of data constraints
3. **Documentation**: Models serve as API documentation
4. **Maintainability**: Easier to refactor and extend
5. **Testing**: Stronger guarantees about data structure

## Backward Compatibility

### Maintaining Dict API

```python
# In BrowserTestResult.to_dict()
def to_dict(self) -> Dict[str, Any]:
    data = super().to_dict()

    # Add backward compatibility fields
    data["duration_seconds"] = data["duration"]

    # Flatten execution_time for compatibility
    if "execution_time" in data:
        timing = data["execution_time"]
        data["execution_time"] = {
            "start": timing["start"],
            "end": timing["end"],
            "duration_seconds": timing["duration_seconds"],
            "timezone": timing["timezone"]
        }

    return data
```

### Migration Helper

```python
# Add to core.py
def run_test_suite_typed(self, ...) -> BrowserTestResult:
    """New method that returns typed result"""
    # Same implementation but return model instead of dict

def run_test_suite(self, ...) -> Dict[str, Any]:
    """Existing method - now delegates to typed version"""
    result = self.run_test_suite_typed(...)
    return result.to_dict()
```

## Testing Strategy

1. **Unit Tests**: Test model creation and validation
2. **Integration Tests**: Ensure dict output matches existing format
3. **Compatibility Tests**: Verify no breaking changes
4. **Performance Tests**: Ensure no significant overhead

## Rollout Plan

### Version 1.1 (Current)
- Internal model usage
- Dict API maintained
- No breaking changes

### Version 1.2
- Add `run_test_suite_typed()` method
- Add deprecation warnings to dict method
- Update documentation

### Version 2.0
- Remove dict-based API
- Models become primary interface
- Migration guide for users

## Risk Mitigation

1. **Extensive Testing**: Full test coverage before release
2. **Gradual Rollout**: Internal usage first
3. **Clear Documentation**: Migration guides and examples
4. **Backward Compatibility**: No breaking changes initially
5. **Performance Monitoring**: Track any overhead
