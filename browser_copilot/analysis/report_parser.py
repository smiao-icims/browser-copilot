"""
Report parsing and analysis module for Browser Copilot

This module handles parsing test execution reports and extracting
execution steps and success/failure status.
"""

import re

from ..models.execution import ExecutionStep


class ReportParser:
    """Parses and analyzes test execution reports"""

    @staticmethod
    def check_success(report_content: str) -> bool:
        """
        Determine if test passed based on report content

        Args:
            report_content: The test report content

        Returns:
            True if test passed, False otherwise
        """
        if not report_content:
            return False

        content_lower = report_content.lower()

        # Look for explicit status indicators (handle markdown formatting)
        if re.search(r"overall status:\*?\*?\s*passed", content_lower):
            return True
        if re.search(r"overall status:\*?\*?\s*failed", content_lower):
            return False

        # Look for summary indicators
        if "test passed" in content_lower:
            return True
        if "test failed" in content_lower:
            return False

        # Look for all tests passed pattern
        if re.search(r"all \d+ tests? passed", content_lower):
            return True

        # Look for failure indicators
        if any(
            indicator in content_lower
            for indicator in [
                "error:",
                "failed:",
                "failure:",
                "exception:",
                "assertion error",
            ]
        ):
            return False

        # Look for success indicators
        if re.search(r"✅.*passed|passed.*✅", content_lower):
            return True

        # Default to False if we can't determine
        return False

    @staticmethod
    def extract_steps(steps: list[dict]) -> list[ExecutionStep]:
        """
        Extract execution steps from raw agent steps

        Args:
            steps: Raw steps from agent execution

        Returns:
            List of ExecutionStep objects
        """
        execution_steps = []

        for step in steps:
            # Skip empty steps
            if not step:
                continue

            # Extract agent messages
            agent_messages = []
            if isinstance(step, dict):
                # Look for agent key
                agent_data = step.get("agent", {})
                if agent_data and isinstance(agent_data, dict):
                    messages = agent_data.get("messages", [])
                    if messages and hasattr(messages[0], "content"):
                        agent_messages.append(messages[0].content)

                # Look for messages directly
                messages = step.get("messages", [])
                if messages:
                    for msg in messages:
                        if hasattr(msg, "content"):
                            agent_messages.append(msg.content)

            # Extract tool calls
            tools_called = []
            if isinstance(step, dict):
                # Look for tools in agent data
                agent_data = step.get("agent", {})
                if agent_data and isinstance(agent_data, dict):
                    messages = agent_data.get("messages", [])
                    for msg in messages:
                        if hasattr(msg, "tool_calls"):
                            for tool_call in msg.tool_calls:
                                if hasattr(tool_call, "name"):
                                    tools_called.append(tool_call.name)
                                elif (
                                    isinstance(tool_call, dict) and "name" in tool_call
                                ):
                                    tools_called.append(tool_call["name"])

                # Look for tool responses
                tools_data = step.get("tools", {})
                if tools_data and isinstance(tools_data, dict):
                    tool_messages = tools_data.get("messages", [])
                    for tool_msg in tool_messages:
                        if hasattr(tool_msg, "name"):
                            tools_called.append(tool_msg.name)

            # Create execution step if we have any data
            if agent_messages or tools_called:
                content = (
                    " ".join(agent_messages)
                    if agent_messages
                    else (
                        f"Tools used: {', '.join(tools_called)}"
                        if tools_called
                        else "Completed"
                    )
                )
                execution_steps.append(
                    ExecutionStep(
                        type="tool_call" if tools_called else "agent_message",
                        name=tools_called[0] if tools_called else None,
                        content=content,
                        metadata={"tools_used": tools_called} if tools_called else {},
                    )
                )

        return execution_steps

    @staticmethod
    def extract_error_message(report_content: str) -> str | None:
        """
        Extract error message from report

        Args:
            report_content: Report content

        Returns:
            Error message if found, None otherwise
        """
        # Look for error section
        error_match = re.search(
            r"(?:error|exception|failure):\s*(.+?)(?:\n|$)",
            report_content,
            re.IGNORECASE | re.MULTILINE,
        )

        if error_match:
            return error_match.group(1).strip()

        # Look for issues section
        issues_match = re.search(
            r"## Issues Encountered\s*\n(.+?)(?:\n##|$)",
            report_content,
            re.IGNORECASE | re.DOTALL,
        )

        if issues_match:
            issues = issues_match.group(1).strip()
            if issues and issues.lower() not in ["none", "n/a", "-"]:
                return issues

        return None

    @staticmethod
    def extract_screenshots(report_content: str) -> list[str]:
        """
        Extract screenshot descriptions from report

        Args:
            report_content: Report content

        Returns:
            List of screenshot descriptions
        """
        screenshots = []

        # Look for screenshots section
        screenshots_match = re.search(
            r"(?:screenshots taken|screenshots):\s*\n((?:[-*]\s*.+\n?)+)",
            report_content,
            re.IGNORECASE | re.MULTILINE,
        )

        if screenshots_match:
            screenshots_text = screenshots_match.group(1)
            # Extract each screenshot description
            for line in screenshots_text.split("\n"):
                line = line.strip()
                if line and line.startswith(("-", "*")):
                    desc = line[1:].strip()
                    if desc:
                        screenshots.append(desc)

        return screenshots

    @staticmethod
    def extract_test_duration(report_content: str) -> float | None:
        """
        Extract test duration from report

        Args:
            report_content: Report content

        Returns:
            Duration in seconds if found
        """
        # Look for duration pattern
        duration_match = re.search(
            r"duration:\s*(\d+(?:\.\d+)?)\s*seconds?", report_content, re.IGNORECASE
        )

        if duration_match:
            return float(duration_match.group(1))

        return None

    @staticmethod
    def parse_test_results(report_content: str) -> tuple[int, int]:
        """
        Parse test results to get passed/failed counts

        Args:
            report_content: Report content

        Returns:
            Tuple of (passed_count, failed_count)
        """
        passed = 0
        failed = 0

        # Look for step results
        for match in re.finditer(r"[✅✓]\s*(.+?)(?:\n|$)", report_content):
            passed += 1

        for match in re.finditer(r"[❌✗]\s*(.+?)(?:\n|$)", report_content):
            failed += 1

        # Look for summary counts
        summary_match = re.search(
            r"(\d+)\s*(?:tests?|steps?)\s*passed.*?(\d+)\s*failed",
            report_content,
            re.IGNORECASE,
        )

        if summary_match:
            passed = int(summary_match.group(1))
            failed = int(summary_match.group(2))

        return passed, failed
