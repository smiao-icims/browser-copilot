"""Main wizard flow orchestrator."""

from dataclasses import dataclass

try:
    import questionary
except ImportError:
    print("❌ Questionary not installed. Please run: pip install questionary")
    raise

from browser_copilot.wizard.state import WizardState
from browser_copilot.wizard.steps import (
    BrowserSelectionStep,
    CompletionStep,
    ModelSelectionStep,
    ProviderSelectionStep,
    SaveConfigurationStep,
    TestModeStep,
    TokenOptimizationStep,
    ValidationStep,
    ViewportStep,
    WelcomeStep,
)
from browser_copilot.wizard.steps.authentication import AuthenticationStep
from browser_copilot.wizard.styles import BROWSER_PILOT_STYLE
from browser_copilot.wizard.types import StepResult, WizardAction


@dataclass
class WizardResult:
    """Result from running the wizard."""

    success: bool
    config: dict | None = None
    error: str | None = None


class WizardFlow:
    """Main orchestrator for the configuration wizard."""

    def __init__(self):
        """Initialize the wizard flow."""
        self.state = WizardState()
        self.steps = [
            WelcomeStep(),
            ProviderSelectionStep(),
            ModelSelectionStep(),
            AuthenticationStep(),
            BrowserSelectionStep(),
            TestModeStep(),
            TokenOptimizationStep(),
            ViewportStep(),
            ValidationStep(),
            SaveConfigurationStep(),
            CompletionStep(),
        ]
        self.current_step_index = 0

    async def run(self) -> WizardResult:
        """Execute the wizard flow."""
        try:
            while self.current_step_index < len(self.steps):
                step = self.steps[self.current_step_index]

                # Skip if step can be skipped
                if step.can_skip(self.state):
                    self.current_step_index += 1
                    continue

                # Show progress
                self._show_progress()

                # Execute step
                result = await self._execute_step(step)

                # Handle result
                if result.action == WizardAction.CANCEL:
                    return await self._handle_cancel()
                elif result.action == WizardAction.BACK:
                    self._handle_back()
                elif result.action == WizardAction.RETRY:
                    # Retry same step
                    continue
                else:
                    # Update state and continue
                    self.state.update(result.data)
                    self.state.current_step = self.current_step_index
                    self.current_step_index += 1

            # Wizard completed successfully
            return WizardResult(success=True, config=self.state.to_config())

        except KeyboardInterrupt:
            print("\n\n⚠️  Wizard interrupted")
            return await self._handle_cancel()
        except Exception as e:
            print(f"\n\n❌ Wizard error: {e}")
            return WizardResult(success=False, error=str(e))

    async def _execute_step(self, step) -> StepResult:
        """Execute a single wizard step."""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                result = await step.execute(self.state)
                return result
            except Exception as e:
                retry_count += 1
                print(f"\n⚠️  Step failed: {e}")

                if retry_count < max_retries:
                    retry = await questionary.confirm(
                        "Try again?", default=True, style=BROWSER_PILOT_STYLE
                    ).unsafe_ask_async()

                    if not retry:
                        return StepResult(action=WizardAction.CANCEL, data={})
                else:
                    print("❌ Maximum retries exceeded")
                    return StepResult(action=WizardAction.CANCEL, data={})

        return StepResult(action=WizardAction.CANCEL, data={})

    def _show_progress(self):
        """Show progress indicator."""
        total = len([s for s in self.steps if not s.can_skip(self.state)])
        current = self.current_step_index + 1

        # Don't show progress for welcome/completion steps
        step_name = self.steps[self.current_step_index].get_name()
        if step_name in ["Welcome", "Completion"]:
            return

        print("\n" + "━" * 50)
        print(f"Step {current} of {total}: {step_name}")
        print("━" * 50)

    def _handle_back(self):
        """Handle going back to previous step."""
        # Find previous non-skippable step
        self.current_step_index = max(0, self.current_step_index - 1)
        while self.current_step_index > 0:
            step = self.steps[self.current_step_index]
            if not step.can_skip(self.state):
                break
            self.current_step_index -= 1

        # Restore state from history if available
        if self.current_step_index < len(self.state.history):
            self.state.restore_from_history(self.current_step_index)

    async def _handle_cancel(self) -> WizardResult:
        """Handle wizard cancellation."""
        confirm = await questionary.confirm(
            "\nAre you sure you want to exit the wizard?",
            default=False,
            style=BROWSER_PILOT_STYLE,
        ).unsafe_ask_async()

        if confirm:
            print("\n👋 Setup wizard cancelled. You can run it again with:")
            print("   browser-copilot --setup-wizard")
            return WizardResult(success=False, error="User cancelled")
        else:
            # Continue from current step
            return await self.run()


async def run_wizard() -> WizardResult:
    """Convenience function to run the wizard."""
    wizard = WizardFlow()
    return await wizard.run()
