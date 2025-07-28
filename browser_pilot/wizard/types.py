"""Type definitions for the configuration wizard."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class WizardAction(Enum):
    """Actions that can be taken after a wizard step."""

    CONTINUE = "continue"
    BACK = "back"
    CANCEL = "cancel"
    RETRY = "retry"


@dataclass
class StepResult:
    """Result from executing a wizard step."""

    action: WizardAction
    data: dict[str, Any]
    error: str | None = None
