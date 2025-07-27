# SauceDemo E-commerce Shopping Flow

A complete end-to-end shopping example using the SauceDemo test site. This example demonstrates login, product selection, cart management, and checkout.

## Test Site Information
- URL: https://www.saucedemo.com
- Username: enter "standard_user"
- Password: enter "secret_sauce"

## Test: Complete Shopping Flow

### Phase 1: Login
1. Navigate to https://www.saucedemo.com
2. Wait for the login page to load
3. Take a screenshot of the login page
4. Allocate username field: enter "standard_user" as user name
5. Allocate password field: enter "secret_sauce" as password
6. Click the "Login" button
7. Verify the products page is displayed (URL should contain "/inventory.html")
8. Verify the page title shows "Swag Labs"

### Phase 2: Browse and Add Products
8. Verify at least 6 products are displayed
9. Find the "Sauce Labs Backpack" product
10. Click "Add to cart" button for the backpack
11. Verify the cart badge shows "1"
12. Find the "Sauce Labs Bike Light" product
13. Click "Add to cart" button for the bike light
14. Verify the cart badge now shows "2"
15. Take a screenshot of the products page with items in cart

### Phase 3: Review Cart
16. Click on the shopping cart icon (top right)
17. Verify the cart page is displayed (URL should contain "/cart.html")
18. Verify both items are in the cart:
    - Sauce Labs Backpack ($29.99)
    - Sauce Labs Bike Light ($9.99)
19. Remove the bike light from cart by clicking its "Remove" button
20. Verify only the backpack remains in the cart
21. Click "Checkout" button

### Phase 4: Checkout Process
22. Verify checkout page is displayed (URL should contain "/checkout-step-one.html")
23. Fill in checkout information:
    - First Name: "Test"
    - Last Name: "User"
    - Zip/Postal Code: "12345"
24. Click "Continue" button
25. Verify checkout overview page (URL should contain "/checkout-step-two.html")
26. Verify the item total shows "$29.99"
27. Verify tax is calculated (should be "$2.40")
28. Verify total is "$32.39"
29. Take a screenshot of the checkout overview
30. Click "Finish" button

### Phase 5: Order Confirmation
31. Verify order complete page (URL should contain "/checkout-complete.html")
32. Verify success message: "Thank you for your order!"
33. Verify the pony express image is displayed
34. Take a screenshot of the confirmation
35. Click "Back Home" button

### Phase 6: Logout
36. Click the hamburger menu (top left)
37. Wait for the menu to slide open
38. Click "Logout" from the menu
39. Verify return to login page
40. Verify the username and password fields are empty

## Expected Results
- All phases should complete successfully
- Total execution time should be under 60 seconds
- Three screenshots should be captured
- No errors should occur during the flow

## Variations

### Different User Scenarios
```markdown
# Problem User (UI Issues)
Username: problem_user
Password: secret_sauce
Note: Some products will have incorrect images

# Performance Glitch User (Slow Loading)
Username: performance_glitch_user  
Password: secret_sauce
Note: All actions will have delays

# Locked Out User (Login Failure)
Username: locked_out_user
Password: secret_sauce
Expected: Login should fail with error message
```

### Additional Test Scenarios
- Sort products by price (low to high)
- Sort products by name (Z to A)
- Add all products to cart
- Verify product details page
- Test cart persistence across sessions

## Notes
- This is a public demo site maintained by SauceLabs
- The site resets periodically, so cart contents don't persist
- All test data is safe to use and won't affect real systems
- The site is designed to handle automation traffic