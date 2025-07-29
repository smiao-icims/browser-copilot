#!/usr/bin/env python3
"""
Debug script to understand why tests are marked as FAILED
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from browser_copilot.core import BrowserPilot


def check_success_patterns():
    """Test the _check_success method with various inputs"""
    
    automation = BrowserPilot("test", "test")
    
    test_reports = [
        # Test 1: Proper format
        """
# Test Execution Report

## Summary
- Overall Status: PASSED
- Duration: 60 seconds

## Test Results
Successfully completed all steps.
        """,
        
        # Test 2: Different format
        """
### Test Execution Summary

#### Overall Status: PASSED

All tests completed successfully.
        """,
        
        # Test 3: Your actual output
        """
- Successfully logged out and returned to the login page.
- Verified that the username and password fields are empty.

### Test Execution Summary

#### Overall Status: PASSED
        """,
        
        # Test 4: Mixed case
        """
# TEST EXECUTION REPORT

Overall status: PASSED
        """,
        
        # Test 5: Failed test
        """
# Test Execution Report

## Summary
- Overall Status: FAILED
- Error: Could not find element
        """
    ]
    
    print("Testing _check_success patterns:\n")
    
    for i, report in enumerate(test_reports, 1):
        result = automation._check_success(report)
        print(f"Test {i}: {'PASS' if result else 'FAIL'}")
        print(f"Report preview: {report.strip()[:100]}...")
        print(f"Has 'test execution report': {'test execution report' in report.lower()}")
        print(f"Has success pattern: {any(p in report.lower() for p in ['overall status:** passed', 'overall status: passed', 'status:** passed', 'status: passed'])}")
        print("-" * 60)


if __name__ == "__main__":
    check_success_patterns()