# Test Writing Guide

This guide covers best practices for writing effective test suites for Browser Copilot.

## Test Structure

Browser Copilot tests are written in Markdown format with numbered steps. Each test should have:

1. **Clear Title**: Descriptive name for the test scenario
2. **Numbered Steps**: Sequential actions to perform
3. **Expected Results**: What should happen
4. **Optional Sections**: Setup, teardown, notes

## Basic Test Format

```markdown
# [Test Name]

## Test Description (optional)
Brief description of what this test validates.

## Test Steps

1. First action to perform
2. Second action with specific details
3. Verification step
4. Continue with more steps...

## Expected Results

- First expected outcome
- Second expected outcome
- Final state verification
```

## Writing Effective Steps

### Be Specific

❌ Bad:
```markdown
1. Go to the login page
2. Login
3. Check if it worked
```

✅ Good:
```markdown
1. Navigate to https://example.com/login
2. Enter "testuser@example.com" in the email field
3. Enter "password123" in the password field
4. Click the "Sign In" button
5. Verify the dashboard displays "Welcome, Test User"
```

### Include Verifications

Always include steps to verify actions completed successfully:

```markdown
1. Click the "Add to Cart" button
2. Wait for the cart icon to update
3. Verify the cart count shows "1"
4. Take a screenshot of the updated cart
```

### Handle Dynamic Content

For pages with loading states:

```markdown
1. Navigate to https://example.com/products
2. Wait for the loading spinner to disappear
3. Wait for product grid to be visible
4. Verify at least 10 products are displayed
```

## Common Patterns

### Form Filling

```markdown
1. Navigate to https://example.com/register
2. Fill in the registration form:
   - Enter "John" in the first name field
   - Enter "Doe" in the last name field
   - Enter "john.doe@example.com" in the email field
   - Enter "SecurePass123!" in the password field
   - Enter "SecurePass123!" in the confirm password field
3. Check the "I agree to terms" checkbox
4. Click the "Create Account" button
5. Wait for confirmation page
6. Verify "Account created successfully" message appears
```

### Navigation Testing

```markdown
1. Navigate to https://example.com
2. Click on "Products" in the main navigation
3. Verify the URL changes to "/products"
4. Click on "About Us" in the navigation
5. Verify the page heading contains "About"
6. Use browser back button
7. Verify we're back on the products page
```

### Search Functionality

```markdown
1. Navigate to https://example.com
2. Locate the search bar
3. Type "wireless headphones" in the search field
4. Press Enter to search
5. Wait for search results to load
6. Verify search results contain "wireless" and "headphones"
7. Count and report the number of results
8. Take a screenshot of the search results
```

## Multi-Phase Tests

For complex scenarios, use phase markers:

```markdown
# E-Commerce Purchase Test

---PHASE---
## Phase 1: Product Selection

1. Navigate to https://shop.example.com
2. Search for "laptop"
3. Filter by price: $500-$1000
4. Sort by "Customer Rating"
5. Select the first product
6. Add to cart

---PHASE---
## Phase 2: Checkout

1. Go to cart
2. Verify product is in cart
3. Click "Proceed to Checkout"
4. Fill in shipping information
5. Select shipping method
6. Continue to payment

---PHASE---
## Phase 3: Order Confirmation

1. Verify order summary
2. Take screenshot of order details
3. Note the order number
4. Verify confirmation email instructions
```

## Best Practices

### 1. Use Descriptive Actions

Instead of generic instructions, be specific about what to look for:

```markdown
1. Find the search box (usually in the header with a magnifying glass icon)
2. Look for the "Sign In" button (typically in the top-right corner)
3. Locate the shopping cart icon (shows item count)
```

### 2. Include Wait Conditions

Always specify when to wait:

```markdown
1. Click "Submit"
2. Wait for the form to be processed
3. Wait until the success message appears
4. Wait for the page to redirect to dashboard
```

### 3. Capture Evidence

Take screenshots at key points:

```markdown
1. Take a screenshot of the login page
2. Enter credentials
3. Click login
4. Take a screenshot after login (success or error)
5. If error, capture the error message
```

### 4. Handle Errors Gracefully

Include alternative paths:

```markdown
1. Click "Accept Cookies" if cookie banner appears
2. If popup appears, close it by clicking the X button
3. If CAPTCHA is present, note it and skip to next section
```

### 5. Provide Context

Add notes for complex scenarios:

```markdown
## Note: Test Account
Use these test credentials:
- Email: test@example.com
- Password: TestPass123!

## Note: Expected Behavior
The system may show a one-time welcome message on first login.
This is normal and should be dismissed.
```

## Anti-Patterns to Avoid

### 1. Vague Instructions

❌ "Check if the page works"
✅ "Verify the page loads without errors and displays the company logo"

### 2. Missing Verifications

❌ "Click submit"
✅ "Click submit and verify the confirmation message appears"

### 3. Hardcoded Waits

❌ "Wait 5 seconds"
✅ "Wait for the loading indicator to disappear"

### 4. Assuming State

❌ "Click logout" (assumes user is logged in)
✅ "If logged in (check for username in header), click logout"

## Advanced Techniques

### Dynamic Content Handling

```markdown
1. Navigate to product listing
2. Note the initial number of products
3. Scroll to bottom of page
4. Wait for lazy-loaded content
5. Verify more products loaded
6. Compare new count with initial count
```

### Accessibility Testing

```markdown
1. Take accessibility snapshot of page
2. Verify all images have alt text
3. Check that form fields have labels
4. Ensure interactive elements are keyboard accessible
```

### Performance Considerations

```markdown
1. Navigate to homepage
2. Note the time when page starts loading
3. Wait for main content to be visible
4. Calculate and report load time
5. Verify load time is under 3 seconds
```

## Test Maintenance

Keep tests maintainable by:

1. **Using stable selectors**: Prefer text content over CSS classes
2. **Avoiding brittle XPaths**: Use semantic elements
3. **Documenting assumptions**: Note any dependencies
4. **Keeping tests focused**: One scenario per test
5. **Regular updates**: Review tests when UI changes

## Example: Complete Test Suite

Here's a well-structured test example:

```markdown
# User Registration and Profile Setup Test

## Test Description
This test validates the complete user registration flow including email
verification and initial profile setup.

## Prerequisites
- Valid email address for testing
- Access to email inbox for verification

## Test Steps

### Registration
1. Navigate to https://example.com/register
2. Wait for registration form to load completely
3. Take screenshot of empty registration form
4. Fill in the registration details:
   - First Name: "Test"
   - Last Name: "User"
   - Email: "testuser@example.com"
   - Password: "SecurePass123!"
   - Confirm Password: "SecurePass123!"
5. Check "I agree to Terms of Service" checkbox
6. Check "I am 18 years or older" checkbox
7. Click "Create Account" button
8. Wait for processing (spinner should appear then disappear)
9. Verify success message: "Account created! Please check your email."
10. Take screenshot of success message

### Email Verification (Simulated)
11. Click "Resend Verification Email" link
12. Verify "Email sent" notification appears
13. For testing, click "Use Test Verification Link"
14. Wait for redirect to profile setup

### Profile Setup
15. Verify we're on profile setup page (URL contains "/profile/setup")
16. Upload profile picture (use test image if available)
17. Enter bio: "This is a test account for automated testing"
18. Select timezone: "America/New_York"
19. Choose notification preferences:
    - Email notifications: Yes
    - SMS notifications: No
20. Click "Complete Setup" button
21. Wait for dashboard to load
22. Verify welcome message displays username
23. Take final screenshot of completed setup

## Expected Results

- Registration form validates all required fields
- Account creation is successful
- Email verification process works (simulated)
- Profile setup saves all information
- User lands on personalized dashboard
- All screenshots captured successfully

## Cleanup Notes
Test account can be deleted through Settings > Account > Delete Account
```

## Conclusion

Writing good tests is an art that improves with practice. Focus on clarity, completeness, and maintainability. Remember that your tests are documentation of how your application should work, so write them as if someone unfamiliar with the system needs to understand and run them.