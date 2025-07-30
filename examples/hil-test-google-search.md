# HIL Test: Google Search with User Query

This test demonstrates using the ask_human tool to get search input from the user (or automated response).

## Test Steps:

1. Navigate to www.google.com
2. Verify the Google search page has loaded by taking a screenshot
3. Use the ask_human tool to ask: "What would you like to search for?"
4. Enter the provided search term in the Google search box
5. Press Enter or click the Google Search button to submit the search
6. Wait for search results to load
7. Verify search results are displayed by taking a screenshot of the results page

## Expected HIL Behavior:

- The ask_human tool will trigger an interrupt at step 3
- In automated mode, it will provide a search term like "artificial intelligence"
- The agent will continue with the provided search term
- The test will complete without manual intervention

## Success Criteria:

- Google homepage loads successfully
- HIL interaction works properly with ask_human tool
- Search is performed with the provided term
- Results page is displayed and captured in screenshot