"""
Tests for TestEnhancer
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path to import modules directly
sys.path.insert(0, str(Path(__file__).parent.parent / "browser_pilot"))
from test_enhancer import TestSuiteEnhancer, TestSuiteValidator


@pytest.mark.unit
class TestTestSuiteEnhancer:
    """Test TestSuiteEnhancer functionality"""

    def test_enhance_basic_test(self):
        """Test enhancement of a basic test suite"""
        basic_test = """# Login Test
1. Navigate to example.com
2. Click login
3. Type username
4. Type password
5. Click submit"""

        enhancer = TestSuiteEnhancer()
        enhanced = enhancer.enhance(basic_test)

        # Check that enhancements were added
        assert len(enhanced["suggestions"]) > 0
        assert enhanced["original"] == basic_test
        assert "enhanced" in enhanced

        # Check for specific enhancement patterns
        suggestions_text = " ".join(enhanced["suggestions"])
        assert any(
            keyword in suggestions_text.lower()
            for keyword in ["wait", "verify", "check", "assert", "screenshot"]
        )

    def test_enhance_with_options(self):
        """Test enhancement with specific options"""
        test_content = """# Search Test
1. Navigate to search page
2. Type query
3. Click search button"""

        enhancer = TestSuiteEnhancer()
        enhanced = enhancer.enhance(
            test_content, add_waits=True, add_verifications=True, add_screenshots=False
        )

        suggestions = enhanced["suggestions"]
        suggestions_text = " ".join(suggestions).lower()

        # Should suggest waits and verifications but not screenshots
        assert "wait" in suggestions_text
        assert "verify" in suggestions_text or "check" in suggestions_text
        assert "screenshot" not in suggestions_text

    def test_suggest_improvements(self):
        """Test specific improvement suggestions"""
        enhancer = TestSuiteEnhancer()

        # Test missing waits
        test1 = "1. Navigate to page\n2. Click button immediately"
        suggestions1 = enhancer.suggest_improvements(test1)
        assert any("wait" in s.lower() for s in suggestions1)

        # Test missing verifications
        test2 = "1. Fill form\n2. Submit\n3. Done"
        suggestions2 = enhancer.suggest_improvements(test2)
        assert any("verify" in s.lower() or "check" in s.lower() for s in suggestions2)

        # Test vague selectors
        test3 = "1. Click the button\n2. Type in the field"
        suggestions3 = enhancer.suggest_improvements(test3)
        assert any(
            "specific" in s.lower() or "selector" in s.lower() for s in suggestions3
        )

    def test_add_wait_steps(self):
        """Test automatic wait step insertion"""
        enhancer = TestSuiteEnhancer()

        test = """1. Navigate to example.com
2. Click login button
3. Type username"""

        enhanced = enhancer.add_wait_steps(test)

        # Should add waits after navigation and interactions
        assert "wait" in enhanced.lower()
        assert enhanced.count("\n") > test.count("\n")  # More lines added

    def test_add_verification_steps(self):
        """Test automatic verification step insertion"""
        enhancer = TestSuiteEnhancer()

        test = """1. Navigate to login page
2. Enter credentials
3. Click submit
4. Navigate to dashboard"""

        enhanced = enhancer.add_verification_steps(test)

        # Should add verifications after key actions
        assert "verify" in enhanced.lower() or "check" in enhanced.lower()
        assert "login" in enhanced.lower()
        assert "dashboard" in enhanced.lower()

    def test_improve_selectors(self):
        """Test selector improvement suggestions"""
        enhancer = TestSuiteEnhancer()

        test = """1. Click the button
2. Type in the input field
3. Select the dropdown option
4. Click on link"""

        enhanced = enhancer.improve_selectors(test)

        # Should suggest more specific selectors
        assert enhanced != test
        assert any(selector in enhanced for selector in ["#", ".", "[", "button"])

    def test_optimize_test_flow(self):
        """Test test flow optimization"""
        enhancer = TestSuiteEnhancer()

        # Test with redundant steps
        test = """1. Navigate to home
2. Click login
3. Navigate to login page
4. Enter username
5. Enter password
6. Enter username again
7. Submit"""

        optimized = enhancer.optimize_test_flow(test)

        # Should identify redundancies
        assert "redundant" in optimized.lower() or "optimize" in optimized.lower()
        assert len(optimized) > len(test)  # Added optimization comments


@pytest.mark.unit
class TestTestSuiteValidator:
    """Test TestSuiteValidator functionality"""

    def test_validate_valid_suite(self):
        """Test validation of a well-formed test suite"""
        valid_test = """# Login Test

1. Navigate to https://example.com/login
2. Wait for page to load
3. Click on input#username
4. Type "testuser"
5. Click on input#password
6. Type "password123"
7. Click button#submit
8. Verify page contains "Dashboard"
9. Take screenshot"""

        result = TestSuiteValidator.validate(valid_test)

        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 0
        assert result["stats"]["total_steps"] == 9

    def test_validate_missing_title(self):
        """Test validation catches missing title"""
        test_no_title = """1. Navigate to page
2. Click button"""

        result = TestSuiteValidator.validate(test_no_title)

        assert len(result["warnings"]) > 0
        assert any("title" in w.lower() for w in result["warnings"])

    def test_validate_invalid_numbering(self):
        """Test validation catches numbering issues"""
        test_bad_numbers = """# Test
1. First step
3. Third step
2. Second step
5. Fifth step"""

        result = TestSuiteValidator.validate(test_bad_numbers)

        assert len(result["errors"]) > 0
        assert any(
            "number" in e.lower() or "sequence" in e.lower() for e in result["errors"]
        )

    def test_validate_empty_steps(self):
        """Test validation catches empty steps"""
        test_empty = """# Test
1. 
2. Click button
3. 
4. Verify result"""

        result = TestSuiteValidator.validate(test_empty)

        assert len(result["errors"]) > 0
        assert any("empty" in e.lower() for e in result["errors"])

    def test_validate_missing_waits(self):
        """Test validation warns about missing waits"""
        test_no_waits = """# Speed Test
1. Navigate to page
2. Click button immediately
3. Type text immediately
4. Submit immediately"""

        result = TestSuiteValidator.validate(test_no_waits)

        assert len(result["warnings"]) > 0
        assert any("wait" in w.lower() for w in result["warnings"])

    def test_validate_missing_verifications(self):
        """Test validation warns about missing verifications"""
        test_no_verify = """# Action Test
1. Navigate to form
2. Fill form
3. Submit form
4. Done"""

        result = TestSuiteValidator.validate(test_no_verify)

        assert len(result["warnings"]) > 0
        assert any(
            "verif" in w.lower() or "check" in w.lower() for w in result["warnings"]
        )

    def test_validate_vague_selectors(self):
        """Test validation warns about vague selectors"""
        test_vague = """# Vague Test
1. Click the button
2. Type in the field
3. Select the option"""

        result = TestSuiteValidator.validate(test_vague)

        assert len(result["warnings"]) > 0
        assert any(
            "specific" in w.lower() or "selector" in w.lower()
            for w in result["warnings"]
        )

    def test_validate_stats(self):
        """Test validation statistics"""
        test = """# Complete Test
1. Navigate to https://example.com
2. Wait for page to load
3. Click button#start
4. Verify element exists
5. Take screenshot
6. Type "test" in input#search
7. Take screenshot"""

        result = TestSuiteValidator.validate(test)
        stats = result["stats"]

        assert stats["total_steps"] == 7
        assert stats["navigation_steps"] == 1
        assert stats["wait_steps"] == 1
        assert stats["action_steps"] >= 2  # Click and Type
        assert stats["verification_steps"] == 1
        assert stats["screenshot_steps"] == 2

    def test_check_test_completeness(self):
        """Test completeness checking"""
        # Incomplete test
        incomplete = """# Login Test
1. Navigate to login
2. Type username
3. Type password"""

        complete_result = TestSuiteValidator.check_test_completeness(incomplete)
        assert complete_result["complete"] is False
        assert "submit" in " ".join(complete_result["missing_elements"]).lower()

        # Complete test
        complete = """# Login Test
1. Navigate to login page
2. Type username
3. Type password
4. Click submit button
5. Verify login successful"""

        complete_result = TestSuiteValidator.check_test_completeness(complete)
        assert complete_result["complete"] is True

    def test_empty_input(self):
        """Test handling of empty input"""
        result = TestSuiteValidator.validate("")

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert result["stats"]["total_steps"] == 0

    def test_malformed_input(self):
        """Test handling of malformed input"""
        malformed = """This is not a proper test format
Just some random text
Without proper numbering"""

        result = TestSuiteValidator.validate(malformed)

        assert len(result["errors"]) > 0
        assert result["stats"]["total_steps"] == 0
