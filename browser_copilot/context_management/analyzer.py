"""
Message analysis utilities for context management
"""

import re

import tiktoken

from .base import Message, MessageImportance, MessageType


class MessageAnalyzer:
    """Analyzes messages for token counting and importance scoring"""

    def __init__(self, model: str = "gpt-4"):
        """
        Initialize the analyzer with a specific model's tokenizer

        Args:
            model: Model name for token counting (defaults to gpt-4)
        """
        # Try to get the exact encoding for the model
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fall back to cl100k_base which is used by GPT-4 and GPT-3.5-turbo
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))

    def analyze_message(self, message: Message) -> Message:
        """
        Analyze a message and update its properties

        Args:
            message: Message to analyze

        Returns:
            Updated message with token count and importance
        """
        # Count tokens if not already set
        if message.token_count == 0:
            message.token_count = self.count_tokens(message.content)

        # Analyze importance based on content patterns
        if message.importance == MessageImportance.MEDIUM:
            message.importance = self._determine_importance(message)

        return message

    def _determine_importance(self, message: Message) -> MessageImportance:
        """
        Determine message importance based on content and type

        Args:
            message: Message to analyze

        Returns:
            Determined importance level
        """
        content_lower = message.content.lower()

        # Critical patterns
        critical_patterns = [
            r"\berror\b",
            r"\bfailed\b",
            r"\bexception\b",
            r"\bcrash\b",
            r"\bcritical\b",
            r"\bfatal\b",
        ]

        # High importance patterns
        high_patterns = [
            r"\bwarning\b",
            r"\bscreenshot\b",
            r"\bnavigat",
            r"\bclick",
            r"\btype",
            r"\bform",
            r"\bsubmit",
            r"\btest\s+(passed|failed)",
            r"\bverif",
            r"\bassert",
        ]

        # Check critical patterns
        for pattern in critical_patterns:
            if re.search(pattern, content_lower):
                return MessageImportance.CRITICAL

        # Check high importance patterns
        for pattern in high_patterns:
            if re.search(pattern, content_lower):
                return MessageImportance.HIGH

        # Tool responses are generally high importance
        if message.type == MessageType.TOOL_RESPONSE:
            # Unless it's just a navigation confirmation
            if not re.search(r"navigated to|page loaded", content_lower):
                return MessageImportance.HIGH

        # Long agent messages might be important summaries
        if message.type == MessageType.ASSISTANT and len(message.content) > 500:
            return MessageImportance.HIGH

        return MessageImportance.MEDIUM

    def get_content_type(self, message: Message) -> str:
        """
        Determine the content type of a message

        Args:
            message: Message to analyze

        Returns:
            Content type (e.g., 'snapshot', 'console', 'navigation', 'interaction')
        """
        if message.tool_name:
            tool_map = {
                "browser_snapshot": "snapshot",
                "browser_console_messages": "console",
                "browser_navigate": "navigation",
                "browser_click": "interaction",
                "browser_type": "interaction",
                "browser_take_screenshot": "screenshot",
            }
            return tool_map.get(message.tool_name, "tool_response")

        content_lower = message.content.lower()

        # Detect content types by patterns
        if "snapshot" in content_lower or "dom tree" in content_lower:
            return "snapshot"
        elif "console" in content_lower:
            return "console"
        elif "navigat" in content_lower:
            return "navigation"
        elif any(
            word in content_lower for word in ["click", "type", "submit", "select"]
        ):
            return "interaction"
        elif "error" in content_lower or "fail" in content_lower:
            return "error"

        return "general"


class ImportanceScorer:
    """Scores message importance for pruning decisions"""

    def __init__(self):
        self.score_weights = {
            MessageImportance.CRITICAL: 1.0,
            MessageImportance.HIGH: 0.7,
            MessageImportance.MEDIUM: 0.4,
            MessageImportance.LOW: 0.1,
        }

    def score_message(
        self, message: Message, context: list[Message] | None = None
    ) -> float:
        """
        Calculate importance score for a message

        Args:
            message: Message to score
            context: Optional context of surrounding messages

        Returns:
            Score between 0.0 and 1.0
        """
        # Base score from importance level
        base_score = self.score_weights.get(message.importance, 0.5)

        # Boost score for recent messages (recency bias)
        # This would need timestamp comparison with current time
        recency_boost = 0.0

        # Boost score for messages with errors
        error_boost = 0.2 if message.type == MessageType.ERROR else 0.0

        # Boost score for tool responses
        tool_boost = 0.1 if message.type == MessageType.TOOL_RESPONSE else 0.0

        # Penalty for very long messages (they take up more space)
        length_penalty = 0.0
        if message.token_count > 2000:
            length_penalty = -0.2
        elif message.token_count > 1000:
            length_penalty = -0.1

        # Calculate final score (clamped to 0-1)
        final_score = (
            base_score + recency_boost + error_boost + tool_boost + length_penalty
        )
        return max(0.0, min(1.0, final_score))
