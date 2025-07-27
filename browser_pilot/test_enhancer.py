"""
Test Suite Enhancer for Browser Pilot

Uses AI to enhance test suites with better selectors, assertions, and error handling.
"""

from typing import Optional

try:
    from .config_manager import ConfigManager
    from .token_optimizer import TokenOptimizer, OptimizationLevel
except ImportError:
    # For standalone testing
    try:
        from browser_pilot.config_manager import ConfigManager
        from browser_pilot.token_optimizer import TokenOptimizer, OptimizationLevel
    except ImportError:
        # For unit testing
        from config_manager import ConfigManager
        from token_optimizer import TokenOptimizer, OptimizationLevel


class TestSuiteEnhancer:
    """Enhances test suites to make them more explicit and reliable"""
    
    ENHANCEMENT_PROMPT = """You are a test automation expert. Enhance the following test suite to make it more explicit and reliable.

Follow these enhancement guidelines:
1. Add specific CSS selectors or element identifiers where they're missing
2. Add explicit waits after navigation and before interactions
3. Add assertions to verify expected outcomes
4. Add error handling for common failure scenarios
5. Make instructions clear and unambiguous
6. Use data-testid attributes when available
7. Add comments explaining complex steps

Original Test Suite:
{test_suite}

Enhanced Test Suite:
"""
    
    def __init__(
        self,
        llm = None,
        config: Optional[ConfigManager] = None,
        optimize_prompt: bool = True
    ):
        """
        Initialize TestSuiteEnhancer
        
        Args:
            llm: Language model instance
            config: ConfigManager instance
            optimize_prompt: Whether to optimize the enhancement prompt
        """
        self.llm = llm
        self.config = config or ConfigManager()
        self.optimize_prompt = optimize_prompt
        
        # Initialize token optimizer if needed
        self.token_optimizer = None
        if optimize_prompt:
            self.token_optimizer = TokenOptimizer(OptimizationLevel.MEDIUM)
    
    async def enhance_test_suite(self, test_suite_content: str) -> str:
        """
        Enhance a test suite using AI
        
        Args:
            test_suite_content: Original test suite content
            
        Returns:
            Enhanced test suite content
        """
        if not self.llm:
            raise ValueError("LLM instance required for test enhancement")
        
        # Build enhancement prompt
        prompt = self.ENHANCEMENT_PROMPT.format(test_suite=test_suite_content)
        
        # Optimize prompt if enabled
        if self.token_optimizer:
            prompt = self.token_optimizer.optimize_prompt(prompt)
        
        # Call LLM for enhancement
        try:
            response = await self.llm.ainvoke(prompt)
            enhanced_content = response.content if hasattr(response, 'content') else str(response)
            
            # Clean up response
            enhanced_content = self._clean_response(enhanced_content)
            
            return enhanced_content
            
        except Exception as e:
            # Return original if enhancement fails
            print(f"Enhancement failed: {e}")
            return test_suite_content
    
    def enhance_test_suite_sync(self, test_suite_content: str) -> str:
        """
        Synchronous version of enhance_test_suite
        
        Args:
            test_suite_content: Original test suite content
            
        Returns:
            Enhanced test suite content
        """
        if not self.llm:
            raise ValueError("LLM instance required for test enhancement")
        
        # Build enhancement prompt
        prompt = self.ENHANCEMENT_PROMPT.format(test_suite=test_suite_content)
        
        # Optimize prompt if enabled
        if self.token_optimizer:
            prompt = self.token_optimizer.optimize_prompt(prompt)
        
        # Call LLM for enhancement
        try:
            response = self.llm.invoke(prompt)
            enhanced_content = response.content if hasattr(response, 'content') else str(response)
            
            # Clean up response
            enhanced_content = self._clean_response(enhanced_content)
            
            return enhanced_content
            
        except Exception as e:
            # Return original if enhancement fails
            print(f"Enhancement failed: {e}")
            return test_suite_content
    
    def _clean_response(self, response: str) -> str:
        """
        Clean up LLM response
        
        Args:
            response: Raw LLM response
            
        Returns:
            Cleaned response
        """
        # Remove common markdown artifacts
        response = response.strip()
        
        # Remove code block markers if present
        if response.startswith("```") and response.endswith("```"):
            lines = response.split('\n')
            if len(lines) > 2:
                response = '\n'.join(lines[1:-1])
        
        # Remove "Enhanced Test Suite:" prefix if present
        prefixes = ["Enhanced Test Suite:", "Enhanced test suite:", "## Enhanced Test Suite"]
        for prefix in prefixes:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
        
        return response
    
    @staticmethod
    def suggest_improvements(test_suite_content: str) -> list:
        """
        Analyze test suite and suggest improvements without AI
        
        Args:
            test_suite_content: Test suite content
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        lines = test_suite_content.lower().split('\n')
        
        # Check for missing waits
        navigation_keywords = ['navigate', 'visit', 'go to', 'open']
        has_navigation = any(keyword in line for line in lines for keyword in navigation_keywords)
        has_wait = any('wait' in line for line in lines)
        
        if has_navigation and not has_wait:
            suggestions.append("Add explicit waits after navigation to ensure page loads")
        
        # Check for missing assertions
        has_assertion = any(word in line for line in lines 
                          for word in ['verify', 'assert', 'check', 'ensure', 'confirm'])
        
        if not has_assertion:
            suggestions.append("Add assertions to verify expected outcomes")
        
        # Check for generic selectors
        generic_selectors = ['button', 'link', 'input', 'div']
        uses_generic = any(f"click {sel}" in line or f"find {sel}" in line 
                         for line in lines for sel in generic_selectors)
        
        if uses_generic:
            suggestions.append("Use specific CSS selectors or data-testid attributes instead of generic element names")
        
        # Check for error handling
        has_error_handling = any(word in line for line in lines 
                               for word in ['if', 'try', 'error', 'fail', 'fallback'])
        
        if not has_error_handling:
            suggestions.append("Add error handling for common failure scenarios")
        
        # Check for data
        has_test_data = any('"' in line or "'" in line for line in lines)
        
        if not has_test_data:
            suggestions.append("Consider using specific test data instead of generic placeholders")
        
        return suggestions


class TestSuiteValidator:
    """Validates test suites for common issues"""
    
    @staticmethod
    def validate(test_suite_content: str) -> dict:
        """
        Validate a test suite
        
        Args:
            test_suite_content: Test suite content
            
        Returns:
            Validation result with warnings and errors
        """
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": {
                "lines": 0,
                "steps": 0,
                "assertions": 0
            }
        }
        
        if not test_suite_content.strip():
            result["valid"] = False
            result["errors"].append("Test suite is empty")
            return result
        
        lines = test_suite_content.split('\n')
        result["stats"]["lines"] = len(lines)
        
        # Count steps and assertions
        step_keywords = ['navigate', 'click', 'type', 'enter', 'select', 'hover', 'wait']
        assertion_keywords = ['verify', 'assert', 'check', 'ensure', 'confirm']
        
        for line in lines:
            lower_line = line.lower()
            if any(keyword in lower_line for keyword in step_keywords):
                result["stats"]["steps"] += 1
            if any(keyword in lower_line for keyword in assertion_keywords):
                result["stats"]["assertions"] += 1
        
        # Validate structure
        if result["stats"]["steps"] == 0:
            result["errors"].append("No test steps found")
            result["valid"] = False
        
        if result["stats"]["assertions"] == 0:
            result["warnings"].append("No assertions found - consider adding verification steps")
        
        # Check for common issues
        if len(lines) > 100:
            result["warnings"].append("Test suite is very long - consider breaking into smaller tests")
        
        if any('todo' in line.lower() or 'fixme' in line.lower() for line in lines):
            result["warnings"].append("Test suite contains TODO/FIXME comments")
        
        # Check for hardcoded values
        if any('localhost' in line or '127.0.0.1' in line for line in lines):
            result["warnings"].append("Test suite contains hardcoded localhost URLs")
        
        return result