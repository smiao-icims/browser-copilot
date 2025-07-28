"""
CLI package for Browser Copilot

This package contains command-line interface functionality split into focused modules.
"""

import asyncio
import sys

from .commands import (
    run_cleanup_command,
    run_config_command,
    run_storage_info_command,
    run_test_command,
)
from .executor import BrowserTestExecutor
from .parser import create_parser, parse_arguments
from .utils import normalize_test_name_for_path


def main():
    """Main CLI entry point"""
    args = parse_arguments()

    # Handle special commands
    if args.config or args.setup_wizard:
        sys.exit(run_config_command(args))
    elif args.cleanup:
        sys.exit(asyncio.run(run_cleanup_command(args)))
    elif args.storage_info:
        sys.exit(asyncio.run(run_storage_info_command(args)))
    else:
        # Default to test execution
        sys.exit(asyncio.run(run_test_command(args)))


__all__ = [
    "create_parser",
    "parse_arguments",
    "BrowserTestExecutor",
    "run_test_command",
    "run_cleanup_command",
    "run_config_command",
    "run_storage_info_command",
    "normalize_test_name_for_path",
    "main",
]
