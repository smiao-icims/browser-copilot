"""
Test Executor component for Browser Copilot

Handles test execution through agent interaction.
"""

import asyncio
from datetime import UTC, datetime
from typing import Any

from ..io import StreamHandler
from .models import ExecutionResult, ExecutionStep


class TestExecutor:
    """Handles test execution through agent interaction"""

    def __init__(self, stream_handler: StreamHandler, verbose: bool = False):
        """
        Initialize TestExecutor

        Args:
            stream_handler: Handler for output streaming
            verbose: Enable verbose output
        """
        self.stream = stream_handler
        self.verbose = verbose

    async def execute(
        self, agent: Any, prompt: str, timeout: int | None = None
    ) -> ExecutionResult:
        """
        Execute test through agent

        Args:
            agent: The agent to execute with
            prompt: The prompt to send to the agent
            timeout: Optional timeout in seconds

        Returns:
            ExecutionResult with steps, response, and metrics

        Raises:
            TimeoutError: If execution exceeds timeout
        """
        start_time = datetime.now(UTC)
        steps = []
        final_response = None

        try:
            # Create the async generator with timeout if specified
            if timeout:
                async_gen = asyncio.wait_for(
                    self._execute_stream(agent, prompt, steps), timeout=timeout
                )
                final_response = await async_gen
            else:
                final_response = await self._execute_stream(agent, prompt, steps)

        except TimeoutError:
            # Add a timeout step to the execution log
            timeout_step = ExecutionStep(
                type="agent_message",
                name="timeout_error",
                content=f"Test execution timed out after {timeout} seconds",
                timestamp=datetime.now(UTC)
            )
            steps.append(timeout_step)
            raise

        # Calculate duration
        duration = (datetime.now(UTC) - start_time).total_seconds()

        # Extract cleaned steps
        extracted_steps = self._extract_steps(steps)

        # Determine success from final response
        success = self._determine_success(final_response)

        return ExecutionResult(
            steps=extracted_steps,
            final_response=final_response,
            duration=duration,
            success=success,
        )

    async def _execute_stream(
        self, agent: Any, prompt: str, steps: list[ExecutionStep]
    ) -> Any:
        """
        Stream execution and collect steps

        Args:
            agent: The agent to execute with
            prompt: The prompt to send
            steps: List to collect steps into

        Returns:
            Final response from agent
        """
        final_response = None
        step_count = 0

        async for chunk in agent.astream({"messages": prompt}):
            step_count += 1

            # Process the chunk
            try:
                step = self._process_chunk(chunk, step_count)
                if step:
                    steps.append(step)

                    # In verbose mode, show progress
                    if self.verbose:
                        self._log_verbose_step(step, step_count)

                # Extract final response from agent messages
                if "agent" in chunk and "messages" in chunk["agent"]:
                    for msg in chunk["agent"]["messages"]:
                        if hasattr(msg, "content") and msg.content:
                            final_response = msg

            except Exception:
                # Continue processing even if one chunk fails
                continue

            # Non-verbose progress indicator
            if not self.verbose and step_count % 5 == 0:
                self.stream.write(f"Progress: {step_count} steps...", "debug")

        return final_response

    def _process_chunk(self, chunk: dict, step_num: int) -> ExecutionStep | None:
        """
        Process individual execution chunk

        Args:
            chunk: The chunk to process
            step_num: Current step number

        Returns:
            ExecutionStep if chunk contains relevant data, None otherwise
        """
        # Extract tool calls
        if "tools" in chunk:
            for tool_msg in chunk.get("tools", {}).get("messages", []):
                if hasattr(tool_msg, "name") and hasattr(tool_msg, "content"):
                    return ExecutionStep(
                        type="tool_call",
                        name=tool_msg.name,
                        content=str(tool_msg.content),
                    )

        # Extract agent messages
        if "agent" in chunk:
            for agent_msg in chunk.get("agent", {}).get("messages", []):
                if hasattr(agent_msg, "content") and agent_msg.content:
                    return ExecutionStep(
                        type="agent_message", name=None, content=str(agent_msg.content)
                    )

        return None

    def _extract_steps(self, raw_steps: list[ExecutionStep]) -> list[ExecutionStep]:
        """
        Convert raw agent output to structured steps

        Args:
            raw_steps: Raw execution steps

        Returns:
            Cleaned list of execution steps
        """
        extracted = []

        for step in raw_steps:
            # Include all tool calls
            if step.type == "tool_call":
                extracted.append(step)
            # Only include substantial agent messages
            elif step.type == "agent_message" and len(step.content) > 50:
                extracted.append(step)

        return extracted

    def _determine_success(self, final_response: Any) -> bool:
        """
        Determine if execution was successful

        Args:
            final_response: Final response from agent

        Returns:
            True if execution succeeded
        """
        if not final_response or not hasattr(final_response, "content"):
            return False

        content_lower = str(final_response.content).lower()

        # Check for success indicators
        success_indicators = ["passed", "success", "completed successfully"]
        failure_indicators = ["failed", "error", "failure"]

        has_success = any(
            indicator in content_lower for indicator in success_indicators
        )
        has_failure = any(
            indicator in content_lower for indicator in failure_indicators
        )

        # Success if we have success indicators and no failure indicators
        return has_success and not has_failure

    def _log_verbose_step(self, step: ExecutionStep, step_num: int) -> None:
        """
        Log step details in verbose mode

        Args:
            step: The step to log
            step_num: Current step number
        """
        self.stream.write(f"\n[STEP {step_num}] Processing...", "debug")

        if step.type == "tool_call":
            self.stream.write(f"  Tool: {step.name}", "info")
            # Show first 200 chars of tool response
            content = step.content[:200]
            if len(step.content) > 200:
                content += "..."
            self.stream.write(f"  Response: {content}", "debug")

        elif step.type == "agent_message":
            # Show first 200 chars of agent thinking
            content = step.content[:200]
            if len(step.content) > 200:
                content += "..."
            self.stream.write(f"  Agent thinking: {content}", "debug")
