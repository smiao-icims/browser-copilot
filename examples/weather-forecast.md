# Weather Forecast Lookup Example

A simple test to find today's weather forecast for a specific location using weather.com.

## Test: Check Weather Forecast

### Input Parameters
- City or Zipcode: "10001" (or "New York, NY")

### Test Steps

1. Navigate to https://weather.com
2. Wait for page to load completely
3. **CRITICAL DIALOG HANDLING**: 
   - when "weather.com” would like to use your current location dialog appears, answer "Allow"
   - dismiss any other pop-ups or dialogs that may appear
4. find the search box (usually labeled "Search City or Zip Code")
5. Enter "10001" in the search field
6. Press Enter or click the search button  
7. Wait for results to load
8. Verify the location shows "New York, NY" or "Manhattan, NY"
9. Find and record today's temperature (both high and low)
10. Find and record today's weather conditions (e.g., "Partly Cloudy", "Rain")
11. Check if there are any weather alerts
12. Take a screenshot of the forecast

### Expected Results
- Weather forecast for the specified location should be displayed
- Current temperature should be visible
- Today's high/low temperatures should be shown
- Weather conditions should be clearly stated
- Any active weather alerts should be highlighted

### Variations

You can modify this test for different scenarios:

```markdown
# International Location
- City: "London, UK"
- Verify temperature is shown in Celsius

# Extended Forecast
- After step 11, click on "10 Day Forecast"
- Verify extended forecast is displayed
- Record weather for the next 3 days

# Hourly Forecast
- After step 11, click on "Hourly"
- Verify hourly breakdown is shown
- Check precipitation chance for next 6 hours
```

### Notes
- The search box location may vary based on weather.com's current design
- Some locations might redirect to a more specific area (e.g., "10001" → "Manhattan, NY")
- Weather alerts are location and time-specific