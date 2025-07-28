"""Wizard steps."""

from browser_pilot.wizard.steps.welcome import WelcomeStep
from browser_pilot.wizard.steps.completion import CompletionStep
from browser_pilot.wizard.steps.provider import ProviderSelectionStep
from browser_pilot.wizard.steps.model import ModelSelectionStep
from browser_pilot.wizard.steps.browser import BrowserSelectionStep
from browser_pilot.wizard.steps.options import (
    TestModeStep,
    TokenOptimizationStep,
    ViewportStep,
)
from browser_pilot.wizard.steps.validation import ValidationStep
from browser_pilot.wizard.steps.save import SaveConfigurationStep

__all__ = [
    "WelcomeStep",
    "CompletionStep",
    "ProviderSelectionStep",
    "ModelSelectionStep",
    "BrowserSelectionStep",
    "TestModeStep",
    "TokenOptimizationStep",
    "ViewportStep",
    "ValidationStep",
    "SaveConfigurationStep",
]