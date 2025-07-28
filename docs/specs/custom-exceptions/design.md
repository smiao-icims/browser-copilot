# Custom Exceptions - Design

## 1. Overview

This document describes the technical design for implementing custom exceptions in Browser Copilot, including class hierarchy, implementation patterns, and integration approach.

## 2. Architecture

### 2.1 Exception Hierarchy

```
BrowserPilotError (base)
├── ConfigurationError
│   ├── MissingConfigError
│   ├── InvalidConfigError
│   └── ProviderConfigError
├── ExecutionError
│   ├── TestExecutionError
│   ├── StepExecutionError
│   └── TimeoutError
├── BrowserError
│   ├── BrowserInitError
│   ├── BrowserOperationError
│   └── MCPConnectionError
├── ValidationError
│   ├── InputValidationError
│   ├── TestValidationError
│   └── OutputValidationError
├── ResourceError
│   ├── FileAccessError
│   ├── StorageError
│   └── NetworkError
└── AuthenticationError
    ├── APIKeyError
    └── TokenError
```

### 2.2 Base Exception Class

```python
# browser_copilot/exceptions.py

from typing import Any, Optional
import json
from datetime import datetime

class BrowserPilotError(Exception):
    """Base exception for all Browser Copilot errors.
    
    Provides context information and optional suggestions for resolution.
    """
    
    def __init__(
        self,
        message: str,
        context: Optional[dict[str, Any]] = None,
        suggestion: Optional[str] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.suggestion = suggestion
        self.error_code = error_code
        self.timestamp = datetime.utcnow()
        
        # Add automatic context
        self._add_automatic_context()
    
    def _add_automatic_context(self) -> None:
        """Add automatic context information."""
        import platform
        self.context.update({
            "timestamp": self.timestamp.isoformat(),
            "python_version": platform.python_version(),
            "platform": platform.system(),
            "error_type": self.__class__.__name__
        })
    
    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            "error": self.message,
            "type": self.__class__.__name__,
            "code": self.error_code,
            "context": self.context,
            "suggestion": self.suggestion,
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        """Convert exception to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        parts = [f"{self.__class__.__name__}: {self.message}"]
        
        if self.error_code:
            parts.append(f"Code: {self.error_code}")
            
        if self.context:
            # Show only key context items in string
            key_context = {k: v for k, v in self.context.items() 
                          if k in ["path", "provider", "browser", "step"]}
            if key_context:
                parts.append(f"Context: {key_context}")
        
        if self.suggestion:
            parts.append(f"Suggestion: {self.suggestion}")
            
        return " | ".join(parts)
```

### 2.3 Specific Exception Classes

```python
class ConfigurationError(BrowserPilotError):
    """Raised for configuration-related errors."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        if config_key:
            kwargs.setdefault("context", {})["config_key"] = config_key
        super().__init__(message, **kwargs)


class TestExecutionError(BrowserPilotError):
    """Raised when test execution fails."""
    
    def __init__(
        self,
        message: str,
        test_file: Optional[str] = None,
        step_number: Optional[int] = None,
        **kwargs
    ):
        context = kwargs.setdefault("context", {})
        if test_file:
            context["test_file"] = test_file
        if step_number:
            context["step_number"] = step_number
        super().__init__(message, **kwargs)
```

### 2.4 Exception Factory

```python
class ExceptionFactory:
    """Factory for creating consistent exceptions."""
    
    @staticmethod
    def configuration_not_found(key: str, available: list[str]) -> ConfigurationError:
        return ConfigurationError(
            f"Configuration key '{key}' not found",
            context={"key": key, "available": available},
            suggestion=f"Available keys: {', '.join(available)}",
            error_code="CONFIG_001"
        )
    
    @staticmethod
    def browser_not_supported(browser: str) -> ValidationError:
        valid = ["chromium", "firefox", "safari", "edge", "webkit"]
        return ValidationError(
            f"Browser '{browser}' is not supported",
            context={"browser": browser, "valid": valid},
            suggestion=f"Choose from: {', '.join(valid)}",
            error_code="BROWSER_001"
        )
```

## 3. Integration Design

### 3.1 Error Handler Decorator

```python
from functools import wraps
from typing import Type, Callable

def handle_errors(
    *exception_types: Type[Exception],
    wrap_with: Optional[Type[BrowserPilotError]] = None
):
    """Decorator to handle and wrap exceptions."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except exception_types as e:
                if wrap_with:
                    raise wrap_with(
                        str(e),
                        context={"original_error": type(e).__name__},
                        suggestion="Check the logs for more details"
                    ) from e
                raise
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                if wrap_with:
                    raise wrap_with(
                        str(e),
                        context={"original_error": type(e).__name__}
                    ) from e
                raise
                
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator
```

### 3.2 Context Manager for Error Context

```python
from contextlib import contextmanager

@contextmanager
def error_context(**context):
    """Add context to any exceptions raised within the block."""
    try:
        yield
    except BrowserPilotError as e:
        e.context.update(context)
        raise
    except Exception as e:
        # Wrap non-BrowserPilot exceptions
        raise BrowserPilotError(
            str(e),
            context=context,
            suggestion="An unexpected error occurred"
        ) from e
```

## 4. Usage Patterns

### 4.1 Basic Usage

```python
# Simple exception
raise ConfigurationError("API key not found")

# With context
raise ConfigurationError(
    "Invalid configuration file",
    context={"path": "/path/to/config.json", "error": "JSON decode error"}
)

# With suggestion
raise BrowserError(
    "Failed to connect to browser",
    suggestion="Ensure browser is installed: npm install -g @modelcontextprotocol/server-playwright"
)
```

### 4.2 Using Factory

```python
# Consistent error creation
raise ExceptionFactory.configuration_not_found("api_key", ["provider", "model"])
```

### 4.3 Using Decorators

```python
@handle_errors(FileNotFoundError, PermissionError, wrap_with=ResourceError)
async def read_test_file(path: Path) -> str:
    return path.read_text()
```

### 4.4 Using Context Manager

```python
with error_context(operation="test_execution", file=test_path):
    # Any exceptions here will have context added
    result = await run_test(content)
```

## 5. Logging Integration

```python
import logging

class ExceptionLogger:
    """Log exceptions with full context."""
    
    @staticmethod
    def log_exception(e: BrowserPilotError, logger: logging.Logger):
        """Log exception with appropriate level."""
        logger.error(
            e.message,
            extra={
                "error_code": e.error_code,
                "context": e.context,
                "suggestion": e.suggestion,
                "exception_type": type(e).__name__
            },
            exc_info=True
        )
```

## 6. Testing Strategy

### 6.1 Exception Testing Utils

```python
# tests/utils/exception_helpers.py

def assert_exception_valid(exc: BrowserPilotError):
    """Assert exception has required attributes."""
    assert exc.message
    assert exc.timestamp
    assert isinstance(exc.context, dict)
    assert exc.to_dict()
    assert exc.to_json()
```

## 7. Migration Strategy

### 7.1 Compatibility Layer

```python
# Temporary compatibility during migration
def create_value_error(message: str) -> Exception:
    """Create exception with deprecation warning."""
    import warnings
    warnings.warn(
        "create_value_error is deprecated, use ValidationError",
        DeprecationWarning,
        stacklevel=2
    )
    return ValidationError(message)
```

## 8. Performance Considerations

- Lazy context evaluation for expensive operations
- Minimal overhead in exception creation
- Efficient serialization for large contexts
- No circular references in context data

## 9. Security Considerations

- Sanitize paths in context (no absolute paths with username)
- Never include passwords or API keys in context
- Redact sensitive environment variables
- Limit context size to prevent memory issues