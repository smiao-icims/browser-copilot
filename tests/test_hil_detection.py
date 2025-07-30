"""
Tests for Human-in-the-Loop detection and handling.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from browser_copilot.hil_detection.detector import HILDetector
from browser_copilot.hil_detection.hooks import create_hil_post_hook, create_simple_hil_hook
from browser_copilot.hil_detection.handler import SmartHILHandler


class TestHILDetection:
    """Test HIL detection functionality."""
    
    @pytest.fixture
    def mock_messages_with_hil(self):
        """Create messages that contain HIL requests."""
        return [
            HumanMessage(content="Please navigate to example.com and fill out the contact form"),
            AIMessage(content="I've navigated to example.com. I can see a contact form."),
            AIMessage(content="I've filled in the name and email fields. Would you like me to submit the form now?")
        ]
    
    @pytest.fixture
    def mock_messages_without_hil(self):
        """Create messages without HIL requests."""
        return [
            HumanMessage(content="Navigate to example.com and submit the contact form"),
            AIMessage(content="I've navigated to example.com."),
            AIMessage(content="I've filled in the form fields and submitted the form successfully.")
        ]
    
    @pytest.fixture
    def mock_messages_with_various_hil(self):
        """Create messages with different types of HIL patterns."""
        return [
            # Confirmation request
            AIMessage(content="I found the login button. Should I click it?"),
            # Choice request
            AIMessage(content="There are two forms on the page. Which one would you prefer I fill out?"),
            # Direction request
            AIMessage(content="The test is complete. What would you like me to do next?"),
            # Exploration request
            AIMessage(content="I see interesting results. Would you like to explore these further?"),
            # Permission request
            AIMessage(content="The form has sensitive fields. Can I proceed with filling them?"),
        ]
    
    def test_pattern_based_detection(self):
        """Test simple pattern-based HIL detection."""
        detector = HILDetector(fallback_to_patterns=True)
        
        # Test positive cases
        hil_messages = [
            "Would you like me to continue?",
            "Should I proceed with the next step?",
            "Do you want me to click submit?",
            "Please confirm this is correct.",
            "What would you prefer?",
        ]
        
        for msg in hil_messages:
            result = detector.detect(msg)
            assert result["is_hil"] is True, f"Failed to detect HIL in: {msg}"
            assert result["confidence"] >= 0.8
            assert result["suggested_response"] != ""
    
    def test_pattern_based_non_detection(self):
        """Test that normal messages don't trigger HIL detection."""
        detector = HILDetector(fallback_to_patterns=True)
        
        non_hil_messages = [
            "I have successfully clicked the button.",
            "The form has been submitted.",
            "Navigating to the next page now.",
            "I will now fill in the form fields.",
            "The test is complete. All steps passed.",
        ]
        
        for msg in non_hil_messages:
            result = detector.detect(msg)
            assert result["is_hil"] is False, f"Incorrectly detected HIL in: {msg}"
    
    def test_simple_hook_integration(self):
        """Test simple HIL hook without LLM."""
        hook = create_simple_hil_hook(verbose=False, auto_continue=True)
        
        # Test with HIL message
        state_with_hil = {
            "messages": [
                HumanMessage(content="Run the test"),
                AIMessage(content="I've completed step 1. Would you like me to continue?")
            ]
        }
        
        result = hook(state_with_hil)
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], HumanMessage)
        assert "continue" in result["messages"][0].content.lower()
    
    def test_simple_hook_no_detection(self):
        """Test simple hook with non-HIL message."""
        hook = create_simple_hil_hook(verbose=False)
        
        state_without_hil = {
            "messages": [
                HumanMessage(content="Run the test"),
                AIMessage(content="I've completed all test steps successfully.")
            ]
        }
        
        result = hook(state_without_hil)
        assert result == {}  # No update
    
    @patch('browser_copilot.hil_detection.detector.ChatOpenAI')
    def test_llm_based_detection(self, mock_chat):
        """Test LLM-based HIL detection."""
        # Mock LLM response
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = '''{
            "is_hil": true,
            "confidence": 0.9,
            "hil_type": "confirmation",
            "suggested_response": "Yes, please proceed with submitting the form.",
            "reasoning": "The agent is asking for permission to submit a form."
        }'''
        mock_llm.invoke.return_value = mock_response
        mock_chat.return_value = mock_llm
        
        detector = HILDetector(detector_model=mock_llm)
        result = detector.detect(
            "Should I submit the form now?",
            test_context="Test: Submit contact form"
        )
        
        assert result["is_hil"] is True
        assert result["confidence"] == 0.9
        assert result["hil_type"] == "confirmation"
        assert "proceed" in result["suggested_response"]
    
    def test_hil_type_classification(self):
        """Test correct classification of HIL types."""
        detector = HILDetector(fallback_to_patterns=True)
        
        test_cases = [
            ("Please confirm this is correct", "confirmation"),
            ("Which option should I choose?", "choice"),
            ("Should I proceed?", "permission"),
            ("Would you like to explore further?", "question"),
        ]
        
        for message, expected_type in test_cases:
            result = detector.detect(message)
            assert result["hil_type"] == expected_type, f"Wrong type for: {message}"
    
    def test_smart_handler_memory(self):
        """Test SmartHILHandler memory functionality."""
        handler = SmartHILHandler(
            detector_model=None,  # Use pattern-based
            memory_size=5,
            verbose=False
        )
        
        # Add some patterns to memory
        handler._update_memory(
            hil_type="confirmation",
            pattern="Should I click submit?",
            response="Yes, click submit.",
            context="Test: Form submission"
        )
        
        # Check memory insight
        insight = handler._get_memory_insight()
        assert "confirmation" in insight
        
        # Test memory formatting
        formatted = handler._format_memory_for_prompt()
        assert "confirmation" in formatted
        assert "Yes, click submit" in formatted


class TestHILIntegration:
    """Test HIL integration with agent creation."""
    
    @pytest.mark.asyncio
    async def test_agent_with_hil_detection(self):
        """Test agent creation with HIL detection enabled."""
        from browser_copilot.agent import AgentFactory
        
        # Mock dependencies
        mock_llm = Mock()
        mock_session = Mock()
        
        # Mock load_mcp_tools
        with patch('browser_copilot.agent.load_mcp_tools', new_callable=AsyncMock) as mock_load_tools:
            mock_load_tools.return_value = []
            
            # Mock create_react_agent
            with patch('browser_copilot.agent.create_react_agent') as mock_create:
                mock_agent = Mock()
                mock_agent.with_config.return_value = mock_agent
                mock_create.return_value = mock_agent
                
                # Create agent with HIL detection
                factory = AgentFactory(mock_llm)
                agent = await factory.create_browser_agent(
                    session=mock_session,
                    hil_detection=True,
                    hil_detection_model="gpt-3.5-turbo"
                )
                
                # Verify create_react_agent was called with post_model_hook
                mock_create.assert_called_once()
                call_args = mock_create.call_args[1]
                assert call_args.get('post_model_hook') is not None
    
    @pytest.mark.asyncio  
    async def test_agent_without_hil_detection(self):
        """Test agent creation with HIL detection disabled."""
        from browser_copilot.agent import AgentFactory
        
        mock_llm = Mock()
        mock_session = Mock()
        
        with patch('browser_copilot.agent.load_mcp_tools', new_callable=AsyncMock) as mock_load_tools:
            mock_load_tools.return_value = []
            
            with patch('browser_copilot.agent.create_react_agent') as mock_create:
                mock_agent = Mock()
                mock_agent.with_config.return_value = mock_agent
                mock_create.return_value = mock_agent
                
                factory = AgentFactory(mock_llm)
                agent = await factory.create_browser_agent(
                    session=mock_session,
                    hil_detection=False
                )
                
                # Verify post_model_hook is None
                call_args = mock_create.call_args[1]
                assert call_args.get('post_model_hook') is None


class TestHILScenarios:
    """Test specific HIL scenarios we want to handle."""
    
    def test_test_completion_scenario(self):
        """Test handling when agent asks what to do after test completion."""
        detector = HILDetector(fallback_to_patterns=True)
        
        message = "I've completed all the test steps successfully. What would you like me to do next?"
        result = detector.detect(message)
        
        assert result["is_hil"] is True
        assert "report" in result["suggested_response"].lower() or "complete" in result["suggested_response"].lower()
    
    def test_ambiguous_instruction_scenario(self):
        """Test handling when agent is unsure about instructions."""
        detector = HILDetector(fallback_to_patterns=True)
        
        message = "The instructions mention clicking a button, but I see three buttons. Should I click the first one?"
        result = detector.detect(message)
        
        assert result["is_hil"] is True
        assert result["hil_type"] in ["confirmation", "choice"]
    
    def test_error_recovery_scenario(self):
        """Test handling when agent encounters an error."""
        detector = HILDetector(fallback_to_patterns=True)
        
        message = "I encountered an error: Element not found. Would you like me to retry or skip this step?"
        result = detector.detect(message)
        
        assert result["is_hil"] is True
        assert "continue" in result["suggested_response"].lower() or "retry" in result["suggested_response"].lower()