"""
Tests for TestExecutor component
"""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from browser_copilot.components.models import ExecutionResult, ExecutionStep
from browser_copilot.components.test_executor import TestExecutor
from browser_copilot.io import StreamHandler


class TestTestExecutor:
    """Test cases for TestExecutor"""

    @pytest.fixture
    def mock_stream(self):
        """Create a mock StreamHandler"""
        stream = MagicMock(spec=StreamHandler)
        stream.write = MagicMock()
        return stream

    @pytest.fixture
    def executor(self, mock_stream):
        """Create a TestExecutor instance"""
        return TestExecutor(mock_stream, verbose=False)

    @pytest.fixture
    def verbose_executor(self, mock_stream):
        """Create a verbose TestExecutor instance"""
        return TestExecutor(mock_stream, verbose=True)

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent"""
        agent = AsyncMock()
        return agent

    @pytest.mark.asyncio
    async def test_execute_basic_success(self, executor, mock_agent):
        """Test basic successful execution"""
        # Setup mock agent to yield chunks
        # Create proper mocks
        agent_msg1 = MagicMock()
        agent_msg1.content = "Starting test execution with detailed analysis of the page structure"
        
        tool_msg = MagicMock()
        tool_msg.name = "browser_navigate"
        tool_msg.content = "Navigated"
        
        agent_msg2 = MagicMock()
        agent_msg2.content = "Test completed successfully with all assertions passing correctly"
        
        chunks = [
            {"agent": {"messages": [agent_msg1]}},
            {"tools": {"messages": [tool_msg]}},
            {"agent": {"messages": [agent_msg2]}},
        ]
        
        async def mock_astream(input_dict):
            for chunk in chunks:
                yield chunk
        
        mock_agent.astream = mock_astream
        
        # Execute
        result = await executor.execute(mock_agent, "Test prompt")
        
        # Verify result
        assert isinstance(result, ExecutionResult)
        assert result.success is True
        assert len(result.steps) == 3
        assert result.duration > 0
        assert result.final_response.content == "Test completed successfully with all assertions passing correctly"

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self, executor, mock_agent):
        """Test execution with timeout"""
        # Setup mock agent to yield slowly
        async def mock_astream(input_dict):
            await asyncio.sleep(2)  # Longer than timeout
            yield {"agent": {"messages": [MagicMock(content="Too late")]}}
        
        mock_agent.astream = mock_astream
        
        # Execute with short timeout
        with pytest.raises(TimeoutError):
            await executor.execute(mock_agent, "Test prompt", timeout=1)

    @pytest.mark.asyncio
    async def test_execute_verbose_mode(self, verbose_executor, mock_agent, mock_stream):
        """Test execution in verbose mode"""
        # Setup mock agent
        # Create proper mocks
        tool_msg = MagicMock()
        tool_msg.name = "browser_click"
        tool_msg.content = "Clicked button"
        
        agent_msg = MagicMock()
        agent_msg.content = "Processing..."
        
        chunks = [
            {"tools": {"messages": [tool_msg]}},
            {"agent": {"messages": [agent_msg]}}
        ]
        
        async def mock_astream(input_dict):
            for chunk in chunks:
                yield chunk
        
        mock_agent.astream = mock_astream
        
        # Execute
        result = await verbose_executor.execute(mock_agent, "Test prompt")
        
        # Verify verbose output was written
        assert mock_stream.write.called
        # Check for step progress messages
        mock_stream.write.assert_any_call("\n[STEP 1] Processing...", "debug")
        # Check that tool info was logged (adjust for actual tool attributes)
        tool_calls = [call for call in mock_stream.write.call_args_list if "Tool:" in str(call[0][0])]
        assert len(tool_calls) > 0

    @pytest.mark.asyncio
    async def test_execute_no_final_response(self, executor, mock_agent):
        """Test execution without final response"""
        # Setup mock agent with no agent messages
        # Create proper mock
        tool_msg = MagicMock()
        tool_msg.name = "browser_navigate"
        tool_msg.content = "Nav"
        
        chunks = [
            {"tools": {"messages": [tool_msg]}},
        ]
        
        async def mock_astream(input_dict):
            for chunk in chunks:
                yield chunk
        
        mock_agent.astream = mock_astream
        
        # Execute
        result = await executor.execute(mock_agent, "Test prompt")
        
        # Should still return result but no final response
        assert result.final_response is None
        assert len(result.steps) == 1
        assert result.success is False  # No final response means incomplete

    @pytest.mark.asyncio
    async def test_process_chunk_tool_call(self, executor):
        """Test processing tool call chunk"""
        mock_msg = MagicMock()
        mock_msg.name = "browser_snapshot"
        mock_msg.content = "Page snapshot taken"
        chunk = {
            "tools": {
                "messages": [mock_msg]
            }
        }
        
        step = executor._process_chunk(chunk, 1)
        
        assert isinstance(step, ExecutionStep)
        assert step.type == "tool_call"
        assert step.name == "browser_snapshot"
        assert step.content == "Page snapshot taken"

    @pytest.mark.asyncio
    async def test_process_chunk_agent_message(self, executor):
        """Test processing agent message chunk"""
        mock_msg = MagicMock()
        mock_msg.content = "Analyzing page structure"
        chunk = {
            "agent": {
                "messages": [mock_msg]
            }
        }
        
        step = executor._process_chunk(chunk, 2)
        
        assert isinstance(step, ExecutionStep)
        assert step.type == "agent_message"
        assert step.name is None
        assert step.content == "Analyzing page structure"

    @pytest.mark.asyncio
    async def test_process_chunk_empty(self, executor):
        """Test processing empty chunk"""
        chunk = {}
        
        step = executor._process_chunk(chunk, 3)
        
        assert step is None

    def test_extract_steps_mixed_content(self, executor):
        """Test extracting steps from mixed content"""
        raw_steps = [
            ExecutionStep("tool_call", "browser_navigate", "Navigated to site"),
            ExecutionStep("agent_message", None, "Short message"),  # Too short, filtered
            ExecutionStep("agent_message", None, "This is a longer message that should be included in the results"),
            ExecutionStep("tool_call", "browser_click", "Clicked submit"),
        ]
        
        extracted = executor._extract_steps(raw_steps)
        
        assert len(extracted) == 3  # Short message filtered out
        assert extracted[0].type == "tool_call"
        assert extracted[1].type == "agent_message"
        assert extracted[2].type == "tool_call"

    def test_extract_steps_empty_list(self, executor):
        """Test extracting steps from empty list"""
        extracted = executor._extract_steps([])
        
        assert extracted == []

    @pytest.mark.asyncio
    async def test_execute_with_progress_callback(self, executor, mock_agent):
        """Test execution tracks progress correctly"""
        chunks = []
        for i in range(10):
            tool_msg = MagicMock()
            tool_msg.name = f"tool_{i}"
            tool_msg.content = f"Step {i}"
            chunks.append({
                "tools": {"messages": [tool_msg]}
            })
        
        async def mock_astream(input_dict):
            for chunk in chunks:
                yield chunk
        
        mock_agent.astream = mock_astream
        
        # Execute
        result = await executor.execute(mock_agent, "Test prompt")
        
        # Verify all steps processed
        assert len(result.steps) == 10

    @pytest.mark.asyncio
    async def test_execute_determines_success_from_content(self, executor, mock_agent):
        """Test success determination from final response"""
        # Test success case
        # Test success case
        success_msg = MagicMock()
        success_msg.content = "Test execution completed. All tests PASSED."
        success_chunks = [
            {"agent": {"messages": [success_msg]}}
        ]
        
        async def mock_success_stream(input_dict):
            for chunk in success_chunks:
                yield chunk
        
        mock_agent.astream = mock_success_stream
        result = await executor.execute(mock_agent, "Test prompt")
        assert result.success is True
        
        # Test failure case
        failure_msg = MagicMock()
        failure_msg.content = "Test FAILED with errors."
        failure_chunks = [
            {"agent": {"messages": [failure_msg]}}
        ]
        
        async def mock_failure_stream(input_dict):
            for chunk in failure_chunks:
                yield chunk
        
        mock_agent.astream = mock_failure_stream
        result = await executor.execute(mock_agent, "Test prompt")
        assert result.success is False

    @pytest.mark.asyncio
    async def test_execute_verbose_truncates_long_content(self, verbose_executor, mock_agent, mock_stream):
        """Test verbose mode truncates long content"""
        long_content = "A" * 500
        tool_msg = MagicMock()
        tool_msg.name = "test_tool"
        tool_msg.content = long_content
        chunks = [
            {"tools": {"messages": [tool_msg]}}
        ]
        
        async def mock_astream(input_dict):
            for chunk in chunks:
                yield chunk
        
        mock_agent.astream = mock_astream
        
        # Execute
        await verbose_executor.execute(mock_agent, "Test prompt")
        
        # Verify content was truncated in debug output
        debug_calls = [call for call in mock_stream.write.call_args_list if call[0][1] == "debug"]
        assert any("..." in str(call[0][0]) for call in debug_calls)

    @pytest.mark.asyncio
    async def test_execute_handles_exception_in_chunk(self, executor, mock_agent):
        """Test handling of exceptions during chunk processing"""
        # Create a chunk that will cause an error
        bad_chunk = {"tools": {"messages": [None]}}  # None will cause AttributeError
        
        recovery_msg = MagicMock()
        recovery_msg.content = "Recovery completed successfully after handling the error in processing"
        good_chunk = {"agent": {"messages": [recovery_msg]}}
        
        async def mock_astream(input_dict):
            yield bad_chunk
            yield good_chunk
        
        mock_agent.astream = mock_astream
        
        # Execute - should continue despite error
        result = await executor.execute(mock_agent, "Test prompt")
        
        # Should have processed the good chunk
        assert len(result.steps) >= 1
        assert any(step.content == "Recovery completed successfully after handling the error in processing" for step in result.steps)

    @pytest.mark.asyncio
    async def test_execute_with_timestamp_ordering(self, executor, mock_agent):
        """Test that steps have proper timestamp ordering"""
        chunks = []
        for i in range(3):
            msg = MagicMock()
            msg.content = f"Step {i}"
            chunks.append({"agent": {"messages": [msg]}})
        
        async def mock_astream(input_dict):
            for chunk in chunks:
                await asyncio.sleep(0.01)  # Small delay to ensure different timestamps
                yield chunk
        
        mock_agent.astream = mock_astream
        
        # Execute
        result = await executor.execute(mock_agent, "Test prompt")
        
        # Verify timestamps are in order
        for i in range(1, len(result.steps)):
            assert result.steps[i].timestamp >= result.steps[i-1].timestamp