# Browser Copilot Best Practices

## Common Issues and Solutions

### Form Field Focus Issues

**Problem**: The first field in a form (especially "First Name") is often missed or not properly filled.

**Solution**: 
1. Always explicitly click on form fields before typing
2. Make sure to complete each field before moving to the next
3. Use clear, sequential test instructions:
   ```markdown
   Instead of: "Click on the First Name field and type 'Test'"
   Better: "For the First Name field: Click on the 'First Name' input field, then immediately type 'Test' in that field"
   ```
   
**Common Mistake**: The AI might interpret instructions to click all fields first, then type in all of them. This causes the first fields to lose focus.

3. For critical forms, consider adding a verification step:
   ```markdown
   1. Take a snapshot of the form
   2. Click on the First Name field
   3. Type "Test"
   4. Verify the field contains "Test" before proceeding
   ```

### Custom System Prompts

You can provide a custom system prompt to improve form handling:

```bash
# Create a custom prompt file
cat > form-prompt.txt << 'EOF'
When filling out forms:
1. Always click on each field before typing to ensure proper focus
2. For the first field in any form, click it twice if needed
3. Wait 500ms after clicking before typing
4. Verify the field has focus by checking for a cursor or highlight
5. If text doesn't appear, click the field again and retry
EOF

# Use the custom prompt
browser-copilot test.md --system-prompt form-prompt.txt
```

### Writing Better Test Instructions

#### Good Practices:
- Be explicit about clicking fields before typing
- Add verification steps after critical actions
- Include wait instructions for dynamic content
- Specify exact text to look for in verifications

#### Example Test Format:
```markdown
## Checkout Form Test

1. Navigate to checkout page
2. Wait for the form to fully load
3. Take a screenshot of the empty form
4. **Focus and fill First Name field:**
   - Click on the "First Name" input field
   - Ensure the field has focus (cursor should be visible)
   - Type "John"
   - Verify the field now contains "John"
5. **Focus and fill Last Name field:**
   - Click on the "Last Name" input field
   - Type "Doe"
6. Continue with other fields...
```

### Debugging Failed Form Fills

If forms are consistently failing:

1. **Enable verbose mode** to see exactly what the AI is doing:
   ```bash
   browser-copilot test.md --verbose
   ```

2. **Add explicit waits** in your test:
   ```markdown
   1. Click on First Name field
   2. Wait for 1 second
   3. Type "Test"
   ```

3. **Use snapshots** to verify field state:
   ```markdown
   1. Take a snapshot before clicking the field
   2. Click on First Name field
   3. Take another snapshot to verify cursor is in the field
   4. Type "Test"
   ```

### Browser-Specific Considerations

Some browsers handle form focus differently:
- **Chrome/Chromium**: Generally reliable with standard click-then-type
- **Firefox**: May require additional wait time between click and type
- **Safari/WebKit**: Sometimes needs explicit focus commands

Consider testing with different browsers if you encounter consistent issues:
```bash
browser-copilot test.md --browser firefox
browser-copilot test.md --browser webkit
```