"""Completion step for the configuration wizard."""

from browser_copilot.wizard.base import WizardStep
from browser_copilot.wizard.state import WizardState
from browser_copilot.wizard.types import StepResult, WizardAction


class CompletionStep(WizardStep):
    """Display completion message and next steps."""

    async def execute(self, state: WizardState) -> StepResult:
        """Display completion screen."""
        print("\n🎉 Setup Complete!\n")

        # Show configuration summary
        print("Configuration Summary:")
        print("━" * 50)
        print(f"Provider:        {state.provider}")
        print(f"Model:           {state.model}")
        print(f"Browser:         {state.browser}")
        print(f"Mode:            {'headless' if state.headless else 'headed'}")
        print(f"Optimization:    {state.compression_level}")
        print("━" * 50)
        print()

        print("You're ready to start testing. Try:\n")
        print("1. Run an example:")
        print("   browser-copilot examples/google-ai-search.md")
        print()
        print("2. Create your own test:")
        print(
            '   echo "Navigate to example.com and verify the title" | browser-copilot -'
        )
        print()
        print("Need help? Run: browser-copilot --help")
        print()

        return StepResult(action=WizardAction.CONTINUE, data={})

    def can_skip(self, state: WizardState) -> bool:
        """Completion step cannot be skipped."""
        return False
