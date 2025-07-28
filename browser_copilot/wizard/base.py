"""Base classes for wizard steps."""

from abc import ABC, abstractmethod

from browser_copilot.wizard.state import WizardState
from browser_copilot.wizard.types import StepResult


class WizardStep(ABC):
    """Base class for all wizard steps."""

    @abstractmethod
    async def execute(self, state: WizardState) -> StepResult:
        """Execute this wizard step."""
        pass

    @abstractmethod
    def can_skip(self, state: WizardState) -> bool:
        """Check if this step can be skipped."""
        pass

    def get_name(self) -> str:
        """Get the name of this step."""
        return self.__class__.__name__.replace("Step", "")
