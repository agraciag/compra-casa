# Property Comparison Metrics

## Overview
To effectively compare properties from different sources, we need standardized metrics that account for various factors affecting value and livability.

## Core Financial Metrics

### 1. Price Per Square Meter
- Formula: price / surface_area
- Benchmark against neighborhood averages
- Identify undervalued properties
- Compare with official statistics (Penotariado, Tinsa)

### 2. Value Score
- Weighted calculation considering:
  - Price per sqm relative to neighborhood average (40%)
  - Property condition (20%)
  - Amenities and features (20%)
  - Location quality (20%)

### 3. Affordability Ratios
- Price to annual income multiples
- Monthly payment to income ratios
- Total cost of ownership estimates

## Property Quality Metrics

### 4. Space Efficiency
- Usable space ratio (living area / total area)
- Room layout efficiency
- Natural light assessment (if available)

### 5. Feature Score
- Presence of desirable features:
  - Elevator (especially for higher floors)
  - Parking space
  - Terrace/balcony
  - Storage room
  - Air conditioning
  - Energy efficiency rating

### 6. Age and Condition Adjustment
- Depreciation based on construction year
- Renovation indicators
- Estimated maintenance costs

## Location-Based Metrics

### 7. Transportation Accessibility
- Distance to public transport
- Walking distance to metro/bus stops
- Car accessibility and parking availability

### 8. Amenity Density
- Proximity to schools, hospitals, shops
- Green spaces and recreational facilities
- Dining and entertainment options

### 9. Neighborhood Quality Indicators
- Crime statistics (where available)
- Average property values in area
- Infrastructure quality
- Future development plans

## Comparative Analysis Metrics

### 10. Market Positioning
- Price percentile within neighborhood
- Comparison to similar properties
- Time on market trends

### 11. Investment Potential
- Historical price trends in area
- Development projects nearby
- Supply-demand balance

## Scoring System

### Overall Property Score
Weighted formula combining:
- Financial metrics (40%)
- Property quality (25%)
- Location factors (25%)
- Market conditions (10%)

### Custom Weightings
Allow users to adjust weights based on priorities:
- Families: More weight on schools and safety
- Young professionals: More weight on transportation and nightlife
- Retirees: More weight on healthcare access and tranquility

## Benchmarking Against Official Data

### 12. Price Fairness Indicator
- Compare listing price to official market values
- Percentage deviation from Penotariado/Tinsa averages
- Identify potentially overpriced or undervalued properties

### 13. Market Alignment Score
- How well the price aligns with official statistics
- Consistency with recent sales in area
- Comparison to similar properties sold recently

## Dynamic Metrics

### 14. Price Change Tracking
- Historical price movements for the property
- Days on market
- Price reduction frequency

### 15. Competition Level
- Number of similar properties available
- Market saturation in price range
- Urgency indicators

## Calculation Examples

### Value Score Formula
```
Value_Score = (
    (1 - abs(price_per_sqm - neighborhood_avg) / neighborhood_avg) * 0.4 +
    condition_score * 0.2 +
    feature_score * 0.2 +
    location_score * 0.2
) * 100
```

### Affordability Index
```
Affordability_Index = (net_monthly_income / estimated_monthly_payment) * 100
```

## Visualization of Metrics

### Dashboard Elements
- Radar charts for multi-dimensional comparisons
- Heat maps for location scoring
- Trend lines for price evolution
- Scatter plots for price vs. features relationships

These metrics will allow for objective comparison of properties despite differences in presentation across various platforms, helping to identify the best value opportunities in the Zaragoza market.