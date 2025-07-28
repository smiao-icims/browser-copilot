"""Welcome step for the configuration wizard."""

import questionary

from browser_copilot.wizard.base import WizardStep
from browser_copilot.wizard.state import WizardState
from browser_copilot.wizard.styles import BROWSER_PILOT_STYLE
from browser_copilot.wizard.types import StepResult, WizardAction


class WelcomeStep(WizardStep):
    """Display welcome message and introduction."""

    async def execute(self, state: WizardState) -> StepResult:
        """Display welcome screen."""
        # ASCII art banner
        banner = """
╔═══════════════════════════════════════════╗
║      🎯 Browser Copilot Setup Wizard      ║
║   Simple • Reliable • Token Efficient     ║
╚═══════════════════════════════════════════╝
        """

        print(banner)
        print(
            "This wizard will help you set up Browser Copilot in less than 2 minutes."
        )
        print(
            "You can press Enter to accept defaults or use arrow keys to change selections."
        )
        print("\n💡 Tip: Press Ctrl+C at any time to exit the wizard")
        print()

        # Ask if user wants to continue
        continue_setup = await questionary.confirm(
            "Ready to begin setup?", default=True, style=BROWSER_PILOT_STYLE
        ).unsafe_ask_async()

        if not continue_setup:
            return StepResult(action=WizardAction.CANCEL, data={})

        return StepResult(action=WizardAction.CONTINUE, data={})

    def can_skip(self, state: WizardState) -> bool:
        """Welcome step cannot be skipped."""
        return False
