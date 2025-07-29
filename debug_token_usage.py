#!/usr/bin/env python3
"""Debug script to check token usage flow"""

import asyncio
import json
from browser_copilot.core import BrowserPilot

async def debug_token_usage():
    # Create a simple test
    pilot = BrowserPilot(
        provider="github_copilot", 
        model="gpt-4o"
    )
    
    test_content = """
# Debug Test
1. Navigate to https://example.com
2. Take a screenshot
"""
    
    # Run test
    result = await pilot.run_test_suite(
        test_content,
        browser="chromium",
        headless=True,
        timeout=30
    )
    
    # Print result structure
    print("Result keys:", list(result.keys()))
    print("\nToken usage data:")
    if "token_usage" in result:
        print(json.dumps(result["token_usage"], indent=2))
    else:
        print("No token_usage in result!")
    
    # Check if telemetry has data
    if hasattr(pilot, 'telemetry') and pilot.telemetry:
        print("\nTelemetry object exists")
        if hasattr(pilot.telemetry, 'metrics'):
            print("Telemetry has metrics")
        
    return result

if __name__ == "__main__":
    asyncio.run(debug_token_usage())