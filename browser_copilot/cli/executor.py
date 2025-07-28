"""
Test executor for Browser Copilot CLI

Handles the orchestration of test execution.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from ..core import BrowserPilot
from ..io import OutputHandler
from ..test_enhancer import TestSuiteEnhancer
from .utils import normalize_test_name_for_path


class BrowserTestExecutor:
    """Orchestrates test execution"""

    def __init__(
        self,
        config,
        storage,
        stream,
    ):
        """
        Initialize TestExecutor

        Args:
            config: ConfigManager instance
            storage: StorageManager instance
            stream: StreamHandler instance
        """
        self.config = config
        self.storage = storage
        self.stream = stream

    async def execute_test(
        self,
        test_content: str,
        system_prompt: str | None = None,
        enhance_test: bool = False,
        playwright_kwargs: dict | None = None,
    ) -> dict[str, Any]:
        """
        Execute a test suite

        Args:
            test_content: Test scenario content
            system_prompt: Optional custom system prompt
            enhance_test: Whether to enhance the test with AI
            playwright_kwargs: Additional Playwright configuration

        Returns:
            Test execution result dictionary
        """
        # Enhance test if requested
        if enhance_test:
            self.stream.write("Enhancing test scenario with AI...", "info")
            enhancer = TestSuiteEnhancer(
                config=self.config,
            )
            try:
                test_content = await enhancer.enhance_test_suite(test_content)
                self.stream.write("Test scenario enhanced successfully", "info")
            except Exception as e:
                self.stream.write(
                    f"Test enhancement failed: {e}. Using original test.", "warning"
                )

        # Get model configuration
        provider = self.config.get("provider")
        model = self.config.get("model")

        if not provider or not model:
            raise ValueError("Provider and model must be specified")

        # Initialize Browser Copilot
        self.stream.write(
            f"Initializing Browser Copilot with {provider}/{model}", "info"
        )

        pilot = BrowserPilot(
            provider=provider,
            model=model,
            system_prompt=system_prompt,
            config=self.config,
            stream=self.stream,
        )

        # Execute test
        browser_config = self.config.get_browser_config()
        self.stream.write(
            f"Executing test with {browser_config['browser']} browser", "info"
        )

        # Merge playwright kwargs with config
        if playwright_kwargs is None:
            playwright_kwargs = {}

        execution_kwargs = {
            "browser": browser_config["browser"],
            "headless": browser_config["headless"],
            "viewport_width": browser_config["viewport"]["width"],
            "viewport_height": browser_config["viewport"]["height"],
            "timeout": self.config.get("timeout"),
            "enable_screenshots": self.config.get("enable_screenshots"),
            "verbose": self.config.get("verbose"),
            **playwright_kwargs,  # Override with any specific kwargs
        }

        # Remove None values
        execution_kwargs = {k: v for k, v in execution_kwargs.items() if v is not None}

        try:
            result = await pilot.run_test_suite(test_content, **execution_kwargs)
            return result
        finally:
            # Always close the pilot to clean up resources
            pilot.close()

    def save_results(
        self,
        result: dict[str, Any],
        output_format: str = "markdown",
        output_file: str | None = None,
    ) -> dict[str, Path]:
        """
        Save test results to appropriate locations

        Args:
            result: Test execution result
            output_format: Output format for results
            output_file: Optional custom output file path

        Returns:
            Dictionary of saved file paths
        """
        # Create session-specific output directory
        test_name = result.get("test_name", "browser-test")
        test_name_normalized = normalize_test_name_for_path(test_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_name = f"{test_name_normalized}_{timestamp}"
        session_dir = self.storage.base_dir / "sessions" / session_name

        # Create subdirectories
        reports_dir = session_dir / "reports"
        screenshots_dir = session_dir / "screenshots"
        logs_dir = session_dir / "logs"

        reports_dir.mkdir(parents=True, exist_ok=True)
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Store session info in result for reference
        result["session_info"] = {
            "session_name": session_name,
            "session_dir": str(session_dir),
            "timestamp": timestamp,
        }

        # Determine file extension
        file_extension = {
            "markdown": "md",
            "json": "json",
            "yaml": "yml",
            "xml": "xml",
            "junit": "xml",
            "html": "html",
        }.get(output_format, "txt")

        report_filename = f"test_report.{file_extension}"
        report_path = reports_dir / report_filename

        # Format the full report
        full_report = OutputHandler.format_output(
            result, format_type=output_format, include_metadata=True
        )

        # Save the report
        OutputHandler.write_output(full_report, file_path=report_path)

        saved_files = {"report": report_path}

        # If user specified custom output file, copy report there too
        if output_file:
            output_path = Path(output_file)
            OutputHandler.write_output(full_report, file_path=output_path)
            saved_files["custom_output"] = output_path

        # Move screenshots if any
        if "_session_dir" in result and Path(result["_session_dir"]).exists():
            src_dir = Path(result["_session_dir"])
            for screenshot in src_dir.glob("*.png"):
                dst = screenshots_dir / screenshot.name
                screenshot.rename(dst)
                self.stream.write(f"Moved screenshot: {screenshot.name}", "debug")

        # Copy verbose log if available
        if "verbose_log" in result and "log_file" in result["verbose_log"]:
            log_path = Path(result["verbose_log"]["log_file"])
            if log_path.exists():
                dst = logs_dir / log_path.name
                log_path.rename(dst)
                saved_files["verbose_log"] = dst

        return saved_files

    def display_summary(self, result: dict[str, Any], quiet: bool = False) -> None:
        """
        Display test execution summary to console

        Args:
            result: Test execution result
            quiet: Whether to suppress output
        """
        if quiet:
            return

        from .utils import format_duration, format_token_count, get_status_emoji

        # Create a concise summary for console
        status_emoji = get_status_emoji(result.get("success", False))
        duration = result.get("duration_seconds", 0)

        console_summary = f"""
# Browser Copilot Test Report

## Test Summary

- **Test Name:** {result.get("test_name", "Browser Test")}
- **Status:** {status_emoji} {"PASSED" if result.get("success") else "FAILED"}
- **Duration:** {format_duration(duration)}
- **Browser:** {result.get("browser", "Unknown")}
- **Provider:** {result.get("provider", "Unknown")}/{result.get("model", "Unknown")}
"""

        # Add token usage summary
        if "token_usage" in result and result["token_usage"]:
            usage = result["token_usage"]
            console_summary += f"""
- **Token Usage:** {format_token_count(usage.get("total_tokens", 0))} tokens
- **Estimated Cost:** ${usage.get("estimated_cost", 0):.4f}
"""
            # Add context usage if available
            if "context_length" in usage and "max_context_length" in usage:
                percentage = usage.get("context_usage_percentage", 0)
                context_emoji = (
                    "⚠️" if percentage >= 80 else "⚡" if percentage >= 60 else "✅"
                )
                console_summary += f"- **Context Usage:** {format_token_count(usage.get('context_length', 0))}/{format_token_count(usage.get('max_context_length', 0))} tokens ({percentage}%) {context_emoji}\n"

            if result.get("provider") == "github_copilot":
                console_summary += "\n> **Note:** Cost estimates for GitHub Copilot are approximate. Actual costs depend on your subscription plan.\n"

        # Add error if present
        if result.get("error"):
            console_summary += f"""
## Error Details

{result["error"]}
"""

        # Add session info
        if "session_info" in result:
            console_summary += f"""
## Session Information

- **Session ID:** {result["session_info"]["session_name"]}
- **Results saved to:** {result["session_info"]["session_dir"]}
"""

        print(console_summary)
