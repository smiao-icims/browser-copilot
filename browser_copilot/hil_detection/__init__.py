"""Human-in-the-Loop detection and handling for Browser Copilot."""

from .detector import HILDetector
from .handler import SmartHILHandler
from .hooks import create_hil_post_hook

__all__ = [
    "HILDetector",
    "SmartHILHandler", 
    "create_hil_post_hook",
]