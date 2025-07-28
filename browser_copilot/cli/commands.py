"""
Command handlers for Browser Copilot CLI

Contains functions that handle different CLI commands.
"""

import sys
from pathlib import Path

from ..config_manager import ConfigManager
from ..config_wizard import run_config_wizard
from ..io import InputHandler, StreamHandler
from ..reporter import print_header
from ..storage_manager import StorageManager
from .executor import BrowserTestExecutor
from .utils import read_system_prompt


async def run_test_command(args) -> int:
    """
    Handle the main test execution command

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Initialize storage and config
    storage = StorageManager()
    config = ConfigManager(storage_manager=storage)
    config.set_cli_args(vars(args))

    # Initialize stream handler
    stream = StreamHandler(verbose=args.verbose, quiet=args.quiet)

    # Display header unless quiet
    if not args.quiet:
        print_header()

    # Read test scenario
    try:
        if args.test_scenario == "-":
            test_content = InputHandler.read_from_stdin()
        else:
            test_path = Path(args.test_scenario)
            test_content = InputHandler.read_from_file(test_path)
    except Exception as e:
        stream.write(f"Failed to read test scenario: {e}", "error")
        return 1

    # Validate test scenario
    warnings = InputHandler.validate_scenario(test_content)
    for warning in warnings:
        stream.write(f"Warning: {warning}", "warning")

    # Read system prompt if provided
    system_prompt = None
    if args.system_prompt:
        try:
            system_prompt = read_system_prompt(args.system_prompt)
        except Exception as e:
            stream.write(f"Failed to read system prompt: {e}", "error")
            return 1

    # Save configuration if requested
    if hasattr(args, "save_config") and args.save_config:
        # TODO: Implement save_defaults method in ConfigManager
        stream.write("Configuration save requested (not yet implemented)", "info")

    # Build playwright kwargs
    playwright_kwargs = {
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

    # Remove None values
    playwright_kwargs = {k: v for k, v in playwright_kwargs.items() if v is not None}

    # Execute test
    executor = BrowserTestExecutor(config, storage, stream)

    try:
        result = await executor.execute_test(
            test_content,
            system_prompt=system_prompt,
            enhance_test=args.enhance_test,
            playwright_kwargs=playwright_kwargs,
        )
    except Exception as e:
        stream.write(f"Test execution failed: {e}", "error")
        if config.get("verbose"):
            import traceback

            stream.write(traceback.format_exc(), "debug")
        return 1

    # Save results
    output_format = args.output_format or "markdown"
    saved_files = executor.save_results(result, output_format, args.output_file)

    # Display summary
    executor.display_summary(result, args.quiet)

    # Log saved files
    if not args.quiet:
        for file_type, file_path in saved_files.items():
            stream.write(f"{file_type.title()} saved to: {file_path}", "info")

    # Return exit code based on test success
    return 0 if result.get("success") else 1


async def run_cleanup_command(args) -> int:
    """
    Handle the cleanup command

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        storage = StorageManager()

        if not args.quiet:
            print(f"\n🧹 Cleaning up files older than {args.cleanup_days} days...\n")

        # Perform cleanup
        deleted_count = storage.cleanup_old_logs(days=args.cleanup_days)
        deleted_count += storage.cleanup_old_files(
            storage.get_cache_dir(), days=args.cleanup_days
        )
        deleted_count += storage.cleanup_old_files(
            storage.get_screenshots_dir(), days=args.cleanup_days
        )

        if not args.quiet:
            print(f"✅ Cleaned up {deleted_count} old files\n")

        # Show storage info if requested
        if args.storage_info:
            await run_storage_info_command(args)

        return 0
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}", file=sys.stderr)
        return 1


def run_config_command(args) -> int:
    """
    Handle the configuration wizard command

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    try:
        run_config_wizard()
        return 0
    except KeyboardInterrupt:
        print("\n\n❌ Configuration wizard cancelled")
        return 1
    except Exception as e:
        print(f"\n❌ Configuration failed: {e}")
        return 1


async def run_storage_info_command(args) -> int:
    """
    Display storage information

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        storage = StorageManager()
        info = storage.get_storage_info()

        print("\n📊 Storage Information\n")
        print(f"Base directory: {storage.base_dir}")
        print(f"Total size: {storage._format_bytes(info['total_size'])}\n")

        print("Directory sizes:")
        for dir_name, size in info["directories"].items():
            print(f"  {dir_name}: {storage._format_bytes(size)}")

        print("\nFile counts:")
        print(f"  Logs: {info['file_counts']['logs']}")
        print(f"  Reports: {info['file_counts']['reports']}")
        print(f"  Screenshots: {info['file_counts']['screenshots']}")
        print(f"  Cache files: {info['file_counts']['cache']}")
        print(f"  Settings: {info['file_counts']['settings']}")
        print()

        return 0
    except Exception as e:
        print(f"\n❌ Storage info failed: {e}", file=sys.stderr)
        return 1
