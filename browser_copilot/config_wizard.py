"""Configuration wizard for Browser Copilot."""

import asyncio
import sys

from browser_copilot.wizard import WizardFlow


def run_config_wizard() -> bool:
    """
    Run the configuration wizard.

    Returns:
        bool: True if configuration was saved successfully, False otherwise.
    """
    try:
        # Check if we're in an async environment
        try:
            asyncio.get_running_loop()
            # Already in async context
            print(
                "⚠️  Cannot run wizard in async context. Please run from command line."
            )
            return False
        except RuntimeError:
            # No running loop, good to go
            pass

        # Create and run wizard
        wizard = WizardFlow()
        result = asyncio.run(wizard.run())

        return result.success

    except KeyboardInterrupt:
        print("\n\n👋 Setup wizard cancelled.")
        return False
    except Exception as e:
        print(f"\n\n❌ Error running wizard: {e}")
        return False


def main() -> None:
    """Entry point for standalone wizard execution."""
    success = run_config_wizard()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
