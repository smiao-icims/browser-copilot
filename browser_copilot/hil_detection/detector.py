"""
HIL (Human-in-the-Loop) detector using LLM for intelligent detection.
"""

import json
import re
from typing import Any, Dict, List, Optional

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from .patterns import FALLBACK_HIL_PATTERNS, HIL_DETECTION_PROMPT


class HILDetector:
    """
    Intelligent HIL detector that uses an LLM to analyze agent responses.
    
    This detector can identify when an agent is inappropriately asking for
    human input during automated testing, and suggest appropriate responses
    to continue the automation.
    """
    
    def __init__(
        self,
        detector_model: Optional[BaseChatModel] = None,
        fallback_to_patterns: bool = True,
        verbose: bool = False
    ):
        """
        Initialize HIL detector.
        
        Args:
            detector_model: LLM to use for detection (if None, only pattern matching)
            fallback_to_patterns: Use regex patterns if LLM detection fails
            verbose: Enable verbose logging
        """
        self.detector_model = detector_model
        self.fallback_to_patterns = fallback_to_patterns
        self.verbose = verbose
        
    def detect(
        self,
        message: str,
        test_context: Optional[str] = None,
        recent_messages: Optional[List[BaseMessage]] = None
    ) -> Dict[str, Any]:
        """
        Detect if a message is requesting human input.
        
        Args:
            message: The agent's message to analyze
            test_context: Context about the current test
            recent_messages: Recent conversation history
            
        Returns:
            Detection result with:
            - is_hil: Whether HIL was detected
            - confidence: Confidence score (0-1)
            - hil_type: Type of HIL request
            - suggested_response: Suggested continuation
            - reasoning: Why this was detected as HIL
        """
        # Try LLM detection first if available
        if self.detector_model:
            try:
                return self._llm_detect(message, test_context, recent_messages)
            except Exception as e:
                if self.verbose:
                    print(f"[HIL Detector] LLM detection failed: {e}")
                if not self.fallback_to_patterns:
                    raise
        
        # Fallback to pattern matching
        if self.fallback_to_patterns:
            return self._pattern_detect(message)
        
        # No detection method available
        return {
            "is_hil": False,
            "confidence": 0.0,
            "hil_type": "none",
            "suggested_response": "",
            "reasoning": "No detection method available"
        }
    
    def _llm_detect(
        self,
        message: str,
        test_context: Optional[str] = None,
        recent_messages: Optional[List[BaseMessage]] = None
    ) -> Dict[str, Any]:
        """Use LLM to detect HIL intelligently."""
        if self.verbose:
            print(f"[HIL Detector] Using LLM detection with model: {type(self.detector_model).__name__}")
        
        # Build conversation context
        conversation_context = ""
        if recent_messages:
            conversation_parts = []
            for msg in recent_messages[-5:]:  # Last 5 messages
                msg_type = msg.__class__.__name__
                content_preview = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                conversation_parts.append(f"{msg_type}: {content_preview}")
            conversation_context = "\n".join(conversation_parts)
        
        # Format the detection prompt
        prompt = HIL_DETECTION_PROMPT.format(
            test_context=test_context or "No specific test context provided",
            conversation=conversation_context or "No recent conversation",
            message=message
        )
        
        if self.verbose:
            print(f"[HIL Detector] Sending prompt to LLM for detection...")
        
        # Call detector LLM
        response = self.detector_model.invoke([
            SystemMessage(content="You are an expert at detecting when AI agents inappropriately ask for human input during automated testing."),
            HumanMessage(content=prompt)
        ])
        
        # Parse response
        try:
            result = json.loads(response.content)
            
            # Validate response structure
            required_fields = ["is_hil", "confidence", "hil_type", "suggested_response"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            # Ensure proper types
            result["is_hil"] = bool(result["is_hil"])
            result["confidence"] = float(result["confidence"])
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            if self.verbose:
                print(f"[HIL Detector] Failed to parse LLM response: {e}")
                print(f"[HIL Detector] Raw response: {response.content}")
            
            # Try to extract what we can from the response
            content_lower = response.content.lower()
            is_hil = "true" in content_lower or "yes" in content_lower
            
            return {
                "is_hil": is_hil,
                "confidence": 0.5,  # Low confidence due to parse failure
                "hil_type": "unknown",
                "suggested_response": "Please continue with the next step.",
                "reasoning": f"LLM response parsing failed: {str(e)}"
            }
    
    def _pattern_detect(self, message: str) -> Dict[str, Any]:
        """Fallback pattern-based detection."""
        message_lower = message.lower()
        
        # Check each pattern
        for pattern in FALLBACK_HIL_PATTERNS:
            if pattern in message_lower:
                # Determine HIL type based on pattern
                hil_type = self._classify_hil_type(pattern)
                
                # Generate appropriate response
                suggested_response = self._generate_pattern_response(hil_type, message)
                
                return {
                    "is_hil": True,
                    "confidence": 0.8,  # Pattern matching has decent confidence
                    "hil_type": hil_type,
                    "suggested_response": suggested_response,
                    "reasoning": f"Matched pattern: '{pattern}'"
                }
        
        # No patterns matched
        return {
            "is_hil": False,
            "confidence": 1.0,
            "hil_type": "none",
            "suggested_response": "",
            "reasoning": "No HIL patterns detected"
        }
    
    def _classify_hil_type(self, pattern: str) -> str:
        """Classify the type of HIL based on the matched pattern."""
        if any(word in pattern for word in ["confirm", "verify", "correct", "ok"]):
            return "confirmation"
        elif any(word in pattern for word in ["choose", "select", "prefer", "which"]):
            return "choice"
        elif any(word in pattern for word in ["should i", "shall i", "can i"]):
            return "permission"
        elif any(word in pattern for word in ["help", "clarify", "explain"]):
            return "clarification"
        else:
            return "question"
    
    def _generate_pattern_response(self, hil_type: str, original_message: str) -> str:
        """Generate an appropriate response based on HIL type."""
        message_lower = original_message.lower()
        
        # Context-specific responses based on keywords
        if "search for" in message_lower or "search query" in message_lower:
            # Provide an actionable response that guides the agent to continue
            return "Search for 'AI Advertisement' - please enter this in the search box and submit the search"
        
        if "name" in message_lower and ("your" in message_lower or "enter" in message_lower):
            return "John Doe"
            
        if "email" in message_lower:
            return "test@example.com"
            
        if "phone" in message_lower or "number" in message_lower:
            return "555-123-4567"
            
        if "address" in message_lower:
            return "123 Test Street, Test City, TC 12345"
            
        if "password" in message_lower:
            return "TestPassword123!"
            
        if "favorite color" in message_lower:
            return "blue"
            
        if "favorite" in message_lower:
            # Generic favorite response
            return "Python"
            
        # Check if we're at the end of a test
        if any(phrase in message_lower for phrase in ["test complete", "all steps completed", "test passed", "test failed"]):
            return "The test appears to be complete. Please generate the final test report."
        
        # Generic responses by type
        responses = {
            "confirmation": "Yes, that's correct. Please proceed.",
            "choice": "Select the first available option and continue.",
            "permission": "Yes, please go ahead and continue with the test.",
            "clarification": "Continue with the standard approach for this test.",
            "question": "Please continue with the next step in the test."
        }
        
        return responses.get(hil_type, "Please continue with the next step.")