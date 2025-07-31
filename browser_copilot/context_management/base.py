"""
Base classes and interfaces for context management
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol


class MessageType(Enum):
    """Types of messages in the conversation"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    ERROR = "error"


class MessageImportance(Enum):
    """Importance levels for messages"""

    CRITICAL = "critical"  # Errors, essential context
    HIGH = "high"  # Tool responses, key decisions
    MEDIUM = "medium"  # Agent reasoning
    LOW = "low"  # Verbose output


@dataclass
class Message:
    """Represents a message in the conversation context"""

    type: MessageType
    content: str
    timestamp: datetime
    importance: MessageImportance = MessageImportance.MEDIUM
    token_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    # Tool-specific fields
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None

    # Preservation flags
    preserve: bool = False  # Force preservation
    mergeable: bool = True  # Can be merged with similar messages

    def __post_init__(self):
        """Set importance based on type if not provided"""
        # Only auto-set importance if it wasn't explicitly set
        if self.type == MessageType.ERROR:
            self.importance = MessageImportance.CRITICAL
        elif (
            self.type in (MessageType.TOOL_RESPONSE, MessageType.SYSTEM)
            and self.importance == MessageImportance.MEDIUM
        ):
            self.importance = MessageImportance.HIGH
        elif (
            self.type == MessageType.TOOL_CALL
            and self.importance == MessageImportance.MEDIUM
        ):
            self.importance = MessageImportance.HIGH


@dataclass
class ContextConfig:
    """Configuration for context management"""

    max_tokens: int = 100000  # Maximum context size
    preserve_window: int = 10  # Number of recent messages to always preserve
    compression_level: str = "medium"  # low, medium, high

    # Sliding window config
    window_size: int = 25000  # Target window size in tokens
    overlap_size: int = 10000  # Overlap between windows

    # Preservation rules
    preserve_errors: bool = True
    preserve_screenshots: bool = True
    preserve_first_n: int = (
        2  # Always keep first N messages (typically 1 system + 1 human)
    )
    preserve_last_n: int = 10  # Always keep last N messages

    # Compression config
    enable_compression: bool = True
    compress_snapshots: bool = True
    compress_console: bool = True
    max_snapshot_elements: int = 100

    # Importance thresholds
    importance_weights: dict[MessageImportance, float] = field(
        default_factory=lambda: {
            MessageImportance.CRITICAL: 1.0,
            MessageImportance.HIGH: 0.8,
            MessageImportance.MEDIUM: 0.5,
            MessageImportance.LOW: 0.2,
        }
    )


class ContextStrategy(Protocol):
    """Protocol for context management strategies"""

    def process_messages(
        self, messages: list[Message], config: ContextConfig
    ) -> list[Message]:
        """Process messages according to the strategy"""
        ...

    def get_metrics(self) -> dict[str, Any]:
        """Get strategy-specific metrics"""
        ...


class ContextManager(ABC):
    """Abstract base class for context managers"""

    def __init__(self, config: ContextConfig):
        self.config = config
        self._messages: list[Message] = []
        self._total_tokens = 0

    @abstractmethod
    def add_message(self, message: Message) -> None:
        """Add a message to the context"""
        pass

    @abstractmethod
    def get_context(self) -> list[Message]:
        """Get the current context after processing"""
        pass

    @abstractmethod
    def get_metrics(self) -> dict[str, Any]:
        """Get context management metrics"""
        pass

    def reset(self) -> None:
        """Reset the context manager"""
        self._messages.clear()
        self._total_tokens = 0
