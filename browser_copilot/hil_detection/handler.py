"""
Advanced HIL handler with context awareness and learning capabilities.
"""

import json
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from langchain_core.messages import (
    AIMessage, BaseMessage, HumanMessage, SystemMessage
)
from langchain_core.language_models import BaseChatModel

from .detector import HILDetector


@dataclass
class HILMemoryEntry:
    """Entry in HIL detection memory."""
    timestamp: datetime
    hil_type: str
    pattern: str
    response: str
    success: bool
    context_snippet: str


class SmartHILHandler:
    """
    Sophisticated HIL handler that maintains context and learns from patterns.
    
    This handler goes beyond simple detection by:
    - Maintaining memory of recent HIL patterns
    - Learning from successful/unsuccessful responses
    - Generating context-aware responses
    - Adapting to specific test patterns
    """
    
    def __init__(
        self,
        detector_model: Optional[str] = "gpt-3.5-turbo",
        responder_model: Optional[str] = "gpt-4",
        memory_size: int = 20,
        confidence_threshold: float = 0.7,
        verbose: bool = False
    ):
        """
        Initialize smart HIL handler.
        
        Args:
            detector_model: Model name for HIL detection (cheaper/faster)
            responder_model: Model name for response generation (smarter)
            memory_size: Number of HIL patterns to remember
            confidence_threshold: Minimum confidence to trigger handling
            verbose: Enable verbose logging
        """
        self.detector_model_name = detector_model
        self.responder_model_name = responder_model
        self.memory = deque(maxlen=memory_size)
        self.confidence_threshold = confidence_threshold
        self.verbose = verbose
        
        # These will be initialized when needed
        self._detector_llm = None
        self._responder_llm = None
        self._detector = None
        
    def create_hook(self) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
        """
        Create the post-model hook with full context awareness.
        
        Returns:
            A post-model hook function for LangGraph
        """
        
        def smart_hil_hook(state: Dict[str, Any]) -> Dict[str, Any]:
            """Smart HIL detection and handling hook."""
            messages = state.get("messages", [])
            if not messages or not isinstance(messages[-1], AIMessage):
                return {}
                
            last_message = messages[-1]
            
            # Skip if message has tool calls
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return {}
            
            # Initialize detector if needed
            if self._detector is None:
                self._init_models()
            
            # Extract comprehensive context
            test_context = self._extract_test_context(messages)
            
            # Detect with full context
            detection = self._detector.detect(
                message=last_message.content,
                test_context=test_context,
                recent_messages=messages[-5:]
            )
            
            if detection["is_hil"] and detection["confidence"] >= self.confidence_threshold:
                # Generate smart response
                response = self._generate_smart_response(
                    detection=detection,
                    test_context=test_context,
                    messages=messages,
                    state=state
                )
                
                # Learn from this pattern
                self._update_memory(
                    hil_type=detection["hil_type"],
                    pattern=last_message.content[:100],
                    response=response.content,
                    context=test_context[:200]
                )
                
                if self.verbose:
                    print(f"\n[Smart HIL] Detected: {detection['hil_type']}")
                    print(f"[Smart HIL] Confidence: {detection['confidence']:.2f}")
                    print(f"[Smart HIL] Response: {response.content}")
                
                return {"messages": [response]}
            
            return {}
        
        return smart_hil_hook
    
    def _init_models(self):
        """Initialize LLM models on first use."""
        # Import here to avoid circular dependencies
        from langchain_openai import ChatOpenAI
        
        if self.detector_model_name:
            self._detector_llm = ChatOpenAI(
                model=self.detector_model_name,
                temperature=0,
                max_tokens=200
            )
        
        if self.responder_model_name:
            self._responder_llm = ChatOpenAI(
                model=self.responder_model_name,
                temperature=0.3,
                max_tokens=150
            )
        
        self._detector = HILDetector(
            detector_model=self._detector_llm,
            verbose=self.verbose
        )
    
    def _extract_test_context(self, messages: List[BaseMessage]) -> str:
        """Extract comprehensive test context from messages."""
        context_parts = []
        
        # Get initial instructions
        for i, msg in enumerate(messages[:5]):
            if isinstance(msg, HumanMessage):
                # Extract test name if present
                content = msg.content
                if "test" in content.lower():
                    lines = content.split('\n')
                    test_line = next((l for l in lines if 'test' in l.lower()), lines[0])
                    context_parts.append(f"Test: {test_line}")
                    
                    # Extract numbered steps if present
                    steps = [l.strip() for l in lines if l.strip().startswith(('1.', '2.', '3.'))]
                    if steps:
                        context_parts.append(f"Total steps: {len(steps)}")
                        context_parts.append(f"First step: {steps[0]}")
                break
        
        # Get system context
        for msg in messages[:3]:
            if isinstance(msg, SystemMessage):
                # Extract key directives
                if "autonom" in msg.content.lower():
                    context_parts.append("Directive: Autonomous operation required")
                break
        
        # Analyze recent progress
        completed_steps = 0
        recent_actions = []
        
        for msg in messages[-10:]:
            if isinstance(msg, AIMessage):
                content_lower = msg.content.lower()
                if any(word in content_lower for word in ["completed", "done", "finished", "✓"]):
                    completed_steps += 1
                if "step" in content_lower and any(char.isdigit() for char in msg.content):
                    # Extract step number
                    import re
                    step_match = re.search(r'step\s*(\d+)', content_lower)
                    if step_match:
                        recent_actions.append(f"Step {step_match.group(1)}")
        
        if completed_steps > 0:
            context_parts.append(f"Completed steps: {completed_steps}")
        if recent_actions:
            context_parts.append(f"Recent: {', '.join(recent_actions[-3:])}")
        
        # Add memory insights
        memory_insight = self._get_memory_insight()
        if memory_insight:
            context_parts.append(f"Pattern history: {memory_insight}")
        
        return "\n".join(context_parts) if context_parts else "Minimal test context available"
    
    def _generate_smart_response(
        self,
        detection: Dict[str, Any],
        test_context: str,
        messages: List[BaseMessage],
        state: Dict[str, Any]
    ) -> HumanMessage:
        """Generate an intelligent, context-aware response."""
        
        # If no responder model, use detection's suggestion
        if not self._responder_llm:
            return HumanMessage(
                content=detection["suggested_response"],
                metadata={
                    "source": "hil_detector_suggestion",
                    "hil_type": detection["hil_type"]
                }
            )
        
        # Build prompt for response generation
        response_prompt = f"""
        The automation agent has paused, potentially asking for human input.
        Generate an appropriate response to continue the test autonomously.
        
        Test Context:
        {test_context}
        
        Agent's Message:
        {messages[-1].content}
        
        HIL Type Detected: {detection['hil_type']}
        Detection Reasoning: {detection.get('reasoning', 'N/A')}
        
        Recent Similar Patterns:
        {self._format_memory_for_prompt()}
        
        Generate a response that:
        1. Directly addresses the agent's question/concern
        2. Provides clear direction to continue
        3. Maintains test momentum
        4. Is consistent with the test objectives
        
        Response (be concise and action-oriented):
        """
        
        response = self._responder_llm.invoke([
            SystemMessage(content="You are a test automation supervisor. Provide clear, concise directions to keep tests running autonomously."),
            HumanMessage(content=response_prompt)
        ])
        
        return HumanMessage(
            content=response.content.strip(),
            metadata={
                "source": "smart_hil_responder",
                "hil_type": detection["hil_type"],
                "confidence": detection["confidence"],
                "test_context_summary": test_context[:100]
            }
        )
    
    def _update_memory(
        self,
        hil_type: str,
        pattern: str,
        response: str,
        context: str,
        success: bool = True
    ):
        """Update memory with new HIL pattern."""
        entry = HILMemoryEntry(
            timestamp=datetime.now(),
            hil_type=hil_type,
            pattern=pattern,
            response=response,
            success=success,
            context_snippet=context
        )
        self.memory.append(entry)
    
    def _get_memory_insight(self) -> str:
        """Get insights from memory for context."""
        if not self.memory:
            return ""
        
        # Count HIL types
        type_counts = {}
        for entry in self.memory:
            type_counts[entry.hil_type] = type_counts.get(entry.hil_type, 0) + 1
        
        # Most common type
        if type_counts:
            most_common = max(type_counts.items(), key=lambda x: x[1])
            return f"Most common HIL: {most_common[0]} ({most_common[1]} times)"
        
        return ""
    
    def _format_memory_for_prompt(self) -> str:
        """Format recent memory entries for prompt context."""
        if not self.memory:
            return "No previous patterns recorded"
        
        # Get last 3 relevant entries
        recent = list(self.memory)[-3:]
        formatted = []
        
        for entry in recent:
            formatted.append(
                f"- Type: {entry.hil_type}, "
                f"Response used: \"{entry.response[:50]}...\""
            )
        
        return "\n".join(formatted)