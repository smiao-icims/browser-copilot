# HIL Test: Form with Multiple Choice Decisions

This test is designed to trigger Human-in-the-Loop detection through choice requests.

## Test Steps:

1. Navigate to https://www.w3schools.com/html/html_forms.asp
2. Scroll to find a form example
3. Ask which form values the user prefers to fill in
4. Fill the form with the chosen values
5. Ask if the user wants to submit the form or make changes
6. Submit the form if confirmed

## Expected HIL Triggers:

- Step 3: "Which values would you like me to use for the form fields?"
- Step 5: "Should I submit the form now, or would you like to make changes?"

## Success Criteria:

- Form page loads successfully
- Multiple HIL detections occur and are handled
- Form is filled and submitted automatically
- No manual intervention required