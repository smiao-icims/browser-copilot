"""
Core browser automation engine for Browser Pilot

This module contains the main BrowserPilot class that orchestrates
AI-powered browser test automation.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from modelforge.registry import ModelForgeRegistry
from modelforge.telemetry import TelemetryCallback
from modelforge.exceptions import ProviderError, ModelNotFoundError, ConfigurationError

from .config_manager import ConfigManager
from .io_handlers import StreamHandler
from .token_optimizer import TokenOptimizer, OptimizationLevel
from .verbose_logger import VerboseLogger, LangChainVerboseCallback


class BrowserPilot:
    """AI-powered browser test automation engine"""
    
    def __init__(
        self, 
        provider: str, 
        model: str,
        system_prompt: Optional[str] = None,
        config: Optional[ConfigManager] = None,
        stream: Optional[StreamHandler] = None
    ):
        """
        Initialize BrowserPilot with specified LLM provider and model
        
        Args:
            provider: LLM provider name (e.g., 'github_copilot', 'openai')
            model: Model name (e.g., 'gpt-4o', 'claude-3-opus')
            system_prompt: Optional custom system prompt
            config: Optional ConfigManager instance
            stream: Optional StreamHandler for output
        """
        self.provider = provider
        self.model = model
        self.system_prompt = system_prompt
        self.config = config or ConfigManager()
        self.stream = stream or StreamHandler()
        # Initialize ModelForge registry
        self.registry = ModelForgeRegistry()
        
        # Add telemetry callback for token tracking
        self.telemetry = TelemetryCallback(provider=provider, model=model)
        
        # Configure logging based on verbose setting
        if not self.config.get("verbose", False):
            # Suppress modelforge logs unless in verbose mode
            logging.getLogger('modelforge').setLevel(logging.ERROR)
            logging.getLogger('modelforge.modelforge').setLevel(logging.ERROR)
        
        # Initialize verbose logger if enabled
        self.verbose_logger = None
        self.langchain_callback = None
        if self.config.get("verbose", False):
            self.verbose_logger = VerboseLogger(
                storage_manager=self.config.storage,
                console_enabled=True,
                file_enabled=True
            )
            self.langchain_callback = LangChainVerboseCallback(self.verbose_logger)
            self.stream.write("Verbose logging enabled", "debug")
        
        # Initialize token optimizer if enabled
        self.token_optimizer = None
        if self.config.get("token_optimization", True):
            optimization_level = self._get_optimization_level()
            self.token_optimizer = TokenOptimizer(optimization_level)
            self.stream.write(f"Token optimization enabled: {optimization_level.value}", "debug")
        
        # Get model configuration
        model_config = self.config.get_model_config()
        
        # Build callbacks list
        callbacks = [self.telemetry]
        if self.langchain_callback:
            callbacks.append(self.langchain_callback)
        
        # Initialize LLM with telemetry and configuration using enhanced mode (v2.2.1+)
        try:
            self.llm = self.registry.get_llm(
                provider_name=provider,
                model_alias=model,
                callbacks=callbacks,
                enhanced=True  # Enable enhanced mode for model metadata access
            )
            self.stream.write("Enhanced mode enabled with full compatibility", "debug")
            # Set temperature and max_tokens on the model if supported
            if hasattr(self.llm, 'temperature') and model_config.get("temperature") is not None:
                self.llm.temperature = model_config.get("temperature")
            if hasattr(self.llm, 'max_tokens') and model_config.get("max_tokens") is not None:
                self.llm.max_tokens = model_config.get("max_tokens")
        except (ProviderError, ModelNotFoundError, ConfigurationError) as e:
            raise RuntimeError(f"Failed to load LLM: {e}")
    
    async def run_test_suite(
        self, 
        test_suite_content: str,
        browser: str = "chromium",
        headless: bool = False,
        verbose: bool = False,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        timeout: Optional[int] = None,
        enable_screenshots: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a test suite using browser automation
        
        Args:
            test_suite_content: Markdown content of the test suite
            browser: Browser to use ('chromium', 'firefox', 'webkit')
            headless: Whether to run in headless mode
            verbose: Enable verbose output
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height
            timeout: Execution timeout in seconds
            enable_screenshots: Whether to enable screenshot capture
            **kwargs: Additional keyword arguments
            
        Returns:
            Dictionary containing test results, including:
            - success: Whether the test passed
            - duration_seconds: Execution time
            - steps_executed: Number of steps taken
            - report: Markdown test report
            - token_usage: Token consumption metrics
            - error: Error message if failed
        """
        
        # Validate browser choice
        valid_browsers = self._get_valid_browsers()
        if browser not in valid_browsers:
            raise ValueError(
                f"Invalid browser '{browser}'. Must be one of: {', '.join(valid_browsers)}"
            )
        
        # Map browser aliases
        browser_map = {
            "chrome": "chromium",
            "edge": "msedge",
            "safari": "webkit"
        }
        actual_browser = browser_map.get(browser, browser)
        
        # Extract test name early for session directory creation
        test_name = self._extract_test_name(test_suite_content)
        
        # Build MCP server arguments
        viewport_size = f"{viewport_width},{viewport_height}"
        browser_args = [
            "@playwright/mcp",
            "--browser", actual_browser,
            "--viewport-size", viewport_size
        ]
        
        if headless:
            browser_args.append("--headless")
            
        if not enable_screenshots:
            browser_args.append("--no-screenshots")
        
        # Add isolated mode by default unless explicitly disabled
        # This ensures each test run starts with a clean browser state
        if not kwargs.get("no_isolated", False):
            browser_args.append("--isolated")
        
        # Add device emulation if specified
        if kwargs.get("device"):
            browser_args.extend(["--device", kwargs["device"]])
            
        # Add user agent if specified
        if kwargs.get("user_agent"):
            browser_args.extend(["--user-agent", kwargs["user_agent"]])
            
        # Add proxy settings if specified
        if kwargs.get("proxy_server"):
            browser_args.extend(["--proxy-server", kwargs["proxy_server"]])
        if kwargs.get("proxy_bypass"):
            browser_args.extend(["--proxy-bypass", kwargs["proxy_bypass"]])
            
        # Add security and debugging options
        if kwargs.get("ignore_https_errors"):
            browser_args.append("--ignore-https-errors")
        if kwargs.get("block_service_workers"):
            browser_args.append("--block-service-workers")
        if kwargs.get("save_trace"):
            browser_args.append("--save-trace")
        if kwargs.get("save_session"):
            browser_args.append("--save-session")
            
        # Add origin restrictions if specified
        if kwargs.get("allowed_origins"):
            browser_args.extend(["--allowed-origins", kwargs["allowed_origins"]])
        if kwargs.get("blocked_origins"):
            browser_args.extend(["--blocked-origins", kwargs["blocked_origins"]])
            
        # Set output directory for traces/sessions if saving
        if kwargs.get("save_trace") or kwargs.get("save_session"):
            # Create session-specific output directory
            test_name_normalized = self._normalize_test_name(test_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_dir = self.config.storage.base_dir / "sessions" / f"{test_name_normalized}_{timestamp}"
            session_dir.mkdir(parents=True, exist_ok=True)
            browser_args.extend(["--output-dir", str(session_dir)])
            # Store session directory for later reference
            kwargs["_session_dir"] = session_dir
        
        server_params = StdioServerParameters(
            command="npx",
            args=browser_args
        )
        
        # Test name already extracted above
        
        # Log test start if verbose
        if self.verbose_logger:
            self.verbose_logger.log_test_start(test_name, {
                "provider": self.provider,
                "model": self.model,
                "browser": browser,
                "headless": headless,
                "viewport": f"{viewport_width}x{viewport_height}",
                "optimization": self.config.get("compression_level", "medium")
            })
        
        # Track execution
        start_time = datetime.now(timezone.utc)
        result = {
            "success": False,
            "provider": self.provider,
            "model": self.model,
            "browser": browser,
            "headless": headless,
            "viewport_size": viewport_size,
            "test_name": test_name,
            "execution_time": {
                "start": start_time.isoformat(),
                "timezone": "UTC"
            },
            "environment": {
                "token_optimization": self.token_optimizer is not None,
                "compression_level": self.config.get("compression_level", "medium")
            }
        }
        
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = await load_mcp_tools(session)
                    
                    self.stream.write(f"Loaded {len(tools)} MCP tools", "debug")
                    
                    # Create ReAct agent with browser tools
                    agent = create_react_agent(self.llm, tools)
                    agent = agent.with_config(recursion_limit=100)
                    
                    # Build execution prompt
                    prompt = self._build_prompt(test_suite_content)
                    
                    # Estimate initial prompt size and warn if approaching limit
                    initial_tokens = self._estimate_tokens(str(prompt))
                    context_limit = getattr(self.llm, 'context_length', 128000)  # Default to 128k
                    
                    if initial_tokens > context_limit * 0.5:
                        self.stream.write(f"\n⚠️  Large test detected: ~{initial_tokens:,} initial tokens", "warning")
                        self.stream.write(f"Context limit: {context_limit:,} tokens", "info")
                        self.stream.write("Consider using --enhance-test to optimize the test suite", "info")
                    
                    # Execute test suite
                    steps = []
                    final_response = None
                    
                    try:
                        async for chunk in agent.astream({"messages": prompt}):
                            steps.append(chunk)
                            if len(steps) % 5 == 0:
                                self.stream.write(f"Progress: {len(steps)} steps...", "debug")
                                
                                # In verbose mode, show token usage progress
                                if self.stream.verbose and hasattr(self.telemetry, 'metrics') and self.telemetry.metrics:
                                    metrics = self.telemetry.metrics
                                    current_tokens = 0
                                    
                                    # Try to get token count from different possible attributes
                                    if hasattr(metrics, 'token_usage') and metrics.token_usage:
                                        # Check if token_usage is a dict or object
                                        if isinstance(metrics.token_usage, dict):
                                            current_tokens = metrics.token_usage.get('total_tokens', 0)
                                        else:
                                            current_tokens = getattr(metrics.token_usage, 'total_tokens', 0)
                                    elif hasattr(metrics, 'total_tokens'):
                                        current_tokens = metrics.total_tokens
                                    elif hasattr(metrics, 'prompt_tokens'):
                                        # Fallback to summing prompt + completion tokens
                                        current_tokens = getattr(metrics, 'prompt_tokens', 0) + getattr(metrics, 'completion_tokens', 0)
                                    
                                    if current_tokens > 0:
                                        usage_pct = (current_tokens / context_limit * 100) if context_limit > 0 else 0
                                        if usage_pct > 80:
                                            self.stream.write(f"⚠️  Context usage: {current_tokens:,}/{context_limit:,} ({usage_pct:.1f}%)", "warning")
                                        elif usage_pct > 60:
                                            self.stream.write(f"Context usage: {current_tokens:,}/{context_limit:,} ({usage_pct:.1f}%)", "info")
                            
                            # Extract final response from agent
                            if 'agent' in chunk and 'messages' in chunk['agent']:
                                for msg in chunk['agent']['messages']:
                                    if hasattr(msg, 'content') and msg.content:
                                        final_response = msg
                    except ValueError as e:
                        error_msg = str(e)
                        # Check for context length exceeded error
                        if "model_max_prompt_tokens_exceeded" in error_msg or "exceeds the limit" in error_msg:
                            # Extract token counts from error message
                            import re
                            token_match = re.search(r'token count of (\d+) exceeds the limit of (\d+)', error_msg)
                            if token_match:
                                used_tokens = int(token_match.group(1))
                                max_tokens = int(token_match.group(2))
                                
                                self.stream.write(f"\n{'='*60}", "error")
                                self.stream.write(f"❌ CONTEXT LENGTH EXCEEDED", "error")
                                self.stream.write(f"{'='*60}", "error")
                                self.stream.write(f"Used: {used_tokens:,} tokens", "error")
                                self.stream.write(f"Limit: {max_tokens:,} tokens", "error")
                                self.stream.write(f"Exceeded by: {used_tokens - max_tokens:,} tokens ({(used_tokens/max_tokens - 1)*100:.1f}%)", "error")
                                
                                self.stream.write("\n📋 Suggestions to reduce context:", "warning")
                                self.stream.write("1. Use --enhance-test to optimize the test suite", "info")
                                self.stream.write("   This can reduce 30-50% of tokens through concise rewriting", "info")
                                self.stream.write("   Example: browser-pilot test.md --enhance-test --save-enhanced optimized.md", "info")
                                self.stream.write("\n2. Break the test into smaller sections", "info")
                                self.stream.write("   Split complex tests into multiple smaller test files", "info")
                                self.stream.write("\n3. Run without --verbose flag", "info")
                                self.stream.write("   Verbose mode adds significant token overhead", "info")
                                self.stream.write("\n4. Use a model with larger context window", "info")
                                self.stream.write("   - gpt-4o-128k (128,000 tokens)", "info")
                                self.stream.write("   - gpt-4-turbo (128,000 tokens)", "info")
                                self.stream.write("   - claude-3-opus (200,000 tokens)", "info")
                                
                                result["error"] = f"Context length exceeded: {used_tokens:,}/{max_tokens:,} tokens"
                                result["error_type"] = "context_length_exceeded"
                                result["token_usage"] = {
                                    "total_tokens": used_tokens,
                                    "prompt_tokens": used_tokens,
                                    "completion_tokens": 0,
                                    "estimated_cost": 0,
                                    "context_length": used_tokens,
                                    "max_context_length": max_tokens,
                                    "context_usage_percentage": (used_tokens / max_tokens * 100) if max_tokens > 0 else 100
                                }
                            else:
                                result["error"] = f"Context length exceeded: {error_msg}"
                                result["error_type"] = "context_length_exceeded"
                            
                            # Return early with partial results
                            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                            result["duration_seconds"] = duration
                            result["execution_time"]["end"] = datetime.now(timezone.utc).isoformat()
                            result["steps"] = self._extract_steps(steps)
                            result["test_report"] = "Test failed due to context length limit"
                            return result
                        else:
                            # Other ValueError - re-raise
                            raise
                    
                    # Process execution results
                    duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                    
                    report_content = ""
                    if final_response and hasattr(final_response, 'content'):
                        report_content = str(final_response.content)
                    
                    # Extract token usage from telemetry
                    token_usage = self._get_token_usage()
                    
                    end_time = datetime.now(timezone.utc)
                    result.update({
                        "success": self._check_success(report_content),
                        "duration": duration,
                        "duration_seconds": duration,  # Backward compatibility
                        "steps_executed": len(steps),
                        "steps": self._extract_steps(steps),
                        "report": report_content,
                        "execution_time": {
                            "start": start_time.isoformat(),
                            "end": end_time.isoformat(),
                            "duration_seconds": duration,
                            "timezone": "UTC"
                        },
                        "token_usage": token_usage,
                        "metrics": {
                            "total_steps": len(steps),
                            "execution_time_ms": duration * 1000,
                            "avg_step_time_ms": (duration * 1000) / len(steps) if steps else 0
                        }
                    })
                    
                    # Log test completion if verbose
                    if self.verbose_logger:
                        self.verbose_logger.log_test_complete(
                            result["success"],
                            duration,
                            f"{len(steps)} steps executed"
                        )
                        
                        # Add verbose log info to result
                        result["verbose_log"] = {
                            "log_file": str(self.verbose_logger.get_log_file_path()),
                            "summary": self.verbose_logger.get_execution_summary()
                        }
                    
        except Exception as e:
            result.update({
                "error": str(e),
                "duration_seconds": (datetime.now(timezone.utc) - start_time).total_seconds()
            })
            if verbose:
                import traceback
                traceback.print_exc()
        
        return result
    
    def _build_prompt(self, test_suite_content: str) -> str:
        """Build the test execution prompt with instructions"""
        # Use custom system prompt if provided
        if self.system_prompt:
            base_prompt = self.system_prompt
        else:
            base_prompt = ""
        
        # Combine prompts
        full_prompt = f"""{base_prompt}{test_suite_content.strip()}

IMPORTANT INSTRUCTIONS:
1. Execute each test step methodically using the browser automation tools
2. Use browser_snapshot before interacting with elements
3. Take screenshots at key points using browser_take_screenshot
4. Handle errors gracefully and continue if possible
5. Wait for page loads after navigation

At the end, generate a comprehensive test report in markdown format:

# Test Execution Report

## Summary
- Overall Status: PASSED or FAILED
- Duration: X seconds
- Browser: {self.browser if hasattr(self, 'browser') else 'Unknown'}

## Test Results

### [Test Name]
**Status:** PASSED/FAILED

**Steps Executed:**
1. ✅ [Step description] - [What happened]
2. ❌ [Step description] - Error: [What went wrong]

**Screenshots Taken:**
- [List of screenshots with descriptions]

## Issues Encountered
[Any errors or unexpected behaviors]

## Recommendations
[Suggestions for improvement]

Execute the test now."""
        
        # Apply token optimization if enabled
        if self.token_optimizer:
            optimized_prompt = self.token_optimizer.optimize_prompt(full_prompt)
            
            # Log optimization metrics
            metrics = self.token_optimizer.get_metrics()
            if metrics['reduction_percentage'] > 0:
                self.stream.write(
                    f"Prompt optimized: {metrics['reduction_percentage']:.1f}% reduction",
                    "debug"
                )
            
            return optimized_prompt
        
        return full_prompt
    
    def _check_success(self, report_content: str) -> bool:
        """
        Determine if test passed based on report content
        
        Uses simple heuristics to check for success indicators
        in the generated report.
        """
        if not report_content:
            return False
            
        lower_content = report_content.lower()
        
        # Check various success patterns
        success_patterns = [
            "overall status:** passed",
            "overall status: passed",
            "status:** passed",
            "status: passed",
            "all tests passed",
            "test passed successfully"
        ]
        
        # Must have test execution report
        has_report = "test execution report" in lower_content
        
        # Check for any success pattern
        has_success = any(pattern in lower_content for pattern in success_patterns)
        
        # Check for explicit failure
        has_failure = any(fail in lower_content for fail in [
            "overall status:** failed",
            "overall status: failed",
            "test failed"
        ])
        
        return has_report and has_success and not has_failure
    
    def _get_token_usage(self) -> Dict[str, Any]:
        """Extract token usage metrics from telemetry"""
        if not self.telemetry:
            return {}
        
        try:
            # Try to get metrics from telemetry
            if hasattr(self.telemetry, 'metrics') and self.telemetry.metrics:
                metrics = self.telemetry.metrics
                usage = {}
                
                # Extract token usage if available
                if hasattr(metrics, 'token_usage') and metrics.token_usage:
                    token_usage = metrics.token_usage
                    # Handle both dict and object formats
                    if isinstance(token_usage, dict):
                        usage.update({
                            "total_tokens": token_usage.get('total_tokens', 0),
                            "prompt_tokens": token_usage.get('prompt_tokens', 0),
                            "completion_tokens": token_usage.get('completion_tokens', 0),
                        })
                    else:
                        usage.update({
                            "total_tokens": getattr(token_usage, 'total_tokens', 0),
                            "prompt_tokens": getattr(token_usage, 'prompt_tokens', 0),
                            "completion_tokens": getattr(token_usage, 'completion_tokens', 0),
                        })
                
                # Extract cost if available
                if hasattr(metrics, 'estimated_cost'):
                    usage["estimated_cost"] = metrics.estimated_cost
                # Enhanced LLM cost estimation (if available and no cost from telemetry)
                elif hasattr(self.llm, 'estimate_cost') and usage.get("prompt_tokens") and usage.get("completion_tokens"):
                    try:
                        enhanced_cost = self.llm.estimate_cost(usage["prompt_tokens"], usage["completion_tokens"])
                        usage["estimated_cost"] = enhanced_cost
                        usage["cost_source"] = "enhanced_llm"
                    except Exception:
                        pass  # Fall back to telemetry cost if enhanced estimation fails
                
                # Add context length information if we have prompt tokens
                if usage.get("prompt_tokens", 0) > 0:
                    context_length = usage["prompt_tokens"]
                    usage["context_length"] = context_length
                    
                    # Get context limit from enhanced model-forge LLM (v2.2.1+)
                    max_context = None
                    
                    # First priority: Use context_length property from enhanced LLM
                    if hasattr(self.llm, 'context_length') and self.llm.context_length:
                        max_context = self.llm.context_length
                    
                    # Second priority: Check model_info from enhanced LLM
                    elif hasattr(self.llm, 'model_info') and isinstance(self.llm.model_info, dict):
                        limit_info = self.llm.model_info.get('limit', {})
                        if 'context' in limit_info:
                            max_context = limit_info['context']
                    
                    # Fallback to hardcoded limits only if enhanced features aren't available
                    if not max_context:
                        model_limits = self._get_model_context_limits()
                        model_key = f"{self.provider}_{self.model}".lower().replace("-", "_").replace(".", "_")
                        
                        if model_key in model_limits:
                            max_context = model_limits[model_key]
                        else:
                            # Try to match by model name only
                            for key, limit in model_limits.items():
                                if self.model.lower().replace("-", "_").replace(".", "_") in key:
                                    max_context = limit
                                    break
                    
                    # Set the context usage info if we found a limit
                    if max_context:
                        usage["max_context_length"] = max_context
                        usage["context_usage_percentage"] = round((context_length / max_context) * 100, 1)
                
                # Add optimization savings if available
                if self.token_optimizer:
                    opt_metrics = self.token_optimizer.get_metrics()
                    if opt_metrics['original_tokens'] > 0:
                        usage["optimization"] = {
                            "original_tokens": opt_metrics['original_tokens'],
                            "optimized_tokens": opt_metrics['optimized_tokens'],
                            "reduction_percentage": opt_metrics['reduction_percentage'],
                            "strategies_applied": opt_metrics['strategies_applied']
                        }
                        
                        # Estimate cost savings
                        if usage.get("estimated_cost"):
                            cost_per_token = usage["estimated_cost"] / usage["total_tokens"]
                            tokens_saved = opt_metrics['original_tokens'] - opt_metrics['optimized_tokens']
                            usage["optimization"]["estimated_savings"] = tokens_saved * cost_per_token
                
                return usage
                
            return {}
            
        except Exception:
            # If anything goes wrong, return empty metrics
            return {}
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        # Simple estimation: ~1.3 tokens per word for English
        # This matches the estimation used in test_enhancer.py
        words = len(str(text).split())
        return int(words * 1.3)
    
    def _extract_steps(self, steps: list) -> list:
        """Extract human-readable steps from agent execution"""
        extracted_steps = []
        
        for step in steps:
            if isinstance(step, dict):
                # Extract tool calls
                if 'tools' in step:
                    for tool_msg in step.get('tools', {}).get('messages', []):
                        if hasattr(tool_msg, 'name') and hasattr(tool_msg, 'content'):
                            content = str(tool_msg.content)
                            # Keep full content for reports - truncation will be handled by formatter
                            extracted_steps.append({
                                "type": "tool_call",
                                "name": tool_msg.name,
                                "content": content
                            })
                
                # Extract agent messages
                if 'agent' in step:
                    for agent_msg in step.get('agent', {}).get('messages', []):
                        if hasattr(agent_msg, 'content') and agent_msg.content:
                            content = str(agent_msg.content)
                            if len(content) > 50:  # Only include substantial messages
                                extracted_steps.append({
                                    "type": "agent_message",
                                    "content": content
                                })
        
        return extracted_steps
    
    def _get_optimization_level(self) -> OptimizationLevel:
        """
        Determine optimization level based on configuration
        
        Returns:
            OptimizationLevel enum value
        """
        compression_level = self.config.get("compression_level", "medium")
        
        level_map = {
            "none": OptimizationLevel.NONE,
            "low": OptimizationLevel.LOW,
            "medium": OptimizationLevel.MEDIUM,
            "high": OptimizationLevel.HIGH
        }
        
        return level_map.get(compression_level.lower(), OptimizationLevel.MEDIUM)
    
    def _get_valid_browsers(self) -> list:
        """
        Get list of valid browser choices
        
        Returns:
            List of valid browser names
        """
        # Playwright supported browsers + common aliases
        return ["chromium", "chrome", "firefox", "safari", "webkit", "edge"]
    
    def _extract_test_name(self, test_content: str) -> str:
        """
        Extract test name from test content
        
        Args:
            test_content: Test scenario content
            
        Returns:
            Test name
        """
        lines = test_content.strip().split('\n')
        
        # Look for markdown heading
        for line in lines:
            if line.startswith('#'):
                return line.strip('# ').strip()
        
        # Use first non-empty line
        for line in lines:
            if line.strip():
                # Truncate if too long
                name = line.strip()
                if len(name) > 50:
                    name = name[:47] + "..."
                return name
        
        return "Browser Test"
    
    def _get_model_context_limits(self) -> Dict[str, int]:
        """
        Get fallback context length limits for models when model-forge metadata is unavailable
        
        NOTE: This is now a fallback method. The primary source of context limits is 
        model-forge v2.2.0+ enhanced metadata via model_info.limit.context
        
        Returns:
            Dictionary mapping model identifiers to their context limits
        """
        # Fallback context limits (only used when model-forge metadata is unavailable)
        return {
            # Common fallback limits - model-forge should provide accurate data
            "github_copilot_gpt_4o": 128000,
            "openai_gpt_4o": 128000,
            "anthropic_claude_3_5_sonnet": 200000,
            "google_gemini_1_5_pro": 2000000,
        }
    
    def _normalize_test_name(self, test_name: str) -> str:
        """
        Normalize test name for use in file paths
        
        Args:
            test_name: Original test name
            
        Returns:
            Normalized test name safe for file paths
        """
        import re
        # Convert to lowercase and replace spaces with hyphens
        normalized = test_name.lower().replace(' ', '-')
        # Remove special characters, keep only alphanumeric and hyphens
        normalized = re.sub(r'[^a-z0-9-]', '', normalized)
        # Remove multiple consecutive hyphens
        normalized = re.sub(r'-+', '-', normalized)
        # Remove leading/trailing hyphens
        normalized = normalized.strip('-')
        # Ensure it's not empty
        if not normalized:
            normalized = 'browser-test'
        # Limit length
        if len(normalized) > 50:
            normalized = normalized[:50].rstrip('-')
        return normalized