# Browser Copilot - Common Use Cases 🎯

Real-world examples and patterns for effective browser automation testing.

## Table of Contents

1. [E-commerce Testing](#e-commerce-testing)
2. [Authentication & Security](#authentication--security)
3. [Form Testing](#form-testing)
4. [Search & Navigation](#search--navigation)
5. [Content Verification](#content-verification)
6. [Mobile Testing](#mobile-testing)
7. [Performance Testing](#performance-testing)
8. [Accessibility Testing](#accessibility-testing)
9. [Multi-Step Workflows](#multi-step-workflows)
10. [Error Handling Patterns](#error-handling-patterns)

## E-commerce Testing

### Complete Purchase Flow

```markdown
# E-commerce Purchase Flow Test

## Setup
1. Navigate to https://demo-store.com
2. Wait for page to load completely
3. Dismiss any popups or cookie banners

## Product Selection
4. Click on "Categories" menu
5. Select "Electronics"
6. Wait for products to load
7. Click on the first product with price under $100
8. Verify product details page loads
9. Select quantity "2"
10. Click "Add to Cart"
11. Verify cart notification appears

## Cart Management
12. Click on cart icon
13. Verify cart contains 2 items
14. Verify total price is calculated correctly
15. Apply coupon code "SAVE10"
16. Verify 10% discount is applied
17. Take screenshot of cart summary

## Checkout Process
18. Click "Proceed to Checkout"
19. Fill shipping information:
    - Full name: "Test User"
    - Email: "test@example.com"
    - Phone: "555-0123"
    - Address: "123 Test St"
    - City: "Test City"
    - ZIP: "12345"
    - Country: "United States"
20. Select "Standard Shipping"
21. Click "Continue to Payment"

## Payment
22. Select "Credit Card" payment method
23. Enter card number "4111 1111 1111 1111"
24. Enter expiry "12/25"
25. Enter CVV "123"
26. Enter name "Test User"
27. Check "Save for future purchases"
28. Click "Place Order"

## Confirmation
29. Wait for order confirmation
30. Verify "Order Successful" message
31. Verify order number is displayed
32. Take screenshot of confirmation page
33. Verify confirmation email message is shown
```

**Run with:**
```bash
browser-copilot ecommerce-flow.md --headless --output-format html --output-file purchase-report.html
```

### Inventory & Stock Testing

```markdown
# Stock Availability Test

1. Navigate to https://shop.example.com/limited-items
2. Find product "Limited Edition Item"
3. Verify stock count is displayed
4. Note the current stock number
5. Add maximum allowed quantity to cart
6. Verify error message if exceeding stock
7. Adjust quantity to available stock
8. Add to cart successfully
9. Return to product page
10. Verify stock count decreased
11. Take screenshot showing updated stock
```

## Authentication & Security

### Multi-Factor Authentication

```markdown
# MFA Login Test

1. Navigate to https://secure-app.com/login
2. Enter username "testuser@example.com"
3. Enter password "SecurePass123!"
4. Click "Sign In"
5. Wait for MFA prompt
6. Verify "Enter verification code" screen appears
7. Enter code "123456" (test environment)
8. Check "Remember this device for 30 days"
9. Click "Verify"
10. Wait for dashboard to load
11. Verify user profile shows correct email
12. Verify "MFA Active" badge is displayed
13. Take screenshot of secure dashboard
```

### OAuth/Social Login

```markdown
# Social Login Test

1. Navigate to https://app.example.com/login
2. Click "Continue with Google"
3. Wait for Google login page
4. Enter email "testaccount@gmail.com"
5. Click "Next"
6. Enter password "TestPass123"
7. Click "Next"
8. If prompted, click "Allow" for permissions
9. Wait for redirect back to app
10. Verify logged in successfully
11. Verify profile shows Google account info
12. Take screenshot of connected account
```

### Password Reset Flow

```markdown
# Password Reset Test

1. Navigate to https://app.example.com/login
2. Click "Forgot Password?"
3. Enter email "reset-test@example.com"
4. Click "Send Reset Link"
5. Verify "Email sent" confirmation appears
6. Navigate to https://app.example.com/reset?token=test123
7. Enter new password "NewSecurePass123!"
8. Enter confirm password "NewSecurePass123!"
9. Click "Reset Password"
10. Verify "Password updated" message
11. Try logging in with new password
12. Verify login successful
```

## Form Testing

### Complex Form Validation

```markdown
# Registration Form Test

## Basic Fields
1. Navigate to https://forms.example.com/register
2. Leave all fields empty
3. Click "Submit"
4. Verify all required field errors appear
5. Take screenshot of validation errors

## Field by Field Validation
6. Enter "a" in email field
7. Tab to next field
8. Verify "Invalid email format" error
9. Clear and enter "test@example.com"
10. Verify email error disappears

## Password Requirements
11. Enter "weak" in password field
12. Verify password strength indicator shows "Weak"
13. Verify requirements list shows:
    - ✗ At least 8 characters
    - ✗ One uppercase letter
    - ✗ One number
    - ✗ One special character
14. Enter "StrongPass123!"
15. Verify all requirements show ✓
16. Verify strength shows "Strong"

## Dependent Fields
17. Select "United States" from country
18. Verify state dropdown becomes enabled
19. Select "California" from state
20. Enter "94025" in ZIP code
21. Verify city auto-fills to "Menlo Park"

## File Upload
22. Click "Upload Avatar"
23. Select file "test-avatar.jpg"
24. Verify preview appears
25. Verify file size validation passes

## Terms and Submission
26. Check "I agree to terms"
27. Check "Subscribe to newsletter"
28. Click "Create Account"
29. Wait for processing
30. Verify success message
31. Take screenshot of confirmation
```

### Dynamic Form Fields

```markdown
# Dynamic Form Test

1. Navigate to https://app.example.com/survey
2. Select "Business" as account type
3. Verify business-specific fields appear:
   - Company name
   - Tax ID
   - Industry
4. Fill company name "Test Corp"
5. Select "Technology" from industry
6. Verify sub-industry dropdown appears
7. Select "Software Development"
8. Change account type to "Personal"
9. Verify business fields disappear
10. Verify personal fields appear:
    - Date of birth
    - SSN (masked)
11. Take screenshot showing field changes
```

## Search & Navigation

### Advanced Search with Filters

```markdown
# Product Search Test

## Basic Search
1. Navigate to https://shop.example.com
2. Click on search bar
3. Type "laptop"
4. Press Enter
5. Wait for results
6. Verify results contain "laptop" in titles

## Apply Filters
7. Click "Price" filter
8. Set minimum price to "500"
9. Set maximum price to "1500"
10. Click "Apply"
11. Verify all results are within price range

## Multiple Filters
12. Click "Brand" filter
13. Check "Dell"
14. Check "HP"
15. Check "Lenovo"
16. Click "Apply"
17. Verify results only show selected brands

## Sort Results
18. Click "Sort by" dropdown
19. Select "Price: Low to High"
20. Verify results are sorted correctly
21. Note first item price
22. Note last item price
23. Verify first <= last

## Save Search
24. Click "Save this search"
25. Enter name "Budget Laptops"
26. Click "Save"
27. Verify "Search saved" confirmation
28. Take screenshot of filtered results
```

### Auto-complete Search

```markdown
# Auto-complete Test

1. Navigate to https://search.example.com
2. Click search box
3. Type "app" slowly
4. Wait for suggestions to appear
5. Verify suggestions include:
   - "apple"
   - "application"
   - "appointment"
6. Use arrow key to select "apple"
7. Press Enter
8. Verify search executed for "apple"
9. Clear search
10. Type "xyz123" (no results)
11. Verify "No suggestions" message
12. Take screenshot of no results state
```

## Content Verification

### Table Data Validation

```markdown
# Data Table Test

1. Navigate to https://app.example.com/reports
2. Wait for table to load
3. Verify table headers are:
   - "Date"
   - "Transaction"
   - "Amount"
   - "Status"
4. Verify table has at least 10 rows
5. Click "Amount" header
6. Verify sorting arrow appears
7. Verify amounts are sorted ascending
8. Click "Amount" header again
9. Verify amounts are sorted descending
10. Search for "Refund" in table search
11. Verify only refund transactions shown
12. Verify all statuses show "Completed"
13. Click "Export" button
14. Select "CSV" format
15. Verify download started
16. Take screenshot of filtered table
```

### PDF Content Verification

```markdown
# PDF Report Test

1. Navigate to https://app.example.com/documents
2. Click "Generate Report"
3. Select date range:
   - From: "01/01/2024"
   - To: "12/31/2024"
4. Click "Generate PDF"
5. Wait for generation to complete
6. Click "View PDF"
7. Wait for PDF to load in browser
8. Verify PDF header contains "Annual Report 2024"
9. Verify page count is at least 10
10. Click "Download PDF"
11. Verify download completes
12. Take screenshot of PDF viewer
```

## Mobile Testing

### Responsive Design Test

```markdown
# Mobile Responsive Test

1. Navigate to https://responsive.example.com
2. Take screenshot of desktop view
3. Verify navigation menu is horizontal
4. Verify 3 columns of content
5. Note: Run with --device "iPhone 12"
6. Verify navigation becomes hamburger menu
7. Verify content is single column
8. Click hamburger menu
9. Verify mobile menu slides in
10. Verify all menu items are visible
11. Tap outside menu
12. Verify menu closes
13. Scroll to bottom
14. Verify footer is stacked vertically
15. Take screenshot of mobile view
```

**Run mobile test:**
```bash
browser-copilot mobile-test.md --device "iPhone 12" --output-format html
```

### Touch Gestures

```markdown
# Touch Interaction Test

1. Navigate to https://touch.example.com/gallery
2. Verify image gallery loads
3. Swipe left on first image
4. Verify second image appears
5. Swipe left again
6. Verify third image appears
7. Pinch to zoom on image
8. Verify image zooms in
9. Double tap image
10. Verify image returns to normal size
11. Long press on image
12. Verify context menu appears
13. Tap "Save Image"
14. Verify save confirmation
15. Take screenshot of gallery
```

## Performance Testing

### Page Load Performance

```markdown
# Performance Test

1. Navigate to https://app.example.com
2. Wait for full page load
3. Verify page loads within 3 seconds
4. Open developer tools (F12)
5. Go to Network tab
6. Refresh page
7. Wait for load to complete
8. Verify no requests take > 1 second
9. Verify total page size < 5MB
10. Verify no 404 errors
11. Verify no console errors
12. Take screenshot of network panel
```

### Lazy Loading Verification

```markdown
# Lazy Load Test

1. Navigate to https://media.example.com/gallery
2. Verify first 10 images are loaded
3. Note network request count
4. Scroll down slowly
5. Verify new images load as they appear
6. Continue scrolling to bottom
7. Verify all images eventually load
8. Scroll back to top quickly
9. Verify no images are missing
10. Take screenshot showing loaded state
```

## Accessibility Testing

### Keyboard Navigation

```markdown
# Keyboard Navigation Test

1. Navigate to https://accessible.example.com
2. Press Tab key
3. Verify focus indicator is visible
4. Verify focus moves to first interactive element
5. Press Tab 5 times
6. Verify focus moves through elements in logical order
7. Press Shift+Tab
8. Verify focus moves backward
9. Press Enter on focused link
10. Verify navigation occurs
11. Press Tab to focus dropdown
12. Press Space to open dropdown
13. Use arrow keys to select option
14. Press Enter to confirm
15. Verify selection is made
16. Take screenshot showing focus indicators
```

### Screen Reader Labels

```markdown
# Accessibility Labels Test

1. Navigate to https://app.example.com/form
2. Inspect search button
3. Verify aria-label="Search products"
4. Inspect close button (X)
5. Verify aria-label="Close dialog"
6. Inspect progress bar
7. Verify aria-valuenow matches visual progress
8. Inspect error message
9. Verify role="alert"
10. Inspect main navigation
11. Verify role="navigation"
12. Take screenshot with inspector open
```

## Multi-Step Workflows

### Wizard Form Completion

```markdown
# Multi-Step Wizard Test

## Step 1: Personal Info
1. Navigate to https://wizard.example.com/apply
2. Verify step 1 of 4 is active
3. Fill first name "John"
4. Fill last name "Doe"
5. Fill email "john.doe@example.com"
6. Click "Next"

## Step 2: Address
7. Verify step 2 of 4 is active
8. Verify email from step 1 is shown
9. Fill address "123 Main St"
10. Fill city "Springfield"
11. Select state "IL"
12. Fill ZIP "62701"
13. Click "Next"

## Step 3: Preferences
14. Verify step 3 of 4 is active
15. Select interest "Technology"
16. Select interest "Sports"
17. Set notification preference "Weekly"
18. Toggle "Email updates" ON
19. Click "Next"

## Step 4: Review
20. Verify step 4 of 4 is active
21. Verify all entered data is displayed
22. Click "Edit" next to email
23. Verify returned to step 1
24. Verify data is preserved
25. Click "Next" three times to return to review
26. Check "I confirm all information is correct"
27. Click "Submit Application"
28. Wait for confirmation
29. Verify "Application submitted" message
30. Verify reference number is shown
31. Take screenshot of confirmation
```

### Booking System Flow

```markdown
# Appointment Booking Test

## Service Selection
1. Navigate to https://booking.example.com
2. Select service "Consultation"
3. Verify duration shows "1 hour"
4. Verify price shows "$100"
5. Click "Book Now"

## Date Selection
6. Verify calendar appears
7. Verify past dates are disabled
8. Click next month arrow
9. Select first available Tuesday
10. Verify selected date is highlighted

## Time Selection
11. Verify available time slots appear
12. Verify morning slots: 9 AM - 12 PM
13. Verify afternoon slots: 1 PM - 5 PM
14. Select "2:00 PM"
15. Click "Continue"

## Customer Details
16. Fill name "Jane Smith"
17. Fill email "jane.smith@example.com"
18. Fill phone "555-0123"
19. Add notes "First time customer"
20. Check "Receive reminder"
21. Click "Continue"

## Payment
22. Verify booking summary shows:
    - Service: Consultation
    - Date: [Selected date]
    - Time: 2:00 PM
    - Price: $100
23. Select "Pay at venue"
24. Click "Confirm Booking"

## Confirmation
25. Wait for processing
26. Verify "Booking confirmed" message
27. Verify booking ID is displayed
28. Verify "Add to calendar" button appears
29. Take screenshot of confirmation
30. Verify confirmation email notice
```

## Error Handling Patterns

### Network Error Recovery

```markdown
# Network Error Test

1. Navigate to https://app.example.com/upload
2. Select large file "test-video.mp4"
3. Click "Upload"
4. Wait for upload to start
5. Verify progress bar appears
6. When progress reaches 50%, simulate network disconnect
7. Verify "Connection lost" error appears
8. Verify "Retry" button is shown
9. Restore network connection
10. Click "Retry"
11. Verify upload resumes from 50%
12. Wait for upload to complete
13. Verify "Upload successful" message
14. Take screenshot of success state
```

### Validation Error Recovery

```markdown
# Form Error Recovery Test

1. Navigate to https://app.example.com/profile
2. Clear all required fields
3. Click "Save Changes"
4. Verify error summary appears at top
5. Verify individual field errors shown
6. Take screenshot of error state
7. Click on first error in summary
8. Verify focus moves to that field
9. Fill in the required field
10. Verify error for that field disappears
11. Fill all remaining required fields
12. Click "Save Changes"
13. Verify all errors cleared
14. Verify "Profile updated" success message
```

## Best Practices Tips

### 1. Use Explicit Waits
```markdown
# Good: Explicit wait
1. Click "Load Data"
2. Wait for "Loading..." to disappear
3. Wait for table to contain at least 1 row
4. Verify data is displayed

# Avoid: Arbitrary time waits
1. Click "Load Data"
2. Wait 5 seconds
3. Verify data is displayed
```

### 2. Be Specific with Selectors
```markdown
# Good: Specific identification
1. Click the "Submit Order" button in the checkout section
2. Click on the email input field with placeholder "Enter your email"

# Avoid: Ambiguous selectors
1. Click "Submit"
2. Click on input field
```

### 3. Verify State Changes
```markdown
# Good: Verify each state
1. Verify cart shows "0 items"
2. Add product to cart
3. Verify cart shows "1 item"
4. Verify cart total updates

# Avoid: Assuming state
1. Add product to cart
2. Go to checkout
```

### 4. Handle Dynamic Content
```markdown
# Good: Handle loading states
1. Click "Search"
2. Wait for spinner to appear
3. Wait for spinner to disappear
4. Wait for results to load
5. Verify at least 1 result appears

# Avoid: Fixed expectations
1. Click "Search"
2. Verify 10 results appear
```

## Running These Examples

### Basic Execution
```bash
browser-copilot use-case.md
```

### With Specific Options
```bash
# Headless with HTML report
browser-copilot use-case.md --headless --output-format html --output-file report.html

# Mobile testing
browser-copilot mobile-case.md --device "iPhone 12"

# With high compression for cost savings
browser-copilot long-test.md --compression-level high

# Verbose mode for debugging
browser-copilot failing-test.md --verbose
```

### Custom System Prompts
For better reliability with complex tests, create domain-specific prompts:

`ecommerce-prompt.txt`:
```
You are testing an e-commerce site. Always:
1. Wait for price updates after cart changes
2. Verify inventory before adding to cart
3. Check for sale prices and discounts
4. Capture order numbers and confirmations
5. Handle pop-ups for newsletters or promotions
```

Use: `browser-copilot shop-test.md --system-prompt ecommerce-prompt.txt`