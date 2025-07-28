# Browser Copilot MVP Technical Design

**Date**: January 26, 2025  
**Version**: 1.0  
**Status**: Draft

## Overview

This document describes the technical design for implementing the Browser Copilot MVP enhancements outlined in requirements.md. The design focuses on maintaining backward compatibility while adding new features for improved debugging, flexibility, and user experience.

## Architecture Changes

### Current Architecture

```
CLI (cli.py) → BrowserPilot (core.py) → LangChain Agent → MCP Tools → Browser
                                      ↓
                                   Reporter (reporter.py)
```

### Enhanced Architecture

```
CLI (cli.py) → InputHandler → BrowserPilot (core.py) → LangChain Agent → MCP Tools → Browser
     ↓                              ↓                          ↓
  ConfigManager              VerboseLogger            StreamingHandler
     ↓                              ↓
  StorageManager                    ↓
                              EnhancedReporter (reporter.py)
                                    ↓
                               ~/.browser_copilot/
                               ├── logs/
                               ├── settings/
                               ├── memory/
                               ├── reports/
                               └── screenshots/
```

## Component Design

### 1. Enhanced CLI Module (`cli.py`)

**New Command-Line Arguments**:
```python
# Existing arguments remain unchanged
parser.add_argument("--test-suite", help="Path to test suite file or '-' for stdin")
parser.add_argument("--provider", help="LLM provider (optional, uses ModelForge default)")
parser.add_argument("--model", help="Model name (optional, uses ModelForge default)")

# New arguments
parser.add_argument("--system-prompt", help="Custom system prompt text")
parser.add_argument("--system-prompt-file", help="Path to custom system prompt file")
parser.add_argument("-o", "--output", help="Output destination (console/file/directory)")
parser.add_argument("--enhance-test-suite", action="store_true", 
                   help="Generate LLM-optimized version of test suite")
parser.add_argument("--no-screenshots", action="store_true",
                   help="Disable automatic screenshot capture")
parser.add_argument("--optimize-tokens", choices=["minimal", "balanced", "aggressive"],
                   help="Enable token optimization to reduce costs")
```

**Key Changes**:
- Refactor `parse_arguments()` to handle optional provider/model
- Add `InputHandler` class for stdin/file input management
- Implement `ConfigManager` for ModelForge integration
- Add pre-execution authentication check

### 2. Configuration Manager

```python
class ConfigManager:
    """Manages ModelForge configuration and authentication"""
    
    def __init__(self):
        self.registry = ModelForgeRegistry()
    
    def get_default_config(self) -> tuple[str, str]:
        """Get default provider and model from ModelForge"""
        # Query ModelForge for active configuration
        # Return (provider, model) tuple
        
    def check_authentication(self, provider: str) -> bool:
        """Check if provider is authenticated"""
        # Verify authentication status
        
    def trigger_authentication(self, provider: str):
        """Trigger authentication flow for provider"""
        # Handle device flow for github_copilot
        # Display instructions and wait for completion
```

### 3. Verbose Logging System

```python
import logging
from pathlib import Path
from datetime import datetime

class VerboseLogger:
    """Handles verbose output during test execution with dual output"""
    
    def __init__(self, enabled: bool = False, test_id: str = None):
        self.enabled = enabled
        self.start_time = datetime.now()
        self.test_id = test_id or self.start_time.strftime("%Y%m%d_%H%M%S")
        
        # Setup local storage
        self.storage_dir = Path.home() / ".browser_copilot"
        self.logs_dir = self.storage_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup file logging
        if self.enabled:
            self.log_file = self.logs_dir / f"test_{self.test_id}.log"
            self._setup_file_logger()
        
    def _setup_file_logger(self):
        """Configure file-based logging"""
        self.file_logger = logging.getLogger(f"browser_copilot.{self.test_id}")
        self.file_logger.setLevel(logging.DEBUG)
        
        # File handler with detailed formatting
        file_handler = logging.FileHandler(self.log_file)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S.%f'
        )
        file_handler.setFormatter(file_formatter)
        self.file_logger.addHandler(file_handler)
        
    def log_step(self, step_type: str, details: dict):
        """Log execution step with timestamp to console and file"""
        if not self.enabled:
            return
        
        timestamp = datetime.now().isoformat()
        
        # Console output (formatted for readability)
        console_output = self._format_console_output(step_type, details, timestamp)
        print(console_output, flush=True)
        
        # File output (structured for parsing)
        file_output = self._format_file_output(step_type, details, timestamp)
        self.file_logger.info(file_output)
    
    def _format_console_output(self, step_type: str, details: dict, timestamp: str) -> str:
        """Format step information for console display"""
        # Color coding and human-readable format
        colors = {
            "tool_start": "\033[94m",  # Blue
            "llm_reasoning": "\033[93m",  # Yellow
            "action": "\033[92m",  # Green
            "error": "\033[91m",  # Red
            "reset": "\033[0m"
        }
        
        color = colors.get(step_type, colors["reset"])
        return f"{color}[{timestamp}] {step_type.upper()}: {details}{colors['reset']}"
    
    def _format_file_output(self, step_type: str, details: dict, timestamp: str) -> str:
        """Format step information for file logging"""
        # JSON-like structure for easy parsing
        import json
        return json.dumps({
            "timestamp": timestamp,
            "type": step_type,
            "details": details
        })
    
    def get_log_path(self) -> Path:
        """Return path to current log file"""
        return self.log_file if self.enabled else None
```

### 3.1 Local Storage Manager

```python
class StorageManager:
    """Manages local storage for Browser Copilot"""
    
    def __init__(self):
        self.base_dir = Path.home() / ".browser_copilot"
        self._ensure_directory_structure()
    
    def _ensure_directory_structure(self):
        """Create necessary directories"""
        directories = [
            self.base_dir,
            self.base_dir / "logs",
            self.base_dir / "settings",
            self.base_dir / "memory",
            self.base_dir / "reports",
            self.base_dir / "screenshots"
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_logs_dir(self) -> Path:
        """Get logs directory"""
        return self.base_dir / "logs"
    
    def get_settings_file(self) -> Path:
        """Get settings file path"""
        return self.base_dir / "settings" / "config.json"
    
    def save_setting(self, key: str, value: any):
        """Save a setting to local storage"""
        settings_file = self.get_settings_file()
        settings = {}
        
        if settings_file.exists():
            settings = json.loads(settings_file.read_text())
        
        settings[key] = value
        settings_file.write_text(json.dumps(settings, indent=2))
    
    def get_setting(self, key: str, default=None):
        """Get a setting from local storage"""
        settings_file = self.get_settings_file()
        if not settings_file.exists():
            return default
        
        settings = json.loads(settings_file.read_text())
        return settings.get(key, default)
    
    def cleanup_old_logs(self, days: int = 7):
        """Remove logs older than specified days"""
        cutoff_time = datetime.now() - timedelta(days=days)
        logs_dir = self.get_logs_dir()
        
        for log_file in logs_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_time.timestamp():
                log_file.unlink()
```

**Integration with LangChain Callbacks**:
```python
class BrowserPilotCallback(BaseCallbackHandler):
    """Custom callback for verbose logging and screenshot control"""
    
    def __init__(self, logger: VerboseLogger, screenshots_enabled: bool = True):
        self.logger = logger
        self.screenshots_enabled = screenshots_enabled
    
    def on_tool_start(self, serialized: dict, input_str: str, **kwargs):
        """Log when MCP tool is called"""
        tool_name = serialized.get("name", "")
        
        # Filter automatic screenshots if disabled
        if tool_name == "browser_take_screenshot" and not self.screenshots_enabled:
            # Check if this is an explicit user request vs automatic
            if "automatic" in input_str.lower() or "step" in input_str.lower():
                self.logger.log_step("screenshot_skipped", {
                    "reason": "Automatic screenshots disabled",
                    "tool": tool_name
                })
                # Return early to skip the screenshot
                return
        
        self.logger.log_step("tool_start", {
            "tool": tool_name,
            "input": input_str
        })
    
    def on_llm_start(self, serialized: dict, prompts: list, **kwargs):
        """Log LLM reasoning"""
        self.logger.log_step("llm_reasoning", {
            "prompts": prompts
        })
```

### 4. Enhanced Core Module (`core.py`)

**Modified BrowserPilot Class**:
```python
class BrowserPilot:
    def __init__(self, provider: str, model: str, verbose_logger: VerboseLogger = None,
                 storage_manager: StorageManager = None, screenshots_enabled: bool = True):
        # Existing initialization
        self.verbose_logger = verbose_logger
        self.storage_manager = storage_manager or StorageManager()
        self.screenshots_enabled = self._resolve_screenshot_setting(screenshots_enabled)
        
        # Add verbose callback if enabled
        callbacks = [self.telemetry]
        if verbose_logger and verbose_logger.enabled:
            callbacks.append(BrowserPilotCallback(verbose_logger))
        
        self.llm = self.registry.get_llm(
            provider_name=provider,
            model_alias=model,
            callbacks=callbacks
        )
    
    def _resolve_screenshot_setting(self, cli_value: bool) -> bool:
        """Resolve screenshot setting from CLI, env, or settings file"""
        # Priority: CLI flag > Environment variable > Settings file > Default (True)
        if not cli_value:
            return False
        
        # Check environment variable
        env_value = os.environ.get('BROWSER_PILOT_SCREENSHOTS', '').lower()
        if env_value in ('false', '0', 'no'):
            return False
        
        # Check settings file
        if self.storage_manager:
            return self.storage_manager.get_setting('screenshots_enabled', True)
        
        return True
    
    def _build_prompt(self, test_suite_content: str, system_prompt: str = None) -> str:
        """Build execution prompt with optional custom system prompt"""
        base_prompt = test_suite_content.strip()
        
        # Add screenshot control instructions
        if not self.screenshots_enabled:
            base_prompt += "\n\nIMPORTANT: Automatic screenshots are DISABLED. Only take screenshots when explicitly requested in the test steps."
        
        if system_prompt:
            return f"{system_prompt}\n\n{base_prompt}"
        return self._default_prompt(base_prompt)
```

**Streaming Support with Token Optimization**:
```python
async def run_test_suite(self, test_suite_content: str, **kwargs):
    """Execute test suite with streaming support and token optimization"""
    # ... existing setup ...
    
    # Apply token optimization if enabled
    if self.token_optimizer:
        original_prompt = prompt
        prompt = self.token_optimizer.optimize_prompt(prompt, {"test_id": self.test_id})
        
        # Track optimization metrics
        savings = self.token_optimizer.calculate_savings(original_prompt, prompt)
        self.tokens_saved = savings["tokens_saved"]
        self.optimization_level = self.token_optimizer.level
    
    # Use astream_events for detailed streaming
    async for event in agent.astream_events({"messages": prompt}):
        if self.verbose_logger:
            self._process_stream_event(event)
        
        # Accumulate results
        # ... rest of implementation ...
    
    # Extract comprehensive telemetry
    token_usage = self._extract_telemetry_data()
    
    # Calculate cost savings if optimization was applied
    if self.token_optimizer and self.tokens_saved > 0:
        # Estimate cost saved based on model pricing
        avg_cost_per_token = token_usage["estimated_cost"] / token_usage["total_tokens"]
        self.cost_saved = self.tokens_saved * avg_cost_per_token

def _extract_telemetry_data(self) -> Dict[str, Any]:
    """Extract comprehensive token usage and cost data from ModelForge telemetry"""
    if not self.telemetry or not hasattr(self.telemetry, 'metrics'):
        return {}
    
    metrics = self.telemetry.metrics
    
    # ModelForge provides detailed cost breakdown
    return {
        "total_tokens": metrics.total_tokens,
        "prompt_tokens": metrics.prompt_tokens,
        "completion_tokens": metrics.completion_tokens,
        "estimated_cost": metrics.estimated_cost,
        "cost_details": {
            "prompt_cost": metrics.prompt_cost,
            "completion_cost": metrics.completion_cost,
            "currency": getattr(metrics, 'currency', 'USD'),
            "pricing_model": getattr(metrics, 'pricing_model', 'standard')
        },
        "optimization_metrics": {
            "tokens_saved": getattr(self, 'tokens_saved', 0),
            "cost_saved": getattr(self, 'cost_saved', 0),
            "optimization_level": getattr(self, 'optimization_level', 'none')
        }
    }
```

### 5. Enhanced Reporter Module (`reporter.py`)

**Extended Result Structure**:
```python
def create_enhanced_report(result: dict, storage_manager: StorageManager = None) -> str:
    """Create report with timing and token usage"""
    report_sections = [
        _create_header(result),
        _create_execution_summary(result),
        _create_test_results(result),
        _create_token_usage_section(result),
        _create_timing_section(result),
        _create_recommendations(result)
    ]
    return "\n\n".join(report_sections)

def _create_timing_section(result: dict) -> str:
    """Format timing information"""
    return f"""## Execution Timeline
- Start: {result['start_time']}
- End: {result['end_time']}
- Duration: {result['duration_seconds']:.2f} seconds
- Steps: {result['steps_executed']}
- Average step time: {result['duration_seconds'] / result['steps_executed']:.2f}s"""

def _create_token_usage_section(result: dict) -> str:
    """Format token usage and cost from telemetry"""
    usage = result.get('token_usage', {})
    
    # ModelForge provides detailed cost breakdown
    cost_details = usage.get('cost_details', {})
    prompt_cost = cost_details.get('prompt_cost', 0)
    completion_cost = cost_details.get('completion_cost', 0)
    total_cost = usage.get('estimated_cost', 0)
    
    # Calculate cost per token for analysis
    prompt_tokens = usage.get('prompt_tokens', 0)
    completion_tokens = usage.get('completion_tokens', 0)
    
    return f"""## Token Usage & Cost Analysis
### Token Counts
- Prompt tokens: {prompt_tokens:,}
- Completion tokens: {completion_tokens:,}
- Total tokens: {usage.get('total_tokens', 0):,}

### Cost Breakdown
- Prompt cost: ${prompt_cost:.4f} (${prompt_cost/prompt_tokens*1000:.4f}/1K tokens)
- Completion cost: ${completion_cost:.4f} (${completion_cost/completion_tokens*1000:.4f}/1K tokens)
- **Total cost: ${total_cost:.4f}**

### Provider & Model
- Provider: {result.get('provider', 'Unknown')}
- Model: {result.get('model', 'Unknown')}"""
```

### 6. Test Suite Enhancement Module

```python
class TestSuiteEnhancer:
    """Generates LLM-optimized test suites"""
    
    def __init__(self, llm):
        self.llm = llm
        self.enhancement_prompt = """
        Analyze this test suite and rewrite it to be more explicit and reliable for AI agents:
        - Add specific element identifiers (CSS selectors, text content)
        - Make success criteria explicit
        - Add wait conditions where needed
        - Preserve original functionality
        
        Original test suite:
        {test_suite}
        
        Enhanced test suite:
        """
    
    async def enhance(self, test_suite_content: str) -> str:
        """Generate enhanced version of test suite"""
        prompt = self.enhancement_prompt.format(test_suite=test_suite_content)
        response = await self.llm.ainvoke(prompt)
        return response.content
```

### 7. Token Optimization Module

```python
class TokenOptimizer:
    """Optimizes token usage for cost reduction"""
    
    def __init__(self, optimization_level: str = "balanced"):
        self.level = optimization_level  # minimal, balanced, aggressive
        self.prompt_cache = {}
        self.common_patterns = self._load_common_patterns()
    
    def optimize_prompt(self, prompt: str, test_context: dict) -> str:
        """Optimize prompt for reduced token usage"""
        if self.level == "minimal":
            return prompt
        
        optimized = prompt
        
        # Strategy 1: Remove redundant instructions
        optimized = self._remove_redundant_instructions(optimized)
        
        # Strategy 2: Compress verbose descriptions
        if self.level == "aggressive":
            optimized = self._compress_descriptions(optimized)
        
        # Strategy 3: Use references for repeated content
        optimized = self._use_references(optimized, test_context)
        
        # Strategy 4: Truncate verbose outputs in context
        optimized = self._truncate_context(optimized)
        
        return optimized
    
    def _remove_redundant_instructions(self, prompt: str) -> str:
        """Remove instructions that LLM already knows"""
        redundant_patterns = [
            "Please make sure to",
            "It is important that you",
            "Remember to always",
            # More patterns based on research
        ]
        
        for pattern in redundant_patterns:
            prompt = prompt.replace(pattern, "")
        
        return prompt.strip()
    
    def _compress_descriptions(self, prompt: str) -> str:
        """Compress verbose descriptions while maintaining clarity"""
        # Use shorter synonyms
        replacements = {
            "navigate to the URL": "go to",
            "click on the button": "click",
            "enter the text": "type",
            "verify that": "check",
        }
        
        for long_form, short_form in replacements.items():
            prompt = prompt.replace(long_form, short_form)
        
        return prompt
    
    def _use_references(self, prompt: str, context: dict) -> str:
        """Replace repeated content with references"""
        # Cache common elements
        if "common_elements" in context:
            for idx, element in enumerate(context["common_elements"]):
                reference = f"[E{idx}]"
                prompt = prompt.replace(element, reference)
        
        return prompt
    
    def _truncate_context(self, prompt: str, max_context_lines: int = 50) -> str:
        """Truncate verbose context like page states"""
        lines = prompt.split('\n')
        
        # Find and truncate large context blocks
        in_context_block = False
        truncated_lines = []
        context_lines = 0
        
        for line in lines:
            if "Page State:" in line or "Context:" in line:
                in_context_block = True
                context_lines = 0
            
            if in_context_block:
                context_lines += 1
                if context_lines > max_context_lines:
                    if context_lines == max_context_lines + 1:
                        truncated_lines.append("... [context truncated for token optimization]")
                    continue
            
            truncated_lines.append(line)
        
        return '\n'.join(truncated_lines)
    
    def calculate_savings(self, original: str, optimized: str) -> dict:
        """Calculate token and cost savings"""
        # Rough token estimation (actual would use tiktoken)
        original_tokens = len(original.split()) * 1.3
        optimized_tokens = len(optimized.split()) * 1.3
        
        reduction_percent = (1 - optimized_tokens / original_tokens) * 100
        
        return {
            "original_tokens": int(original_tokens),
            "optimized_tokens": int(optimized_tokens),
            "reduction_percent": reduction_percent,
            "tokens_saved": int(original_tokens - optimized_tokens)
        }
```

### 8. Input/Output Handlers

```python
class InputHandler:
    """Handles test suite input from file or stdin"""
    
    @staticmethod
    def read_test_suite(source: str) -> str:
        """Read test suite from file path or stdin"""
        if source == "-" or not source:
            # Read from stdin
            return sys.stdin.read()
        else:
            # Read from file
            return Path(source).read_text()

class OutputHandler:
    """Handles report output to console or file"""
    
    @staticmethod
    def write_report(report: str, destination: str = None):
        """Write report to specified destination"""
        if not destination:
            # Console output
            print(report)
        elif Path(destination).suffix:
            # File path provided
            Path(destination).write_text(report)
        else:
            # Directory provided, generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = Path(destination) / f"report_{timestamp}.md"
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_text(report)
```

## Data Flow

### Standard Execution Flow

1. CLI validates arguments and reads configuration
2. ConfigManager checks ModelForge defaults if needed
3. StorageManager initializes local storage structure
4. Authentication check/trigger if required
5. InputHandler reads test suite
6. BrowserPilot initialized with verbose logger
7. Test execution with streaming callbacks
   - Console output for immediate feedback
   - Detailed logs saved to ~/.browser_copilot/logs/
8. EnhancedReporter generates comprehensive report
9. OutputHandler writes to specified destination
10. Optional: Save report copy to ~/.browser_copilot/reports/

### Enhanced Test Suite Flow

1. Read original test suite
2. Initialize TestSuiteEnhancer with LLM
3. Generate enhanced version
4. Save to output destination
5. Exit without execution

## Integration Points

### LangChain Streaming Integration

Based on the Context7 documentation, we'll use:
- `astream_events` for detailed step visibility
- Custom callbacks for verbose logging
- Proper callback propagation in tool calls

```python
# Ensure callbacks propagate through tool calls
async for event in agent.astream_events(
    {"messages": prompt},
    config={"callbacks": [BrowserPilotCallback(verbose_logger)]}
):
    # Process streaming events
```

### ModelForge Integration

```python
# Check for default configuration
try:
    config = registry.get_default_config()
    provider = args.provider or config.provider
    model = args.model or config.model
except ConfigNotFoundError:
    if not args.provider or not args.model:
        raise ValueError("No ModelForge config found. Specify --provider and --model")
```

## Error Handling

### Authentication Errors
- Clear messages about authentication requirements
- Automatic triggering of device flow
- Timeout handling for authentication

### Input Validation
- Validate test suite format
- Check file permissions
- Validate browser selection

### Streaming Errors
- Graceful degradation if streaming fails
- Fallback to non-verbose mode
- Capture errors in report

## Performance Considerations

### Verbose Mode Overhead
- Use Python's logging levels for efficiency
- Buffer output to reduce I/O calls
- Conditional processing based on verbosity

### Memory Management
- Stream processing instead of accumulation where possible
- Limit stored event history
- Clean up resources after execution

## Security Considerations

### Prompt Injection Prevention
- Validate custom prompts for malicious patterns
- Escape user input in prompts
- Limit prompt size

### Sensitive Data Protection
- Filter common patterns (API keys, passwords)
- Sanitize verbose output
- Secure storage of authentication tokens

## Testing Strategy

### Unit Tests
- Test each new component in isolation
- Mock ModelForge and LangChain dependencies
- Verify error handling paths

### Integration Tests
- Test CLI argument combinations
- Verify ModelForge integration
- Test streaming callback flow

### End-to-End Tests
- Test with real browser automation
- Verify report generation
- Test authentication flows

## Migration Plan

1. Implement components incrementally
2. Maintain backward compatibility
3. Add feature flags for gradual rollout
4. Update documentation with examples
5. Deprecation warnings for old behavior

## Future Considerations

- Plugin architecture for custom reporters
- WebSocket support for real-time monitoring
- Integration with test management systems
- Multi-language test suite support