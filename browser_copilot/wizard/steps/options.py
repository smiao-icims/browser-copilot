"""Configuration option steps for the wizard."""

import questionary
from questionary import Choice

from browser_copilot.wizard.base import WizardStep
from browser_copilot.wizard.state import WizardState
from browser_copilot.wizard.styles import BROWSER_PILOT_STYLE
from browser_copilot.wizard.types import StepResult, WizardAction


class TestModeStep(WizardStep):
    """Configure test execution mode (headless/headed)."""

    async def execute(self, state: WizardState) -> StepResult:
        """Execute test mode selection."""
        print("\n🖥️  Test Execution Mode\n")

        choices = [
            Choice(title="headless    (Faster, no browser window)", value=True),
            Choice(title="headed      (See browser actions)", value=False),
        ]

        headless = await questionary.select(
            "Default test execution mode:",
            choices=choices,
            default=choices[0],
            use_shortcuts=True,
            use_arrow_keys=True,
            style=BROWSER_PILOT_STYLE,
        ).unsafe_ask_async()

        if headless is None:
            return StepResult(action=WizardAction.BACK, data={})

        return StepResult(action=WizardAction.CONTINUE, data={"headless": headless})

    def can_skip(self, state: WizardState) -> bool:
        """Can be skipped - has default."""
        return True


class TokenOptimizationStep(WizardStep):
    """Configure token optimization level."""

    async def execute(self, state: WizardState) -> StepResult:
        """Execute token optimization selection."""
        print("\n💰 Token Optimization\n")
        print("Reduce API costs by optimizing prompts:\n")

        choices = [
            Choice(title="medium      (Balanced - 20% reduction)", value="medium"),
            Choice(title="high        (Maximum savings - 30% reduction)", value="high"),
            Choice(title="low         (Conservative - 10% reduction)", value="low"),
            Choice(title="none        (No optimization)", value="none"),
        ]

        level = await questionary.select(
            "Token optimization level:",
            choices=choices,
            default=choices[0],
            use_shortcuts=True,
            use_arrow_keys=True,
            style=BROWSER_PILOT_STYLE,
        ).unsafe_ask_async()

        if level is None:
            return StepResult(action=WizardAction.BACK, data={})

        return StepResult(
            action=WizardAction.CONTINUE, data={"compression_level": level}
        )

    def can_skip(self, state: WizardState) -> bool:
        """Can be skipped - has default."""
        return True


class ViewportStep(WizardStep):
    """Configure browser viewport size."""

    VIEWPORT_PRESETS: list[dict[str, str | int | None]] = [
        {"name": "Desktop HD (1920x1080)", "width": 1920, "height": 1080},
        {"name": "Desktop (1366x768)", "width": 1366, "height": 768},
        {"name": "Tablet (1024x768)", "width": 1024, "height": 768},
        {"name": "Mobile (375x812)", "width": 375, "height": 812},
        {"name": "Custom...", "width": None, "height": None},
    ]

    async def execute(self, state: WizardState) -> StepResult:
        """Execute viewport configuration."""
        print("\n📐 Browser Viewport Size\n")

        choices = []
        for preset in self.VIEWPORT_PRESETS:
            if preset["width"]:
                title = f"{preset['name']:<25} ({preset['width']}x{preset['height']})"
            else:
                title = str(preset["name"])
            choices.append(Choice(title=title, value=preset))

        selected = await questionary.select(
            "Default viewport size:",
            choices=choices,
            default=choices[0],
            use_shortcuts=True,
            use_arrow_keys=True,
            style=BROWSER_PILOT_STYLE,
        ).unsafe_ask_async()

        if selected is None:
            return StepResult(action=WizardAction.BACK, data={})

        if selected["width"] is None:
            # Custom size
            width = await questionary.text(
                "Enter viewport width:",
                default="1920",
                validate=lambda x: x.isdigit() or "Please enter a number",
                style=BROWSER_PILOT_STYLE,
            ).unsafe_ask_async()

            if width is None:
                return StepResult(action=WizardAction.BACK, data={})

            height = await questionary.text(
                "Enter viewport height:",
                default="1080",
                validate=lambda x: x.isdigit() or "Please enter a number",
                style=BROWSER_PILOT_STYLE,
            ).unsafe_ask_async()

            if height is None:
                return StepResult(action=WizardAction.BACK, data={})

            return StepResult(
                action=WizardAction.CONTINUE,
                data={"viewport_width": int(width), "viewport_height": int(height)},
            )

        return StepResult(
            action=WizardAction.CONTINUE,
            data={
                "viewport_width": selected["width"],
                "viewport_height": selected["height"],
            },
        )

    def can_skip(self, state: WizardState) -> bool:
        """Can be skipped - has default."""
        return True
