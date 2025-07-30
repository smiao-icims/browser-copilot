# HIL Test: Google Search with User Query

This test is designed to trigger Human-in-the-Loop detection by intentionally asking for user input.

## Test Steps:

1. Navigate to www.google.com
2. Verify the Google search page has loaded by taking a screenshot
3. Output the message: "What would you like to search for?" (This will trigger HIL detection)
4. Wait for a response, then enter the provided search term in the Google search box
5. Press Enter or click the Google Search button to submit the search
6. Wait for search results to load
7. Verify search results are displayed by taking a screenshot

## Expected HIL Behavior:

At step 3, the agent should ask something like "What would you like to search for?" which should trigger HIL detection. The HIL handler should automatically provide a response to continue the test.

## Success Criteria:

- Google homepage loads successfully
- HIL is detected and handled automatically
- Search is performed without manual intervention
- Results page is displayed