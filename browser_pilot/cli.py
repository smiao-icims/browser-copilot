"""
Command-line interface for Browser Pilot

This module provides the CLI entry point for running browser
automation tests from the command line.
"""

import argparse
import asyncio
import re
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .config_manager import ConfigManager
from .core import BrowserPilot
from .io_handlers import InputHandler, OutputHandler, StreamHandler
from .reporter import print_header
from .storage_manager import StorageManager


def _normalize_test_name_for_path(test_name: str) -> str:
    """
    Normalize test name for use in file paths
    
    Args:
        test_name: Original test name
        
    Returns:
        Normalized test name safe for file paths
    """
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


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Browser Pilot - AI-powered browser test automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a test from file
  browser-pilot test.md

  # Run test from stdin
  echo "Navigate to example.com and verify title" | browser-pilot -

  # Run with custom output format
  browser-pilot test.md --output-format html --output-file report.html

  # Run with custom system prompt
  browser-pilot test.md --system-prompt prompt.txt

  # Use custom configuration
  browser-pilot test.md --provider anthropic --model claude-3-opus --browser firefox
        """
    )
    
    # Positional argument for test scenario (optional for cleanup mode)
    parser.add_argument(
        "test_scenario",
        nargs="?",
        default="-",
        help="Test scenario file path or '-' for stdin (default: -). Not required when using --cleanup"
    )
    
    # Model configuration (now optional with smart defaults)
    parser.add_argument(
        "--provider", 
        help="LLM provider (uses ModelForge discovery if not specified)"
    )
    parser.add_argument(
        "--model", 
        help="Model name (uses provider default if not specified)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        help="Model temperature (0.0-1.0)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        help="Maximum tokens for model response"
    )
    
    # Browser options
    parser.add_argument(
        "--browser", 
        choices=["chromium", "chrome", "firefox", "safari", "webkit", "edge", "msedge"],
        help="Browser to use (default: chromium)"
    )
    parser.add_argument(
        "--headless", 
        action="store_true", 
        help="Run browser in headless mode"
    )
    parser.add_argument(
        "--viewport-width",
        type=int,
        help="Browser viewport width (default: 1280)"
    )
    parser.add_argument(
        "--viewport-height",
        type=int,
        help="Browser viewport height (default: 720)"
    )
    
    # Playwright MCP specific options
    parser.add_argument(
        "--no-isolated",
        action="store_true",
        help="Disable isolated browser mode (default: isolated mode enabled for clean state)"
    )
    parser.add_argument(
        "--device",
        help="Device to emulate (e.g., 'iPhone 15', 'Pixel 7')"
    )
    parser.add_argument(
        "--user-agent",
        help="Custom user agent string"
    )
    parser.add_argument(
        "--proxy-server",
        help="Proxy server URL (e.g., 'http://myproxy:3128')"
    )
    parser.add_argument(
        "--proxy-bypass",
        help="Comma-separated domains to bypass proxy"
    )
    parser.add_argument(
        "--ignore-https-errors",
        action="store_true",
        help="Ignore HTTPS certificate errors"
    )
    parser.add_argument(
        "--block-service-workers",
        action="store_true",
        help="Block service workers for consistent testing"
    )
    parser.add_argument(
        "--save-trace",
        action="store_true",
        help="Save Playwright trace for debugging"
    )
    parser.add_argument(
        "--save-session",
        action="store_true",
        help="Save browser session for debugging"
    )
    parser.add_argument(
        "--allowed-origins",
        help="Semicolon-separated list of allowed origins"
    )
    parser.add_argument(
        "--blocked-origins",
        help="Semicolon-separated list of blocked origins"
    )
    
    # Output options
    parser.add_argument(
        "--output-format",
        choices=["json", "yaml", "xml", "junit", "html", "markdown"],
        help="Output format for test results"
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        help="File to save test results (stdout if not specified)"
    )
    parser.add_argument(
        "--verbose", 
        "-v",
        action="store_true", 
        help="Enable verbose output with step-by-step debugging"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress all output except errors"
    )
    
    # Advanced options
    parser.add_argument(
        "--system-prompt",
        type=Path,
        help="Custom system prompt file"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="Test execution timeout in seconds"
    )
    parser.add_argument(
        "--retry",
        type=int,
        help="Number of retries on failure"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        help="Number of parallel tests to run"
    )
    parser.add_argument(
        "--no-screenshots",
        action="store_true",
        help="Disable screenshot capture"
    )
    parser.add_argument(
        "--no-token-optimization",
        action="store_true",
        help="Disable token optimization"
    )
    parser.add_argument(
        "--compression-level",
        choices=["none", "low", "medium", "high"],
        default="medium",
        help="Token optimization level: none (0%%), low (10%%), medium (20%%, default), high (30%%)"
    )
    
    # Configuration management
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--save-config",
        action="store_true",
        help="Save current settings as defaults"
    )
    
    # Cleanup options
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up all test outputs and exit"
    )
    parser.add_argument(
        "--cleanup-days",
        type=int,
        default=7,
        help="Clean up outputs older than specified days (default: 7)"
    )
    
    # Setup wizard
    parser.add_argument(
        "--setup-wizard",
        action="store_true",
        help="Launch interactive configuration wizard"
    )
    
    return parser.parse_args()


def load_test_scenario(scenario_path: str, stream: StreamHandler) -> Optional[str]:
    """
    Load test scenario from file or stdin
    
    Args:
        scenario_path: Path to test file or '-' for stdin
        stream: Stream handler for output
        
    Returns:
        Test scenario content or None if invalid
    """
    try:
        if scenario_path == "-":
            stream.write("Reading test scenario from stdin...", "info")
            content = InputHandler.read_from_stdin()
        else:
            test_path = Path(scenario_path)
            stream.write(f"Reading test scenario from: {test_path}", "info")
            content = InputHandler.read_from_file(test_path)
        
        # Validate scenario
        warnings = InputHandler.validate_scenario(content)
        for warning in warnings:
            stream.write(f"Warning: {warning}", "warning")
        
        return content
        
    except Exception as e:
        stream.write(f"Failed to load test scenario: {e}", "error")
        return None


async def run_test_async(args: argparse.Namespace) -> int:
    """
    Run test suite asynchronously
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Initialize components
    storage = StorageManager()
    config = ConfigManager(storage)
    stream = StreamHandler(verbose=args.verbose, quiet=args.quiet)
    
    # Load configuration from file if specified
    if args.config:
        try:
            config.import_config(args.config)
            stream.write(f"Loaded configuration from: {args.config}", "info")
        except Exception as e:
            stream.write(f"Failed to load config: {e}", "error")
            return 1
    
    # Set CLI arguments in config (highest priority)
    cli_config = {k: v for k, v in vars(args).items() if v is not None}
    config.set_cli_args(cli_config)
    
    # Validate configuration
    errors = config.validate()
    if errors:
        for error in errors:
            stream.write(error, "error")
        return 1
    
    # Load test scenario
    test_content = load_test_scenario(args.test_scenario, stream)
    if not test_content:
        return 1
    
    # Load custom system prompt if specified
    system_prompt = None
    if args.system_prompt:
        try:
            system_prompt = args.system_prompt.read_text()
            stream.write(f"Loaded system prompt from: {args.system_prompt}", "info")
        except Exception as e:
            stream.write(f"Failed to load system prompt: {e}", "warning")
    
    # Get configuration values
    provider = config.get("provider")
    model = config.get("model")
    
    if not provider or not model:
        stream.write("Provider and model must be specified", "error")
        return 1
    
    # Initialize Browser Pilot
    stream.write(f"Initializing Browser Pilot with {provider}/{model}", "info")
    
    try:
        pilot = BrowserPilot(
            provider=provider,
            model=model,
            system_prompt=system_prompt,
            config=config,
            stream=stream
        )
    except Exception as e:
        stream.write(f"Failed to initialize Browser Pilot: {e}", "error")
        return 1
    
    # Execute test
    browser_config = config.get_browser_config()
    stream.write(f"Executing test with {browser_config['browser']} browser", "info")
    
    try:
        # Build kwargs for Playwright MCP options
        playwright_kwargs = {
            "browser": browser_config["browser"],
            "headless": browser_config["headless"],
            "viewport_width": browser_config["viewport"]["width"],
            "viewport_height": browser_config["viewport"]["height"],
            "timeout": config.get("timeout"),
            "enable_screenshots": config.get("enable_screenshots"),
            "verbose": config.get("verbose"),
            # Pass through Playwright MCP specific options
            "no_isolated": args.no_isolated,
            "device": args.device,
            "user_agent": args.user_agent,
            "proxy_server": args.proxy_server,
            "proxy_bypass": args.proxy_bypass,
            "ignore_https_errors": args.ignore_https_errors,
            "block_service_workers": args.block_service_workers,
            "save_trace": args.save_trace,
            "save_session": args.save_session,
            "allowed_origins": args.allowed_origins,
            "blocked_origins": args.blocked_origins,
        }
        
        # Remove None values to avoid passing unnecessary arguments
        playwright_kwargs = {k: v for k, v in playwright_kwargs.items() if v is not None}
        
        result = await pilot.run_test_suite(
            test_content,
            **playwright_kwargs
        )
    except Exception as e:
        stream.write(f"Test execution failed: {e}", "error")
        if config.get("verbose"):
            import traceback
            stream.write(traceback.format_exc(), "debug")
        return 1
    
    # Create session-specific output directory
    test_name = result.get("test_name", "browser-test")
    test_name_normalized = _normalize_test_name_for_path(test_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_name = f"{test_name_normalized}_{timestamp}"
    session_dir = storage.base_dir / "sessions" / session_name
    
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
        "timestamp": timestamp
    }
    
    # Determine report format (markdown by default for better readability)
    report_format = args.output_format or "markdown"
    file_extension = "md" if report_format == "markdown" else "json" if report_format == "json" else "html"
    report_filename = f"test_report.{file_extension}"
    report_path = reports_dir / report_filename
    
    # Format the full report with all details
    full_report = OutputHandler.format_output(
        result,
        format_type=report_format,
        include_metadata=True
    )
    
    # Save the report
    OutputHandler.write_output(
        full_report,
        file_path=report_path
    )
    
    # If user specified custom output file, copy report there too
    if args.output_file:
        OutputHandler.write_output(
            full_report,
            file_path=args.output_file
        )
    
    # Display console summary
    if not args.quiet:
        # Create a concise summary for console
        status_emoji = "✅" if result.get("success") else "❌"
        duration = result.get("duration_seconds", 0)
        
        console_summary = f"""
# Browser Pilot Test Report

## Test Summary

- **Test Name:** {result.get('test_name', 'Browser Test')}
- **Status:** {status_emoji} {'PASSED' if result.get('success') else 'FAILED'}
- **Duration:** {duration:.2f} seconds
- **Browser:** {result.get('browser', 'Unknown')}
- **Provider:** {result.get('provider', 'Unknown')}/{result.get('model', 'Unknown')}
"""
        
        # Add token usage summary
        if "token_usage" in result and result["token_usage"]:
            usage = result["token_usage"]
            console_summary += f"""
- **Token Usage:** {usage.get('total_tokens', 0):,} tokens
- **Estimated Cost:** ${usage.get('estimated_cost', 0):.4f}
"""
            # Add context usage if available
            if "context_length" in usage and "max_context_length" in usage:
                percentage = usage.get('context_usage_percentage', 0)
                context_emoji = "⚠️" if percentage >= 80 else "⚡" if percentage >= 60 else "✅"
                console_summary += f"- **Context Usage:** {usage.get('context_length', 0):,}/{usage.get('max_context_length', 0):,} tokens ({percentage}%) {context_emoji}\n"
            
            if result.get("provider") == "github_copilot":
                console_summary += "\n> **Note:** Cost estimates for GitHub Copilot are approximate. Actual costs depend on your subscription plan.\n"
        
        # Add error if present
        if result.get("error"):
            console_summary += f"""

## Error Details

{result['error']}
"""
        
        # Add report location
        console_summary += f"""

## Test Session Output

📁 **Session Directory:** `{session_dir}`
📄 **Test Report:** `{report_path}`
"""
        
        print(console_summary)
    
    # Save configuration if requested
    if args.save_config:
        try:
            for key, value in cli_config.items():
                if key not in ["test_scenario", "save_config", "config"]:
                    config.set(key, value)
            stream.write("Configuration saved for future use", "info")
        except Exception as e:
            stream.write(f"Failed to save configuration: {e}", "warning")
    
    # Clean up old files if configured
    if not config.get("quiet"):
        storage.cleanup_old_logs(days=config.get("logs_retention_days"))
        storage.cleanup_old_files("reports", "*.html", days=config.get("reports_retention_days"))
        storage.cleanup_old_files("screenshots", "*.png", days=config.get("screenshots_retention_days"))
    
    return 0 if result.get("success") else 1


def main() -> int:
    """Main entry point for CLI"""
    # Parse arguments
    args = parse_arguments()
    
    # Handle setup wizard
    if args.setup_wizard:
        from .config_wizard import run_config_wizard
        return 0 if run_config_wizard() else 1
    
    # Handle cleanup mode
    if args.cleanup:
        return handle_cleanup(args)
    
    # Check if configuration exists, prompt for wizard if not
    config_manager = ConfigManager()
    if not config_manager.has_config() and not args.provider:
        print("⚠️  No configuration found.\n")
        print("Would you like to run the setup wizard? It takes less than 2 minutes.")
        print("You can also run it anytime with: browser-pilot --setup-wizard\n")
        
        # Simple yes/no prompt (no questionary needed here)
        response = input("Run setup wizard now? [Y/n]: ").strip().lower()
        if response in ['', 'y', 'yes']:
            from .config_wizard import run_config_wizard
            if run_config_wizard():
                print("\n✅ Configuration complete! Continuing with test...\n")
            else:
                print("\n❌ Setup cancelled. Please configure manually or run:")
                print("   browser-pilot --setup-wizard")
                return 1
    
    # Print header only if not quiet
    if not args.quiet:
        print_header()
    
    # Run test
    try:
        exit_code = asyncio.run(run_test_async(args))
    except KeyboardInterrupt:
        if not args.quiet:
            print("\n\n⚠️  Test interrupted by user")
        exit_code = 130  # Standard exit code for SIGINT
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        exit_code = 1
    
    return exit_code


def handle_cleanup(args: argparse.Namespace) -> int:
    """
    Handle cleanup of test outputs
    
    Args:
        args: Command line arguments
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    storage = StorageManager()
    
    print("\n🧹 Browser Pilot Cleanup")
    print("=" * 40)
    
    try:
        # Get sessions directory
        sessions_dir = storage.base_dir / "sessions"
        if not sessions_dir.exists():
            print("✓ No test sessions found to clean up")
            return 0
        
        # Count sessions before cleanup
        all_sessions = list(sessions_dir.iterdir())
        total_sessions = len([d for d in all_sessions if d.is_dir()])
        
        if total_sessions == 0:
            print("✓ No test sessions found to clean up")
            return 0
        
        print(f"Found {total_sessions} test session(s)")
        
        # Clean up sessions older than specified days
        if args.cleanup_days == 0:
            # Clean up all sessions
            print(f"\nRemoving all test sessions...")
            removed_count = 0
            for session_dir in sessions_dir.iterdir():
                if session_dir.is_dir():
                    try:
                        shutil.rmtree(session_dir)
                        removed_count += 1
                        print(f"  ✓ Removed: {session_dir.name}")
                    except Exception as e:
                        print(f"  ✗ Failed to remove {session_dir.name}: {e}")
        else:
            # Clean up old sessions
            print(f"\nRemoving test sessions older than {args.cleanup_days} days...")
            cutoff_time = datetime.now() - timedelta(days=args.cleanup_days)
            removed_count = 0
            
            for session_dir in sessions_dir.iterdir():
                if session_dir.is_dir():
                    # Extract timestamp from directory name (format: test-name_YYYYMMDD_HHMMSS)
                    dir_parts = session_dir.name.rsplit('_', 2)
                    if len(dir_parts) >= 3:
                        try:
                            date_str = dir_parts[-2]
                            time_str = dir_parts[-1]
                            session_time = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                            
                            if session_time < cutoff_time:
                                shutil.rmtree(session_dir)
                                removed_count += 1
                                print(f"  ✓ Removed: {session_dir.name}")
                        except (ValueError, IndexError):
                            # Skip directories with unexpected naming
                            pass
        
        print(f"\n✓ Cleanup complete: removed {removed_count} session(s)")
        
        # Also clean up old files in legacy directories if they exist
        print("\nCleaning up legacy directories...")
        storage.cleanup_old_logs(days=args.cleanup_days)
        storage.cleanup_old_files("reports", "*.*", days=args.cleanup_days)
        storage.cleanup_old_files("screenshots", "*.png", days=args.cleanup_days)
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Cleanup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())