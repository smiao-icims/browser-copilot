"""
Core browser automation engine for Browser Copilot

This module contains the main BrowserPilot class that orchestrates
AI-powered browser test automation.
"""

import logging
from datetime import UTC, datetime
from typing import Any, Optional
import uuid

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from modelforge.exceptions import ConfigurationError, ModelNotFoundError, ProviderError
from modelforge.registry import ModelForgeRegistry
from modelforge.telemetry import TelemetryCallback

from .agent import AgentFactory
from .config_manager import ConfigManager
from .io import StreamHandler
from .models.execution import ExecutionStep, ExecutionMetadata, ExecutionTiming
from .models.metrics import TokenMetrics, OptimizationSavings
from .models.results import BrowserTestResult
from .token_optimizer import OptimizationLevel, TokenOptimizer
from .verbose_logger import LangChainVerboseCallback, VerboseLogger


class BrowserPilot:
    """AI-powered browser test automation engine"""

    def __init__(
        self,
        provider: str,
        model: str,
        system_prompt: str | None = None,
        config: ConfigManager | None = None,
        stream: StreamHandler | None = None,
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
            logging.getLogger("modelforge").setLevel(logging.ERROR)
            logging.getLogger("modelforge.modelforge").setLevel(logging.ERROR)

        # Initialize verbose logger if enabled
        self.verbose_logger = None
        self.langchain_callback = None
        if self.config.get("verbose", False):
            self.verbose_logger = VerboseLogger(
                storage_manager=self.config.storage,
                console_enabled=True,
                file_enabled=True,
            )
            self.langchain_callback = LangChainVerboseCallback(self.verbose_logger)
            self.stream.write("Verbose logging enabled", "debug")

        # Initialize token optimizer if enabled
        self.token_optimizer = None
        if self.config.get("token_optimization", True):
            optimization_level = self._get_optimization_level()
            self.token_optimizer = TokenOptimizer(optimization_level)
            self.stream.write(
                f"Token optimization enabled: {optimization_level.value}", "debug"
            )

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
                enhanced=True,  # Enable enhanced mode for model metadata access
            )
            self.stream.write("Enhanced mode enabled with full compatibility", "debug")
            # Set temperature and max_tokens on the model if supported
            if (
                hasattr(self.llm, "temperature")
                and model_config.get("temperature") is not None
            ):
                self.llm.temperature = model_config.get("temperature")
            if (
                hasattr(self.llm, "max_tokens")
                and model_config.get("max_tokens") is not None
            ):
                self.llm.max_tokens = model_config.get("max_tokens")
        except (ProviderError, ModelNotFoundError, ConfigurationError) as e:
            raise RuntimeError(f"Failed to load LLM: {e}")

        # Initialize agent factory
        self.agent_factory = AgentFactory(self.llm)

    async def run_test_suite(
        self,
        test_suite_content: str,
        browser: str = "chromium",
        headless: bool = False,
        verbose: bool = False,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        timeout: int | None = None,
        enable_screenshots: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
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
        browser_map = {"chrome": "chromium", "edge": "msedge", "safari": "webkit"}
        actual_browser = browser_map.get(browser, browser)

        # Extract test name early for session directory creation
        test_name = self._extract_test_name(test_suite_content)

        # Build MCP server arguments
        viewport_size = f"{viewport_width},{viewport_height}"
        browser_args = [
            "@playwright/mcp",
            "--browser",
            actual_browser,
            "--viewport-size",
            viewport_size,
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
            session_dir = (
                self.config.storage.base_dir
                / "sessions"
                / f"{test_name_normalized}_{timestamp}"
            )
            session_dir.mkdir(parents=True, exist_ok=True)
            browser_args.extend(["--output-dir", str(session_dir)])
            # Store session directory for later reference
            kwargs["_session_dir"] = session_dir

        server_params = StdioServerParameters(command="npx", args=browser_args)

        # Test name already extracted above

        # Log test start if verbose
        if self.verbose_logger:
            self.verbose_logger.log_test_start(
                test_name,
                {
                    "provider": self.provider,
                    "model": self.model,
                    "browser": browser,
                    "headless": headless,
                    "viewport": f"{viewport_width}x{viewport_height}",
                    "optimization": self.config.get("compression_level", "medium"),
                },
            )

        # Create execution metadata
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
            session_id=str(kwargs.get("_session_dir", uuid.uuid4()))
        )
        
        # Track execution
        start_time = datetime.now(UTC)
        
        # Initialize result components
        execution_steps: list[ExecutionStep] = []
        report_content = ""
        error_message: Optional[str] = None
        token_metrics: Optional[TokenMetrics] = None

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    # Get context management configuration
                    context_strategy = self.config.get("context_strategy", "sliding-window")
                    
                    # Build context config from CLI/config
                    from .context_management.base import ContextConfig
                    context_config = ContextConfig(
                        window_size=self.config.get("context_window_size", 50000),
                        preserve_first_n=self.config.get("context_preserve_first", 5),
                        preserve_last_n=self.config.get("context_preserve_last", 10),
                        compression_level=self.config.get("compression_level", "medium"),
                        preserve_errors=True,
                        preserve_screenshots=True,
                    )
                    
                    # Log context configuration
                    if self.verbose_logger:
                        self.stream.write(f"Context management: {context_strategy}", "debug")
                        self.stream.write(f"Window size: {context_config.window_size} tokens", "debug")
                        self.stream.write(f"Preserve first: {context_config.preserve_first_n}, last: {context_config.preserve_last_n}", "debug")
                    
                    # Create browser automation agent using AgentFactory with context management
                    agent = await self.agent_factory.create_browser_agent(
                        session=session, 
                        recursion_limit=100,
                        context_strategy=context_strategy,
                        context_config=context_config,
                        verbose=self.verbose_logger is not None
                    )

                    # Build execution prompt
                    prompt = self._build_prompt(test_suite_content)

                    # In verbose mode, show the initial prompt
                    if self.verbose_logger:
                        self.stream.write("\n" + "=" * 60, "debug")
                        self.stream.write("INITIAL PROMPT SENT TO LLM:", "info")
                        self.stream.write("=" * 60, "debug")
                        # Show first 1000 chars of prompt
                        prompt_preview = str(prompt)[:1000]
                        if len(str(prompt)) > 1000:
                            prompt_preview += f"\n... (truncated, total length: {len(str(prompt))} chars)"
                        self.stream.write(prompt_preview, "debug")
                        self.stream.write("=" * 60 + "\n", "debug")

                    # Execute test suite
                    steps = []
                    final_response = None

                    async for chunk in agent.astream({"messages": prompt}):
                        steps.append(chunk)

                        # In verbose mode, show every step
                        if self.verbose_logger:
                            self.stream.write(
                                f"\n[STEP {len(steps)}] Processing...", "debug"
                            )

                            # Extract and display tool calls
                            if "tools" in chunk:
                                for tool_msg in chunk.get("tools", {}).get(
                                    "messages", []
                                ):
                                    if hasattr(tool_msg, "name") and hasattr(tool_msg, "content"):
                                        # Create ExecutionStep for tool call
                                        step = ExecutionStep(
                                            type="tool_call",
                                            name=tool_msg.name,
                                            content=str(tool_msg.content),
                                            timestamp=datetime.now(UTC)
                                        )
                                        execution_steps.append(step)
                                        
                                        self.stream.write(
                                            f"  Tool: {tool_msg.name}", "info"
                                        )
                                        # Show first 200 chars of tool response
                                        content = str(tool_msg.content)[:200]
                                        if len(str(tool_msg.content)) > 200:
                                            content += "..."
                                        self.stream.write(
                                            f"  Response: {content}", "debug"
                                        )

                            # Extract and display agent messages
                            if "agent" in chunk:
                                for agent_msg in chunk.get("agent", {}).get(
                                    "messages", []
                                ):
                                    if (
                                        hasattr(agent_msg, "content")
                                        and agent_msg.content
                                    ):
                                        content = str(agent_msg.content)
                                        if len(content) > 50:  # Only include substantial messages
                                            step = ExecutionStep(
                                                type="agent_message",
                                                name=None,
                                                content=content,
                                                timestamp=datetime.now(UTC)
                                            )
                                            execution_steps.append(step)
                                        
                                        self.stream.write(
                                            f"  Agent thinking: {content[:200]}...",
                                            "debug",
                                        )

                        elif len(steps) % 5 == 0:
                            self.stream.write(
                                f"Progress: {len(steps)} steps...", "debug"
                            )

                        # Extract final response from agent
                        if "agent" in chunk and "messages" in chunk["agent"]:
                            for msg in chunk["agent"]["messages"]:
                                if hasattr(msg, "content") and msg.content:
                                    final_response = msg

                    # Process execution results
                    duration = (datetime.now(UTC) - start_time).total_seconds()
                    end_time = datetime.now(UTC)

                    if final_response and hasattr(final_response, "content"):
                        report_content = str(final_response.content)

                    # Extract token usage from telemetry
                    token_metrics = self._get_token_usage()
                    
                    # Get context management metrics if available
                    context_metrics = None
                    if hasattr(agent, '_context_manager'):
                        context_metrics = agent._context_manager.get_metrics()
                        # Log context management summary
                        if self.verbose_logger:
                            self.stream.write("\n" + agent._context_manager.get_summary(), "debug")
                    
                    # Determine success
                    success = self._check_success(report_content)
                    
                    # Create timing information
                    timing = ExecutionTiming(
                        start=start_time,
                        end=end_time,
                        duration_seconds=duration,
                        timezone="UTC"
                    )
                    
                    # Build verbose log if enabled
                    verbose_log = None
                    if self.verbose_logger:
                        self.verbose_logger.log_test_complete(
                            success,
                            duration,
                            f"{len(steps)} steps executed",
                        )
                        verbose_log = {
                            "log_file": str(self.verbose_logger.get_log_file_path()),
                            "summary": self.verbose_logger.get_execution_summary(),
                        }
                    
                    # Create the result model
                    result = BrowserTestResult(
                        success=success,
                        test_name=test_name,
                        duration=duration,
                        report=report_content if success else None,
                        error=error_message if not success else None,
                        steps=execution_steps,
                        execution_time=timing,
                        metrics={
                            "total_steps": len(steps),
                            "execution_time_ms": duration * 1000,
                            "avg_step_time_ms": (duration * 1000) / len(steps) if steps else 0,
                        },
                        token_usage=token_metrics,
                        environment={
                            "token_optimization": self.token_optimizer is not None,
                            "compression_level": self.config.get("compression_level", "medium"),
                            "context_strategy": context_strategy,
                            "context_metrics": context_metrics,
                        },
                        verbose_log=verbose_log,
                        # Browser-specific fields
                        provider=self.provider,
                        model=self.model,
                        browser=browser,
                        headless=headless,
                        viewport_size=viewport_size,
                        steps_executed=len(steps)
                    )
                    
                    # Return the result as dict for backward compatibility
                    return result.to_dict()

        except TimeoutError as e:
            # Handle timeout specifically
            timeout_step = ExecutionStep(
                type="agent_message",
                name="timeout_error",
                content=f"Test execution timed out after {timeout} seconds",
                timestamp=datetime.now(UTC)
            )
            execution_steps.append(timeout_step)
            
            duration = (datetime.now(UTC) - start_time).total_seconds()
            timing = ExecutionTiming(
                start=start_time,
                end=datetime.now(UTC),
                duration_seconds=duration,
                timezone="UTC"
            )
            
            result = BrowserTestResult(
                success=False,
                test_name=test_name,
                duration=duration,
                report=None,
                error=f"Test execution timed out after {timeout} seconds",
                steps=execution_steps,
                execution_time=timing,
                metrics={
                    "total_steps": len(execution_steps),
                    "execution_time_ms": duration * 1000,
                    "avg_step_time_ms": (duration * 1000) / len(execution_steps) if execution_steps else 0,
                },
                token_usage=self._get_token_usage(),
                environment={
                    "token_optimization": self.token_optimizer is not None,
                    "compression_level": self.config.get("compression_level", "medium"),
                    "context_strategy": self.config.get("context_strategy", "sliding-window"),
                    "context_metrics": None,
                },
                verbose_log=None,
                provider=self.provider,
                model=self.model,
                browser=browser,
                headless=headless,
                viewport_size=viewport_size,
                steps_executed=len(execution_steps)
            )
            
            if self.verbose_logger:
                self.verbose_logger.log_test_complete(
                    False,
                    duration,
                    f"Timeout after {timeout} seconds",
                )
                
            return result.to_dict()
            
        except BaseExceptionGroup as eg:
            # Handle ExceptionGroup (Python 3.11+)
            duration = (datetime.now(UTC) - start_time).total_seconds()
            timing = ExecutionTiming(
                start=start_time,
                end=datetime.now(UTC),
                duration_seconds=duration,
                timezone="UTC"
            )
            
            # Extract first meaningful exception
            first_exception = None
            for exc in eg.exceptions:
                if isinstance(exc, TimeoutError):
                    first_exception = exc
                    break
                elif not isinstance(exc, (KeyboardInterrupt, SystemExit)):
                    first_exception = exc
                    break
            
            error_msg = str(first_exception) if first_exception else str(eg)
            
            result = BrowserTestResult(
                success=False,
                test_name=test_name,
                duration=duration,
                report=None,
                error=error_msg,
                steps=execution_steps,
                execution_time=timing,
                metrics={
                    "total_steps": len(execution_steps),
                    "execution_time_ms": duration * 1000,
                    "avg_step_time_ms": (duration * 1000) / len(execution_steps) if execution_steps else 0,
                },
                token_usage=self._get_token_usage(),
                environment={
                    "token_optimization": self.token_optimizer is not None,
                    "compression_level": self.config.get("compression_level", "medium"),
                    "context_strategy": self.config.get("context_strategy", "sliding-window"),
                    "context_metrics": None,
                },
                verbose_log=None,
                provider=self.provider,
                model=self.model,
                browser=browser,
                headless=headless,
                viewport_size=viewport_size,
                steps_executed=len(execution_steps)
            )
            
            if self.verbose_logger:
                self.verbose_logger.log_test_complete(
                    False,
                    duration,
                    f"Error: {error_msg}",
                )
                
            if verbose:
                import traceback
                traceback.print_exc()
                
            return result.to_dict()
            
        except Exception as e:
            # Handle other exceptions
            duration = (datetime.now(UTC) - start_time).total_seconds()
            timing = ExecutionTiming(
                start=start_time,
                end=datetime.now(UTC),
                duration_seconds=duration,
                timezone="UTC"
            )
            
            result = BrowserTestResult(
                success=False,
                test_name=test_name,
                duration=duration,
                report=None,
                error=str(e),
                steps=execution_steps,
                execution_time=timing,
                metrics={
                    "total_steps": len(execution_steps),
                    "execution_time_ms": duration * 1000,
                    "avg_step_time_ms": (duration * 1000) / len(execution_steps) if execution_steps else 0,
                },
                token_usage=self._get_token_usage(),
                environment={
                    "token_optimization": self.token_optimizer is not None,
                    "compression_level": self.config.get("compression_level", "medium"),
                    "context_strategy": self.config.get("context_strategy", "sliding-window"),
                    "context_metrics": None,
                },
                verbose_log=None,
                provider=self.provider,
                model=self.model,
                browser=browser,
                headless=headless,
                viewport_size=viewport_size,
                steps_executed=len(execution_steps)
            )
            
            if self.verbose_logger:
                self.verbose_logger.log_test_complete(
                    False,
                    duration,
                    f"Error: {str(e)}",
                )
                
            if verbose:
                import traceback
                traceback.print_exc()

        # Return the result as dict for backward compatibility
        return result.to_dict()

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
6. For form fields - IMPORTANT:
   - Process each field completely before moving to the next
   - Click a field and immediately type in it (don't click multiple fields then type)
   - For each field: click it, then type the value right away
   - Never click all fields first and then go back to type
   - If a field doesn't accept input, click it again
7. Be especially careful with the first field in a form - complete it fully before moving on

At the end, generate a comprehensive test report in markdown format:

# Test Execution Report

## Summary
- Overall Status: PASSED or FAILED
- Duration: X seconds
- Browser: {self.browser if hasattr(self, "browser") else "Unknown"}

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
            if metrics["reduction_percentage"] > 0:
                self.stream.write(
                    f"Prompt optimized: {metrics['reduction_percentage']:.1f}% reduction",
                    "debug",
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
            "test passed successfully",
        ]

        # Must have test execution report or summary
        has_report = any(
            header in lower_content 
            for header in [
                "test execution report",
                "test execution summary", 
                "test report",
                "execution report",
                "test results"
            ]
        )

        # Check for any success pattern
        has_success = any(pattern in lower_content for pattern in success_patterns)

        # Check for explicit failure
        has_failure = any(
            fail in lower_content
            for fail in [
                "overall status:** failed",
                "overall status: failed",
                "test failed",
            ]
        )

        return has_report and has_success and not has_failure

    def _get_token_usage(self) -> TokenMetrics | None:
        """Extract token usage metrics from telemetry"""
        if not self.telemetry:
            return None

        try:
            # Try to get metrics from telemetry
            if hasattr(self.telemetry, "metrics") and self.telemetry.metrics:
                metrics = self.telemetry.metrics
                total_tokens = 0
                prompt_tokens = 0
                completion_tokens = 0
                estimated_cost = None

                # Extract token usage if available
                if hasattr(metrics, "token_usage"):
                    token_usage = metrics.token_usage
                    total_tokens = getattr(token_usage, "total_tokens", 0)
                    prompt_tokens = getattr(token_usage, "prompt_tokens", 0)
                    completion_tokens = getattr(token_usage, "completion_tokens", 0)

                # Extract cost if available
                if hasattr(metrics, "estimated_cost"):
                    estimated_cost = metrics.estimated_cost
                # Enhanced LLM cost estimation (if available and no cost from telemetry)
                elif (
                    hasattr(self.llm, "estimate_cost")
                    and prompt_tokens > 0
                    and completion_tokens > 0
                ):
                    try:
                        estimated_cost = self.llm.estimate_cost(
                            prompt_tokens, completion_tokens
                        )
                    except Exception:
                        pass  # Fall back to telemetry cost if enhanced estimation fails

                # Add context length information if we have prompt tokens
                context_length = prompt_tokens if prompt_tokens > 0 else None
                max_context_length = None
                context_usage_percentage = None

                if context_length:
                    # Get context limit from enhanced model-forge LLM (v2.2.1+)
                    max_context = None

                    # First priority: Use context_length property from enhanced LLM
                    if hasattr(self.llm, "context_length") and self.llm.context_length:
                        max_context = self.llm.context_length

                    # Second priority: Check model_info from enhanced LLM
                    elif hasattr(self.llm, "model_info") and isinstance(
                        self.llm.model_info, dict
                    ):
                        limit_info = self.llm.model_info.get("limit", {})
                        if "context" in limit_info:
                            max_context = limit_info["context"]

                    # Fallback to hardcoded limits only if enhanced features aren't available
                    if not max_context:
                        model_limits = self._get_model_context_limits()
                        model_key = (
                            f"{self.provider}_{self.model}".lower()
                            .replace("-", "_")
                            .replace(".", "_")
                        )

                        if model_key in model_limits:
                            max_context = model_limits[model_key]
                        else:
                            # Try to match by model name only
                            for key, limit in model_limits.items():
                                if (
                                    self.model.lower()
                                    .replace("-", "_")
                                    .replace(".", "_")
                                    in key
                                ):
                                    max_context = limit
                                    break

                    # Set the context usage info if we found a limit
                    if max_context:
                        max_context_length = max_context
                        context_usage_percentage = round(
                            (context_length / max_context) * 100, 1
                        )

                # Add optimization savings if available
                optimization_savings = None
                if self.token_optimizer:
                    opt_metrics = self.token_optimizer.get_metrics()
                    if opt_metrics["original_tokens"] > 0:
                        # Estimate cost savings
                        estimated_savings = None
                        if estimated_cost and total_tokens > 0:
                            cost_per_token = estimated_cost / total_tokens
                            tokens_saved = (
                                opt_metrics["original_tokens"]
                                - opt_metrics["optimized_tokens"]
                            )
                            estimated_savings = tokens_saved * cost_per_token

                        optimization_savings = OptimizationSavings(
                            original_tokens=opt_metrics["original_tokens"],
                            optimized_tokens=opt_metrics["optimized_tokens"],
                            reduction_percentage=opt_metrics["reduction_percentage"],
                            strategies_applied=opt_metrics["strategies_applied"],
                            estimated_savings=estimated_savings
                        )

                # Return TokenMetrics even if counts are zero
                return TokenMetrics(
                    total_tokens=total_tokens,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    estimated_cost=estimated_cost,
                    context_length=context_length,
                    max_context_length=max_context_length,
                    context_usage_percentage=context_usage_percentage,
                    optimization_savings=optimization_savings
                )

            return None

        except Exception:
            # If anything goes wrong, return None
            return None

    def _extract_steps(self, steps: list) -> list[ExecutionStep]:
        """Extract execution steps from agent execution
        
        This method is kept for backward compatibility but could be removed
        since we now create ExecutionStep objects directly in the main loop.
        """
        extracted_steps = []

        for step in steps:
            if isinstance(step, dict):
                # Extract tool calls
                if "tools" in step:
                    for tool_msg in step.get("tools", {}).get("messages", []):
                        if hasattr(tool_msg, "name") and hasattr(tool_msg, "content"):
                            content = str(tool_msg.content)
                            extracted_steps.append(
                                ExecutionStep(
                                    type="tool_call",
                                    name=tool_msg.name,
                                    content=content,
                                    timestamp=datetime.now(UTC)
                                )
                            )

                # Extract agent messages
                if "agent" in step:
                    for agent_msg in step.get("agent", {}).get("messages", []):
                        if hasattr(agent_msg, "content") and agent_msg.content:
                            content = str(agent_msg.content)
                            if len(content) > 50:  # Only include substantial messages
                                extracted_steps.append(
                                    ExecutionStep(
                                        type="agent_message",
                                        name=None,
                                        content=content,
                                        timestamp=datetime.now(UTC)
                                    )
                                )

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
            "high": OptimizationLevel.HIGH,
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
        lines = test_content.strip().split("\n")

        # Look for markdown heading
        for line in lines:
            if line.startswith("#"):
                return line.strip("# ").strip()

        # Use first non-empty line
        for line in lines:
            if line.strip():
                # Truncate if too long
                name = line.strip()
                if len(name) > 50:
                    name = name[:47] + "..."
                return name

        return "Browser Test"

    def _get_model_context_limits(self) -> dict[str, int]:
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
        normalized = test_name.lower().replace(" ", "-")
        # Remove special characters, keep only alphanumeric and hyphens
        normalized = re.sub(r"[^a-z0-9-]", "", normalized)
        # Remove multiple consecutive hyphens
        normalized = re.sub(r"-+", "-", normalized)
        # Remove leading/trailing hyphens
        normalized = normalized.strip("-")
        # Ensure it's not empty
        if not normalized:
            normalized = "browser-test"
        # Limit length
        if len(normalized) > 50:
            normalized = normalized[:50].rstrip("-")
        return normalized

    def close(self) -> None:
        """Clean up resources, particularly closing the verbose logger"""
        if hasattr(self, "verbose_logger") and self.verbose_logger:
            self.verbose_logger.close()
