"""
Verbose Logger for Browser Copilot

Provides enhanced logging with dual output (console + file) for debugging.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from langchain_core.callbacks.base import BaseCallbackHandler

try:
    from .storage_manager import StorageManager
except ImportError:
    # For standalone testing
    try:
        from browser_copilot.storage_manager import StorageManager
    except ImportError:
        # For unit testing
        from storage_manager import (  # type: ignore[no-redef]
            StorageManager,  # type: ignore[import-not-found]
        )


class VerboseLogger:
    """Enhanced logger with dual output and structured logging"""

    def __init__(
        self,
        storage_manager: StorageManager | None = None,
        console_enabled: bool = True,
        file_enabled: bool = True,
        log_level: str = "DEBUG",
    ):
        """
        Initialize VerboseLogger

        Args:
            storage_manager: StorageManager instance for file paths
            console_enabled: Whether to log to console
            file_enabled: Whether to log to file
            log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR)
        """
        self.storage = storage_manager or StorageManager()
        self.console_enabled = console_enabled
        self.file_enabled = file_enabled
        self.log_level = getattr(logging, log_level.upper(), logging.DEBUG)

        # Create unique log file for this session
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = (
            self.storage.get_logs_dir() / f"browser_copilot_{self.session_id}.log"
        )

        # Setup loggers
        self._setup_logger()

        # Track structured data
        self.execution_steps: list[dict[str, Any]] = []
        self.tool_calls: list[dict[str, Any]] = []
        self.token_metrics: dict[str, Any] = {}

    def _setup_logger(self) -> None:
        """Configure Python logging with dual outputs"""
        self.logger = logging.getLogger(f"browser_copilot_{self.session_id}")
        self.logger.setLevel(self.log_level)
        self.logger.handlers.clear()  # Clear any existing handlers

        # Create formatters
        console_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
        )
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        if self.console_enabled:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        # File handler
        if self.file_enabled:
            file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)  # Always log everything to file
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

    def log_test_start(self, test_name: str, config: dict[str, Any]) -> None:
        """Log test execution start"""
        self.logger.info(f"Starting test: {test_name}")
        self.logger.debug(f"Configuration: {json.dumps(config, indent=2)}")

        # Write header to log file
        if self.file_enabled:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write("\n" + "=" * 80 + "\n")
                f.write(f"Test: {test_name}\n")
                f.write(f"Started: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n\n")

    def log_step(
        self,
        step_type: str,
        description: str,
        details: dict[str, Any] | None = None,
        level: str = "INFO",
    ) -> None:
        """
        Log an execution step

        Args:
            step_type: Type of step (e.g., "navigation", "interaction", "verification")
            description: Human-readable description
            details: Additional structured data
            level: Log level
        """
        timestamp = datetime.now()

        # Create step record
        step = {
            "timestamp": timestamp.isoformat(),
            "type": step_type,
            "description": description,
            "details": details or {},
        }
        self.execution_steps.append(step)

        # Log to outputs
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(f"[{step_type.upper()}] {description}")

        if details and self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"Details: {json.dumps(details, indent=2)}")

    def log_tool_call(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        result: Any,
        duration_ms: float | None = None,
    ) -> None:
        """
        Log a browser tool call

        Args:
            tool_name: Name of the tool called
            parameters: Tool parameters
            result: Tool execution result
            duration_ms: Execution duration in milliseconds
        """
        tool_call = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "parameters": parameters,
            "result": self._truncate_result(result),
            "duration_ms": duration_ms,
        }
        self.tool_calls.append(tool_call)

        # Format for logging
        param_str = json.dumps(parameters, ensure_ascii=False)
        if len(param_str) > 100:
            param_str = param_str[:97] + "..."

        msg = f"Tool: {tool_name}({param_str})"
        if duration_ms:
            msg += f" [{duration_ms:.1f}ms]"

        self.logger.debug(msg)

    def log_token_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        estimated_cost: float | None = None,
    ) -> None:
        """Log token usage metrics"""
        self.token_metrics = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": estimated_cost,
        }

        msg = f"Tokens used: {total_tokens} (prompt: {prompt_tokens}, completion: {completion_tokens})"
        if estimated_cost:
            msg += f" | Cost: ${estimated_cost:.4f}"

        self.logger.info(msg)

    def log_error(
        self,
        error_type: str,
        message: str,
        details: dict[str, Any] | None = None,
        recoverable: bool = True,
    ) -> None:
        """
        Log an error

        Args:
            error_type: Type of error
            message: Error message
            details: Additional error details
            recoverable: Whether execution can continue
        """
        _ = {
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "message": message,
            "details": details or {},
            "recoverable": recoverable,
        }

        level = "WARNING" if recoverable else "ERROR"
        log_method = getattr(self.logger, level.lower())

        log_method(f"[{error_type}] {message}")
        if details:
            self.logger.debug(f"Error details: {json.dumps(details, indent=2)}")

    def log_screenshot(self, filepath: Path, description: str) -> None:
        """Log screenshot capture"""
        self.logger.info(f"Screenshot saved: {filepath.name} - {description}")
        self.log_step("screenshot", description, {"file": str(filepath)}, level="DEBUG")

    def log_test_complete(
        self, success: bool, duration: float, summary: str | None = None
    ) -> None:
        """Log test completion"""
        status = "PASSED" if success else "FAILED"
        self.logger.info(f"Test {status} in {duration:.2f} seconds")

        if summary:
            self.logger.info(f"Summary: {summary}")

        # Log final metrics
        if self.token_metrics:
            self.log_token_usage(**self.token_metrics)

        # Write summary to file
        if self.file_enabled:
            self._write_execution_summary()

    def get_log_file_path(self) -> Path:
        """Get the path to the current log file"""
        return self.log_file

    def get_execution_summary(self) -> dict[str, Any]:
        """Get structured summary of execution"""
        return {
            "session_id": self.session_id,
            "log_file": str(self.log_file),
            "steps": len(self.execution_steps),
            "tool_calls": len(self.tool_calls),
            "token_usage": self.token_metrics,
            "execution_steps": self.execution_steps[-10:],  # Last 10 steps
            "recent_tools": self.tool_calls[-10:],  # Last 10 tool calls
        }

    def _truncate_result(self, result: Any, max_length: int = 200) -> Any:
        """Truncate long results for logging"""
        if isinstance(result, str) and len(result) > max_length:
            return result[:max_length] + "..."
        elif isinstance(result, dict):
            return {k: self._truncate_result(v, max_length) for k, v in result.items()}
        elif isinstance(result, list) and len(result) > 10:
            return result[:10] + ["..."]
        return result

    def _write_execution_summary(self) -> None:
        """Write execution summary to log file"""
        summary = self.get_execution_summary()

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write("\n\n" + "=" * 80 + "\n")
            f.write("EXECUTION SUMMARY\n")
            f.write("=" * 80 + "\n")
            f.write(json.dumps(summary, indent=2, ensure_ascii=False))
            f.write("\n" + "=" * 80 + "\n")

    def close(self) -> None:
        """Close all file handlers to release file locks"""
        # Close all handlers, especially file handlers
        for handler in self.logger.handlers[
            :
        ]:  # Copy list to avoid modification during iteration
            if hasattr(handler, "close"):
                handler.close()
            self.logger.removeHandler(handler)


class LangChainVerboseCallback(BaseCallbackHandler):
    """Callback for integrating VerboseLogger with LangChain"""

    def __init__(self, verbose_logger: VerboseLogger):
        """
        Initialize callback

        Args:
            verbose_logger: VerboseLogger instance
        """
        super().__init__()
        self.logger = verbose_logger
        self._start_times: dict[str, datetime] = {}

    def on_tool_start(
        self, serialized: dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Called when tool starts"""
        tool_name = serialized.get("name", "unknown")
        self._start_times[tool_name] = datetime.now()

        self.logger.log_step(
            "tool_start", f"Starting {tool_name}", {"input": input_str}, level="DEBUG"
        )

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when tool completes"""
        # Calculate duration if we have start time
        tool_name = kwargs.get("name", "unknown")
        duration_ms = None

        if tool_name in self._start_times:
            duration = (
                datetime.now() - self._start_times[tool_name]
            ).total_seconds() * 1000
            duration_ms = duration
            del self._start_times[tool_name]

        self.logger.log_tool_call(
            tool_name, kwargs.get("input", {}), output, duration_ms
        )

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Called when tool errors"""
        tool_name = kwargs.get("name", "unknown")

        self.logger.log_error(
            "tool_error",
            f"Tool {tool_name} failed: {str(error)}",
            {"tool": tool_name, "error_type": type(error).__name__},
            recoverable=True,
        )

    def on_llm_start(
        self, serialized: dict[str, Any], prompts: list[str], **kwargs: Any
    ) -> None:
        """Called when LLM starts"""
        # Show the actual prompt being sent in verbose mode
        prompt_preview = ""
        if prompts and len(prompts) > 0:
            # Show first 500 chars of the prompt
            prompt_preview = str(prompts[0])[:500]
            if len(str(prompts[0])) > 500:
                prompt_preview += (
                    f"... (truncated, total: {len(str(prompts[0]))} chars)"
                )

        self.logger.log_step(
            "llm_call",
            "Sending prompt to LLM",
            {"prompt_count": len(prompts), "prompt_preview": prompt_preview},
            level="DEBUG",
        )

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Called when LLM completes"""
        # Show the LLM response in verbose mode
        response_preview = ""
        if hasattr(response, "generations") and response.generations:
            if len(response.generations) > 0 and len(response.generations[0]) > 0:
                generation = response.generations[0][0]
                if hasattr(generation, "text"):
                    response_preview = generation.text[:500]
                    if len(generation.text) > 500:
                        response_preview += (
                            f"... (truncated, total: {len(generation.text)} chars)"
                        )
                elif hasattr(generation, "message") and hasattr(
                    generation.message, "content"
                ):
                    response_preview = str(generation.message.content)[:500]
                    if len(str(generation.message.content)) > 500:
                        response_preview += "... (truncated)"

        if response_preview:
            self.logger.log_step(
                "llm_response",
                "Received LLM response",
                {"response_preview": response_preview},
                level="DEBUG",
            )

        # Extract token usage if available
        if hasattr(response, "llm_output") and response.llm_output:
            usage = response.llm_output.get("token_usage", {})
            if usage:
                self.logger.log_token_usage(
                    usage.get("prompt_tokens", 0),
                    usage.get("completion_tokens", 0),
                    usage.get("total_tokens", 0),
                    response.llm_output.get("estimated_cost"),
                )
