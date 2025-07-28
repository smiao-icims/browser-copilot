# SauceDemo E-commerce Shopping Flow

A complete end-to-end shopping example using the SauceDemo test site. This example demonstrates login, product selection, cart management, and checkout.

## Test Site Information
- URL: https://www.saucedemo.com
- Username: enter "standard_user"
- Password: enter "secret_sauce"

## Test: Complete Shopping Flow

### Phase 1: Login
1. Navigate to https://www.saucedemo.com
2. Wait for the login page to load completely
3. Take a screenshot of the login page
4. Click on the "Username" textbox
5. Type "standard_user" into the username field
6. Click on the "Password" textbox
7. Type "secret_sauce" into the password field
8. Click the "Login" button
9. Wait for the page to load
10. Verify the products page is displayed (URL should contain "/inventory.html")
11. Verify the page title shows "Swag Labs"

### Phase 2: Browse and Add Products
12. Verify at least 6 products are displayed on the inventory page
13. Locate the "Sauce Labs Backpack" product on the page
14. Click the "Add to cart" button for the Sauce Labs Backpack
15. Wait for the button to change to "Remove"
16. Verify the shopping cart badge shows "1"
17. Locate the "Sauce Labs Bike Light" product on the page
18. Click the "Add to cart" button for the Sauce Labs Bike Light
19. Wait for the button to change to "Remove"
20. Verify the shopping cart badge now shows "2"
21. Take a screenshot of the products page with items in cart

### Phase 3: Review Cart
22. Click on the shopping cart badge in the top right corner
23. Wait for the cart page to load
24. Verify the cart page is displayed (URL should contain "/cart.html")
25. Verify both items are in the cart:
    - Sauce Labs Backpack ($29.99)
    - Sauce Labs Bike Light ($9.99)
26. Find the "Remove" button for the Sauce Labs Bike Light and click it
27. Wait for the item to be removed from the cart
28. Verify only the Sauce Labs Backpack remains in the cart
29. Click the "Checkout" button

### Phase 4: Checkout Process
30. Wait for the checkout page to load
31. Verify checkout page is displayed (URL should contain "/checkout-step-one.html")
32. For the First Name field: Click on the "First Name" input field, then immediately type "Test" in that field
33. For the Last Name field: Click on the "Last Name" input field, then immediately type "User" in that field  
34. For the Postal Code field: Click on the "Zip/Postal Code" input field, then immediately type "12345" in that field
35. Click the "Continue" button
36. Wait for the checkout overview page to load
37. Verify checkout overview page is displayed (URL should contain "/checkout-step-two.html")
38. Verify the item total shows "$29.99"
39. Verify tax is calculated (should be "$2.40")
40. Verify the total is "$32.39"
41. Take a screenshot of the checkout overview
42. Click the "Finish" button

### Phase 5: Order Confirmation
43. Wait for the order confirmation page to load
44. Verify order complete page is displayed (URL should contain "/checkout-complete.html")
45. Verify success message: "Thank you for your order!"
46. Verify the pony express delivery image is displayed
47. Take a screenshot of the confirmation page
48. Click the "Back Home" button

### Phase 6: Logout
49. Wait for the inventory page to load
50. Click the "Open Menu" button in the top left corner
51. Wait for the side menu to slide open
52. Click the "Logout" link from the menu
53. Wait for the login page to load
54. Verify you have returned to the login page
55. Verify the username and password fields are empty

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