"""
Token Optimization Module for Browser Copilot

Implements strategies to reduce token usage and costs while maintaining test reliability.
"""

import re
from enum import Enum
from typing import Any

try:
    from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

    LANGCHAIN_AVAILABLE = True
except ImportError:
    # For testing without langchain
    LANGCHAIN_AVAILABLE = False
    BaseMessage = Any  # type: ignore[misc,assignment]
    HumanMessage = Any  # type: ignore[misc,assignment]
    SystemMessage = Any  # type: ignore[misc,assignment]


class OptimizationLevel(Enum):
    """Token optimization levels"""

    NONE = "none"
    LOW = "low"  # Basic optimizations, ~10% reduction
    MEDIUM = "medium"  # Moderate optimizations, ~20% reduction
    HIGH = "high"  # Aggressive optimizations, ~30% reduction


class TokenOptimizer:
    """Optimizes prompts and contexts to reduce token usage"""

    # Common words to remove in aggressive optimization
    FILLER_WORDS = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "up",
        "about",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "under",
        "since",
        "without",
        "within",
        "along",
        "following",
        "across",
        "behind",
        "beyond",
        "plus",
        "except",
        "versus",
        "via",
    }

    # Replacements for common phrases
    PHRASE_REPLACEMENTS = {
        # Verbose -> Concise
        "navigate to": "goto",
        "click on": "click",
        "press the": "press",
        "enter text": "type",
        "verify that": "check",
        "ensure that": "check",
        "wait for": "wait",
        "should be": "=",
        "should contain": "contains",
        "should not": "!=",
        "is equal to": "=",
        "is not equal to": "!=",
        "greater than": ">",
        "less than": "<",
        "and then": "then",
        "after that": "then",
        "in order to": "to",
        "make sure": "ensure",
        "at this point": "now",
        "it is necessary to": "must",
        "it is important to": "must",
        "please note that": "note:",
        "keep in mind": "remember:",
    }

    def __init__(self, level: OptimizationLevel = OptimizationLevel.MEDIUM):
        """
        Initialize TokenOptimizer

        Args:
            level: Optimization level to use
        """
        self.level = level
        self.metrics: dict[str, Any] = {
            "original_tokens": 0,
            "optimized_tokens": 0,
            "reduction_percentage": 0.0,
            "strategies_applied": [],
        }

    def optimize_prompt(self, prompt: str) -> str:
        """
        Optimize a text prompt based on the configured level

        Args:
            prompt: Original prompt text

        Returns:
            Optimized prompt
        """
        if self.level == OptimizationLevel.NONE:
            return prompt

        original_length = len(prompt.split())
        optimized = prompt
        strategies = []

        # Apply optimizations based on level
        if self.level in [
            OptimizationLevel.LOW,
            OptimizationLevel.MEDIUM,
            OptimizationLevel.HIGH,
        ]:
            optimized = self._remove_extra_whitespace(optimized)
            optimized = self._simplify_punctuation(optimized)
            strategies.extend(["whitespace", "punctuation"])

        if self.level in [OptimizationLevel.MEDIUM, OptimizationLevel.HIGH]:
            optimized = self._replace_common_phrases(optimized)
            optimized = self._remove_redundant_words(optimized)
            optimized = self._simplify_numbers(optimized)
            strategies.extend(["phrases", "redundancy", "numbers"])

        if self.level == OptimizationLevel.HIGH:
            optimized = self._remove_filler_words(optimized)
            optimized = self._abbreviate_common_terms(optimized)
            optimized = self._compress_instructions(optimized)
            strategies.extend(["fillers", "abbreviations", "compression"])

        # Update metrics
        optimized_length = len(optimized.split())
        self._update_metrics(original_length, optimized_length, strategies)

        return optimized

    def optimize_messages(self, messages: list[BaseMessage]) -> list[BaseMessage]:
        """
        Optimize a list of LangChain messages

        Args:
            messages: List of messages to optimize

        Returns:
            Optimized messages
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain is required for message optimization")

        if self.level == OptimizationLevel.NONE:
            return messages

        optimized_messages: list[BaseMessage] = []

        for message in messages:
            if isinstance(message, HumanMessage | SystemMessage):
                optimized_content = self.optimize_prompt(str(message.content))
                optimized_message = type(message)(content=optimized_content)
                optimized_messages.append(optimized_message)
            else:
                optimized_messages.append(message)

        return optimized_messages

    def optimize_context(
        self, context: str, max_length: int = 4000, preserve_recent: int = 1000
    ) -> str:
        """
        Optimize context by intelligently truncating while preserving important information

        Args:
            context: Full context string
            max_length: Maximum allowed length in characters
            preserve_recent: Number of recent characters to always preserve

        Returns:
            Optimized context
        """
        if len(context) <= max_length:
            return self.optimize_prompt(context)

        # Split into sections
        lines = context.split("\n")

        # Preserve recent content
        recent_content = (
            context[-preserve_recent:] if len(context) > preserve_recent else context
        )
        remaining_space = max_length - len(recent_content)

        # Prioritize content
        prioritized_lines = self._prioritize_content(lines, remaining_space)

        # Combine and optimize
        optimized = "\n".join(prioritized_lines) + "\n...\n" + recent_content
        return self.optimize_prompt(optimized)

    def get_metrics(self) -> dict[str, Any]:
        """
        Get optimization metrics

        Returns:
            Dictionary of metrics
        """
        return self.metrics.copy()

    def estimate_cost_savings(
        self,
        original_tokens: int,
        optimized_tokens: int,
        cost_per_1k_tokens: float = 0.002,
    ) -> dict[str, float]:
        """
        Estimate cost savings from optimization

        Args:
            original_tokens: Original token count
            optimized_tokens: Optimized token count
            cost_per_1k_tokens: Cost per 1000 tokens

        Returns:
            Cost analysis
        """
        original_cost = (original_tokens / 1000) * cost_per_1k_tokens
        optimized_cost = (optimized_tokens / 1000) * cost_per_1k_tokens
        savings = original_cost - optimized_cost
        savings_percentage = (savings / original_cost * 100) if original_cost > 0 else 0

        return {
            "original_cost": original_cost,
            "optimized_cost": optimized_cost,
            "savings": savings,
            "savings_percentage": savings_percentage,
        }

    def _remove_extra_whitespace(self, text: str) -> str:
        """Remove unnecessary whitespace"""
        # Multiple spaces to single space
        text = re.sub(r"\s+", " ", text)
        # Remove space before punctuation
        text = re.sub(r"\s+([.,;!?])", r"\1", text)
        # Remove trailing whitespace
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        return text.strip()

    def _simplify_punctuation(self, text: str) -> str:
        """Simplify punctuation usage"""
        # Multiple punctuation to single
        text = re.sub(r"([.!?]){2,}", r"\1", text)
        # Remove unnecessary quotes in simple cases
        text = re.sub(r'"(\w+)"', r"\1", text)
        return text

    def _replace_common_phrases(self, text: str) -> str:
        """Replace verbose phrases with concise versions"""
        for verbose, concise in self.PHRASE_REPLACEMENTS.items():
            text = re.sub(r"\b" + verbose + r"\b", concise, text, flags=re.IGNORECASE)
        return text

    def _remove_redundant_words(self, text: str) -> str:
        """Remove obviously redundant words"""
        # Remove "very", "really", "quite" before adjectives
        text = re.sub(
            r"\b(very|really|quite|extremely)\s+", "", text, flags=re.IGNORECASE
        )
        # Remove "please" in instructions
        text = re.sub(r"\bplease\s+", "", text, flags=re.IGNORECASE)
        return text

    def _simplify_numbers(self, text: str) -> str:
        """Simplify number representations"""
        # "1,000" -> "1000"
        text = re.sub(r"(\d),(\d{3})", r"\1\2", text)
        # "first" -> "1st", "second" -> "2nd", etc.
        ordinals = {
            "first": "1st",
            "second": "2nd",
            "third": "3rd",
            "fourth": "4th",
            "fifth": "5th",
            "sixth": "6th",
            "seventh": "7th",
            "eighth": "8th",
            "ninth": "9th",
            "tenth": "10th",
        }
        for word, num in ordinals.items():
            text = re.sub(r"\b" + word + r"\b", num, text, flags=re.IGNORECASE)
        return text

    def _remove_filler_words(self, text: str) -> str:
        """Remove filler words (aggressive optimization)"""
        words = text.split()
        filtered_words = []

        for i, word in enumerate(words):
            # Keep if not a filler word or if it's critical for meaning
            if word.lower() not in self.FILLER_WORDS or self._is_critical_context(
                words, i
            ):
                filtered_words.append(word)

        return " ".join(filtered_words)

    def _is_critical_context(self, words: list[str], index: int) -> bool:
        """Check if a word is critical in its context"""
        # Keep articles before specific elements/selectors
        if index < len(words) - 1:
            next_word = words[index + 1]
            if next_word.startswith(("#", ".", "[", "button", "input", "link")):
                return True
        return False

    def _abbreviate_common_terms(self, text: str) -> str:
        """Abbreviate common technical terms"""
        abbreviations = {
            "button": "btn",
            "navigation": "nav",
            "password": "pwd",
            "username": "user",
            "email address": "email",
            "telephone": "tel",
            "number": "num",
            "message": "msg",
            "description": "desc",
            "configuration": "config",
            "information": "info",
            "administrator": "admin",
        }

        for full, abbr in abbreviations.items():
            text = re.sub(r"\b" + full + r"\b", abbr, text, flags=re.IGNORECASE)

        return text

    def _compress_instructions(self, text: str) -> str:
        """Compress instruction patterns"""
        # "Step 1: Navigate to..." -> "1. Navigate to..."
        text = re.sub(r"Step (\d+):\s*", r"\1. ", text)
        # Remove obvious instruction prefixes
        text = re.sub(
            r"^(You should|You must|You need to)\s+",
            "",
            text,
            flags=re.MULTILINE | re.IGNORECASE,
        )
        return text

    def _prioritize_content(self, lines: list[str], max_chars: int) -> list[str]:
        """Prioritize content lines based on importance"""
        prioritized = []
        current_length = 0

        # Priority patterns (higher score = higher priority)
        priority_patterns = [
            (r"error|fail|issue|problem", 10),
            (r"test|verify|check|assert", 8),
            (r"click|type|enter|select", 7),
            (r"navigate|goto|visit", 6),
            (r"#|\.|\[.*\]", 5),  # Selectors
            (r"http[s]?://|www\.", 4),  # URLs
            (r"\d+", 2),  # Numbers
        ]

        # Score each line
        scored_lines = []
        for line in lines:
            score = 1  # Base score
            for pattern, weight in priority_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    score += weight
            scored_lines.append((score, line))

        # Sort by score and add until space runs out
        scored_lines.sort(reverse=True, key=lambda x: x[0])

        for score, line in scored_lines:
            line_length = len(line) + 1  # +1 for newline
            if current_length + line_length <= max_chars:
                prioritized.append(line)
                current_length += line_length
            else:
                break

        return prioritized

    def _update_metrics(
        self, original: int, optimized: int, strategies: list[str]
    ) -> None:
        """Update optimization metrics"""
        self.metrics["original_tokens"] += original
        self.metrics["optimized_tokens"] += optimized

        if original > 0:
            reduction = ((original - optimized) / original) * 100
            # Running average
            if self.metrics["reduction_percentage"] == 0:
                self.metrics["reduction_percentage"] = reduction
            else:
                self.metrics["reduction_percentage"] = (
                    self.metrics["reduction_percentage"] + reduction
                ) / 2

        # Track unique strategies
        for strategy in strategies:
            strategies_list = self.metrics["strategies_applied"]
            if isinstance(strategies_list, list) and strategy not in strategies_list:
                strategies_list.append(strategy)


class OptimizationPresets:
    """Predefined optimization configurations for different scenarios"""

    @staticmethod
    def get_preset(scenario: str) -> dict[str, Any]:
        """
        Get optimization preset for a scenario

        Args:
            scenario: Scenario name (e.g., "quick_test", "detailed_debug", "cost_sensitive")

        Returns:
            Preset configuration
        """
        presets = {
            "quick_test": {
                "level": OptimizationLevel.HIGH,
                "max_context": 2000,
                "preserve_recent": 500,
                "skip_screenshots": True,
            },
            "detailed_debug": {
                "level": OptimizationLevel.LOW,
                "max_context": 8000,
                "preserve_recent": 2000,
                "skip_screenshots": False,
            },
            "cost_sensitive": {
                "level": OptimizationLevel.HIGH,
                "max_context": 3000,
                "preserve_recent": 800,
                "skip_screenshots": True,
            },
            "balanced": {
                "level": OptimizationLevel.MEDIUM,
                "max_context": 4000,
                "preserve_recent": 1000,
                "skip_screenshots": False,
            },
        }

        return presets.get(scenario, presets["balanced"])
