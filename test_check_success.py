#!/usr/bin/env python3
"""
Test the _check_success logic
"""

def check_success(report_content: str) -> bool:
    """
    Copied from BrowserPilot._check_success
    """
    if not report_content:
        return False

    lower_content = report_content.lower()

    # Check various success patterns
    success_patterns = [
        "overall status:** passed",
        "overall status: passed",
        "status:** passed",
        "status: passed",
        "all tests passed",
        "test passed successfully",
    ]

    # Must have test execution report
    has_report = "test execution report" in lower_content

    # Check for any success pattern
    has_success = any(pattern in lower_content for pattern in success_patterns)

    # Check for explicit failure
    has_failure = any(
        fail in lower_content
        for fail in [
            "overall status:** failed",
            "overall status: failed",
            "test failed",
        ]
    )

    return has_report and has_success and not has_failure


def test_patterns():
    """Test various report formats"""
    
    test_cases = [
        # Test 1: Standard format (should PASS)
        ("""
# Test Execution Report

## Summary
- Overall Status: PASSED
- Duration: 60 seconds
        """, "Standard format"),
        
        # Test 2: Markdown bold format (should PASS)
        ("""
# Test Execution Report

**Overall Status:** PASSED
        """, "Markdown bold format"),
        
        # Test 3: Your actual test output (should PASS but might not)
        ("""
### Test Execution Summary

#### Overall Status: PASSED

- Successfully logged out and returned to the login page.
- Verified that the username and password fields are empty.
        """, "Your actual output format"),
        
        # Test 4: Without "Test Execution Report" header (should FAIL)
        ("""
## Summary
- Overall Status: PASSED
        """, "Missing report header"),
        
        # Test 5: Case variations (should PASS)
        ("""
# TEST EXECUTION REPORT

Overall status: passed
        """, "Case variations"),
        
        # Test 6: Failed test (should FAIL)
        ("""
# Test Execution Report

Overall Status: FAILED
        """, "Failed test"),
    ]
    
    print("Testing _check_success patterns:\n")
    print("=" * 80)
    
    for content, description in test_cases:
        result = check_success(content)
        lower = content.lower()
        
        print(f"\nTest: {description}")
        print(f"Result: {'✅ PASS' if result else '❌ FAIL'}")
        print(f"Content preview: {content.strip()[:100]}...")
        print(f"\nChecks:")
        print(f"  - Has 'test execution report': {'✅' if 'test execution report' in lower else '❌'}")
        print(f"  - Has success pattern: {'✅' if any(p in lower for p in ['overall status:** passed', 'overall status: passed', 'status:** passed', 'status: passed']) else '❌'}")
        print(f"  - Has failure pattern: {'✅' if any(p in lower for p in ['overall status:** failed', 'overall status: failed', 'test failed']) else '❌'}")
        print("-" * 80)


if __name__ == "__main__":
    test_patterns()
    
    print("\n\nKEY INSIGHTS:")
    print("1. The report MUST contain 'test execution report' (case insensitive)")
    print("2. The report MUST contain a success pattern like 'overall status: passed'")
    print("3. The report MUST NOT contain failure patterns")
    print("\nYour test likely failed because the AI didn't include 'Test Execution Report' as a header")