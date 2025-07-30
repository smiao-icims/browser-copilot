# HIL Retry Decision Test

This test demonstrates the ask_human tool's ability to make intelligent retry decisions
during test failures.

## Test Steps:

1. Navigate to httpstat.us/500 (this will return a 500 error)
2. Use the ask_human tool to ask: "The page returned a 500 server error. Should I retry the navigation or proceed with a different test scenario?"
3. Based on the response, either:
   - If "retry": Navigate to httpstat.us/200 (simulating a retry that succeeds)
   - If "proceed": Skip to step 5
4. Take a screenshot of the final page
5. Output: "Test completed with decision: [response]"

## Expected Behavior:

- The ask_human tool should intelligently decide to retry since 500 errors are often transient
- The agent should continue execution based on the decision
- The test should adapt its flow based on the HIL response
