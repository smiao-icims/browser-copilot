"""
Patterns and prompts for HIL detection.
"""

# Fallback patterns for regex-based detection
FALLBACK_HIL_PATTERNS = [
    "would you like",
    "should i",
    "do you want",
    "do you need", 
    "do you prefer",
    "please confirm",
    "please verify",
    "is this correct",
    "is that correct",
    "is this ok",
    "is that ok",
    "shall i",
    "can i proceed",
    "let me know",
    "tell me if",
    "what would you like",
    "what would you prefer",
    "how would you like",
    "would you prefer",
    "any preference",
    "need any changes",
    "anything else",
    "explore further",
    "continue exploring",
    "what is your",
    "what are your",
]

# LLM detection prompt template
HIL_DETECTION_PROMPT = """You are an expert test automation engineer monitoring an AI-assisted browser test execution. Your role is to ensure the test runs completely autonomously without human intervention.

Analyze the current situation and determine if the AI agent is inappropriately asking for human input instead of making autonomous decisions.

Test Context:
{test_context}

Recent Conversation:
{conversation}

Current Agent Message:
{message}

Your task:
1. Determine if the agent is asking for human input (HIL) or just providing status updates
2. If HIL is detected, provide a reasonable response that allows the test to continue autonomously

Guidelines for detection:
- Status reports like "I will now..." or "The test is complete" → NOT HIL
- Questions like "What would you like to search for?" or "Should I..." → IS HIL
- Requests for clarification or confirmation → IS HIL
- Informational messages or progress updates → NOT HIL

Guidelines for responses:
- For search queries: Provide relevant, current search terms (e.g., "artificial intelligence trends 2025")
- For form inputs: Generate realistic test data (names, emails, addresses, etc.)
- For choices: Select the most reasonable option that advances the test
- For confirmations: Always confirm to proceed with the test
- Make assumptions based on common test scenarios to keep automation flowing
- IMPORTANT: Frame the response as if continuing the conversation naturally, not just providing data

Your response MUST be valid JSON:
{{
    "is_hil": boolean,
    "confidence": float (0-1),
    "hil_type": "confirmation|choice|permission|clarification|direction|search_query|form_input|none",
    "reasoning": "brief explanation of your determination",
    "suggested_response": "specific, actionable response that continues the test autonomously"
}}"""