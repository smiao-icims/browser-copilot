"""
Tests for AgentFactory
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Direct import to avoid package-level imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from browser_copilot.agent import AgentFactory


@pytest.mark.unit
class TestAgentFactory:
    """Test AgentFactory functionality"""

    @pytest.fixture
    def mock_llm(self):
        """Create mock LLM instance"""
        llm = MagicMock()
        llm.temperature = 0.7
        llm.max_tokens = 1000
        return llm

    @pytest.fixture
    def agent_factory(self, mock_llm):
        """Create AgentFactory instance"""
        return AgentFactory(mock_llm)

    @pytest.fixture
    def mock_session(self):
        """Create mock MCP session"""
        session = MagicMock()
        return session

    def test_initialization(self, mock_llm):
        """Test AgentFactory initialization"""
        factory = AgentFactory(mock_llm)
        assert factory.llm is mock_llm

    def test_get_llm(self, agent_factory, mock_llm):
        """Test getting LLM instance from factory"""
        assert agent_factory.get_llm() is mock_llm

    @pytest.mark.asyncio
    @patch("browser_copilot.agent.load_mcp_tools")
    @patch("browser_copilot.agent.create_react_agent")
    async def test_create_browser_agent_default_params(
        self, mock_create_agent, mock_load_tools, agent_factory, mock_session
    ):
        """Test creating browser agent with default parameters"""
        # Setup mocks
        mock_tools = [MagicMock(), MagicMock()]
        mock_load_tools.return_value = mock_tools

        mock_agent = MagicMock()
        mock_configured_agent = MagicMock()
        mock_agent.with_config.return_value = mock_configured_agent
        mock_create_agent.return_value = mock_agent

        # Call method
        result = await agent_factory.create_browser_agent(mock_session)

        # Verify calls
        mock_load_tools.assert_called_once_with(mock_session)
        mock_create_agent.assert_called_once_with(agent_factory.llm, mock_tools)
        mock_agent.with_config.assert_called_once_with(recursion_limit=100)

        assert result is mock_configured_agent

    @pytest.mark.asyncio
    @patch("browser_copilot.agent.load_mcp_tools")
    @patch("browser_copilot.agent.create_react_agent")
    async def test_create_browser_agent_custom_recursion_limit(
        self, mock_create_agent, mock_load_tools, agent_factory, mock_session
    ):
        """Test creating browser agent with custom recursion limit"""
        # Setup mocks
        mock_tools = [MagicMock()]
        mock_load_tools.return_value = mock_tools

        mock_agent = MagicMock()
        mock_configured_agent = MagicMock()
        mock_agent.with_config.return_value = mock_configured_agent
        mock_create_agent.return_value = mock_agent

        # Call method with custom recursion limit
        result = await agent_factory.create_browser_agent(
            mock_session, recursion_limit=50
        )

        # Verify calls
        mock_load_tools.assert_called_once_with(mock_session)
        mock_create_agent.assert_called_once_with(agent_factory.llm, mock_tools)
        mock_agent.with_config.assert_called_once_with(recursion_limit=50)

        assert result is mock_configured_agent

    @pytest.mark.asyncio
    @patch("browser_copilot.agent.load_mcp_tools")
    async def test_create_browser_agent_tool_loading_error(
        self, mock_load_tools, agent_factory, mock_session
    ):
        """Test handling tool loading errors"""
        # Setup mock to raise exception
        mock_load_tools.side_effect = Exception("Tool loading failed")

        # Verify exception is propagated
        with pytest.raises(Exception, match="Tool loading failed"):
            await agent_factory.create_browser_agent(mock_session)

    @pytest.mark.asyncio
    @patch("browser_copilot.agent.load_mcp_tools")
    @patch("browser_copilot.agent.create_react_agent")
    async def test_create_browser_agent_empty_tools(
        self, mock_create_agent, mock_load_tools, agent_factory, mock_session
    ):
        """Test creating agent with empty tools list"""
        # Setup mocks
        mock_tools = []  # Empty tools list
        mock_load_tools.return_value = mock_tools

        mock_agent = MagicMock()
        mock_configured_agent = MagicMock()
        mock_agent.with_config.return_value = mock_configured_agent
        mock_create_agent.return_value = mock_agent

        # Call method
        result = await agent_factory.create_browser_agent(mock_session)

        # Verify it still works with empty tools
        mock_load_tools.assert_called_once_with(mock_session)
        mock_create_agent.assert_called_once_with(agent_factory.llm, mock_tools)
        mock_agent.with_config.assert_called_once_with(recursion_limit=100)

        assert result is mock_configured_agent

    @pytest.mark.asyncio
    @patch("browser_copilot.agent.load_mcp_tools")
    @patch("browser_copilot.agent.create_react_agent")
    async def test_create_browser_agent_agent_creation_error(
        self, mock_create_agent, mock_load_tools, agent_factory, mock_session
    ):
        """Test handling agent creation errors"""
        # Setup mocks
        mock_tools = [MagicMock()]
        mock_load_tools.return_value = mock_tools
        mock_create_agent.side_effect = Exception("Agent creation failed")

        # Verify exception is propagated
        with pytest.raises(Exception, match="Agent creation failed"):
            await agent_factory.create_browser_agent(mock_session)

    @pytest.mark.asyncio
    @patch("browser_copilot.agent.load_mcp_tools")
    @patch("browser_copilot.agent.create_react_agent")
    async def test_create_browser_agent_configuration_error(
        self, mock_create_agent, mock_load_tools, agent_factory, mock_session
    ):
        """Test handling agent configuration errors"""
        # Setup mocks
        mock_tools = [MagicMock()]
        mock_load_tools.return_value = mock_tools

        mock_agent = MagicMock()
        mock_agent.with_config.side_effect = Exception("Configuration failed")
        mock_create_agent.return_value = mock_agent

        # Verify exception is propagated
        with pytest.raises(Exception, match="Configuration failed"):
            await agent_factory.create_browser_agent(mock_session)

    @pytest.mark.asyncio
    @patch("browser_copilot.agent.load_mcp_tools")
    @patch("browser_copilot.agent.create_react_agent")
    async def test_multiple_agent_creation(
        self, mock_create_agent, mock_load_tools, agent_factory, mock_session
    ):
        """Test creating multiple agents with same factory"""
        # Setup mocks
        mock_tools = [MagicMock()]
        mock_load_tools.return_value = mock_tools

        mock_agent1 = MagicMock()
        mock_agent2 = MagicMock()
        mock_configured_agent1 = MagicMock()
        mock_configured_agent2 = MagicMock()

        mock_agent1.with_config.return_value = mock_configured_agent1
        mock_agent2.with_config.return_value = mock_configured_agent2
        mock_create_agent.side_effect = [mock_agent1, mock_agent2]

        # Create two agents
        result1 = await agent_factory.create_browser_agent(mock_session)
        result2 = await agent_factory.create_browser_agent(mock_session)

        # Verify both calls were made correctly
        assert mock_load_tools.call_count == 2
        assert mock_create_agent.call_count == 2
        assert result1 is mock_configured_agent1
        assert result2 is mock_configured_agent2

    def test_agent_factory_with_different_llms(self):
        """Test creating factories with different LLM instances"""
        llm1 = MagicMock()
        llm2 = MagicMock()

        factory1 = AgentFactory(llm1)
        factory2 = AgentFactory(llm2)

        assert factory1.get_llm() is llm1
        assert factory2.get_llm() is llm2
        assert factory1.get_llm() is not factory2.get_llm()

    @pytest.mark.asyncio
    @patch("browser_copilot.agent.load_mcp_tools")
    @patch("browser_copilot.agent.create_react_agent")
    async def test_create_browser_agent_with_zero_recursion_limit(
        self, mock_create_agent, mock_load_tools, agent_factory, mock_session
    ):
        """Test creating agent with zero recursion limit"""
        # Setup mocks
        mock_tools = [MagicMock()]
        mock_load_tools.return_value = mock_tools

        mock_agent = MagicMock()
        mock_configured_agent = MagicMock()
        mock_agent.with_config.return_value = mock_configured_agent
        mock_create_agent.return_value = mock_agent

        # Call method with zero recursion limit
        result = await agent_factory.create_browser_agent(
            mock_session, recursion_limit=0
        )

        # Verify configuration with zero limit
        mock_agent.with_config.assert_called_once_with(recursion_limit=0)
        assert result is mock_configured_agent
