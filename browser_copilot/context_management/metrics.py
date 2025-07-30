"""
Metrics tracking for context management
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class ContextMetrics:
    """Metrics for context management operations"""

    # Token metrics
    original_tokens: int = 0
    processed_tokens: int = 0
    tokens_saved: int = 0
    reduction_percentage: float = 0.0

    # Message metrics
    original_messages: int = 0
    processed_messages: int = 0
    messages_removed: int = 0
    messages_compressed: int = 0
    messages_merged: int = 0

    # Strategy-specific metrics
    strategy_name: str = ""
    processing_time_ms: float = 0.0

    # Window metrics (for sliding window)
    window_size: int | None = None
    windows_created: int = 0
    overlap_size: int | None = None

    # Preservation metrics
    messages_preserved: int = 0
    critical_messages_kept: int = 0

    # Performance metrics
    avg_message_tokens: float = 0.0
    max_message_tokens: int = 0

    # Timestamp
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def calculate_savings(self) -> None:
        """Calculate derived metrics"""
        if self.original_tokens > 0:
            self.tokens_saved = self.original_tokens - self.processed_tokens
            self.reduction_percentage = (self.tokens_saved / self.original_tokens) * 100

        if self.original_messages > 0:
            self.messages_removed = self.original_messages - self.processed_messages
            self.avg_message_tokens = self.original_tokens / self.original_messages

    def to_dict(self) -> dict:
        """Convert metrics to dictionary for reporting"""
        return {
            "strategy": self.strategy_name,
            "token_metrics": {
                "original": self.original_tokens,
                "processed": self.processed_tokens,
                "saved": self.tokens_saved,
                "reduction_percentage": round(self.reduction_percentage, 1),
            },
            "message_metrics": {
                "original": self.original_messages,
                "processed": self.processed_messages,
                "removed": self.messages_removed,
                "compressed": self.messages_compressed,
                "merged": self.messages_merged,
                "preserved": self.messages_preserved,
            },
            "performance": {
                "processing_time_ms": round(self.processing_time_ms, 2),
                "avg_message_tokens": round(self.avg_message_tokens, 1),
                "max_message_tokens": self.max_message_tokens,
            },
            "timestamp": self.timestamp.isoformat(),
        }
