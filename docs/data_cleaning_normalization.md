# Data Cleaning and Normalization Plan

## Overview
Property data from different sources varies significantly in format, completeness, and quality. A systematic approach to cleaning and normalization is essential for meaningful comparisons.

## Data Quality Issues to Address

### Missing Values
- Handle null values in critical fields (price, surface area, rooms)
- Implement imputation strategies for missing data
- Flag records with excessive missing information

### Inconsistent Formats
- Standardize address formats across sources
- Normalize property types (apartment/piso/departamento)
- Convert units to metric system (sq meters, euros)

### Data Validation
- Verify price ranges are reasonable for Zaragoza market
- Validate geographic coordinates are in Zaragoza area
- Check room counts are logical for property sizes

## Cleaning Pipeline

### 1. Initial Data Validation
```python
def validate_raw_data(data):
    """
    Basic validation of scraped data
    """
    # Check for required fields
    required_fields = ['title', 'price', 'surface_area', 'city']
    for field in required_fields:
        if field not in data or data[field] is None:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate price range
    if data['price'] <= 0 or data['price'] > 10000000:  # Arbitrary upper limit
        raise ValueError(f"Invalid price: {data['price']}")
    
    # Validate surface area
    if data['surface_area'] <= 0 or data['surface_area'] > 1000:  # Max 1000 sqm
        raise ValueError(f"Invalid surface area: {data['surface_area']}")
    
    return True
```

### 2. Text Normalization
- Standardize property type descriptions
- Clean and normalize titles and descriptions
- Extract numeric values from text fields
- Handle special characters and encoding issues

### 3. Address Standardization
- Parse addresses into components (street, number, door, etc.)
- Standardize street names and abbreviations
- Match districts to official boundaries
- Geocode addresses to coordinates if missing

### 4. Numeric Field Normalization
- Convert prices to consistent currency (EUR)
- Standardize area measurements to square meters
- Normalize room counts to integers
- Calculate derived metrics (price per sqm)

### 5. Feature Extraction
- Parse amenities from description text
- Extract boolean features (has_elevator, has_parking, etc.)
- Identify property condition indicators
- Extract energy efficiency ratings

## Specific Cleaning Functions

### Price Normalization
```python
def normalize_price(price_str, currency=None):
    """
    Convert price string to standardized format
    """
    import re
    
    # Remove non-numeric characters except decimal point
    clean_price = re.sub(r'[^\d,.]', '', str(price_str))
    
    # Handle different decimal separators
    if ',' in clean_price and '.' in clean_price:
        # If both commas and periods exist, assume comma is thousands separator
        clean_price = clean_price.replace(',', '')
    elif ',' in clean_price:
        # If only comma exists, check if it's a decimal separator
        parts = clean_price.split(',')
        if len(parts) == 2 and len(parts[1]) == 2:  # Likely decimal
            clean_price = clean_price.replace(',', '.')
    
    try:
        return float(clean_price)
    except ValueError:
        return None
```

### Area Normalization
```python
def normalize_area(area_str):
    """
    Convert area string to square meters
    """
    import re
    
    # Extract numeric value
    numbers = re.findall(r'\d+(?:[.,]\d+)?', str(area_str))
    if not numbers:
        return None
    
    area_val = float(numbers[0].replace(',', '.'))
    
    # Check for unit indicators
    area_str_lower = area_str.lower()
    if 'm²' in area_str_lower or 'sqm' in area_str_lower or 'metros' in area_str_lower:
        return area_val  # Already in square meters
    elif 'ha' in area_str_lower or 'hectarea' in area_str_lower:
        return area_val * 10000  # hectares to square meters
    else:
        # Assume square meters if no unit specified
        return area_val
```

### Property Type Normalization
```python
PROPERTY_TYPE_MAPPING = {
    'piso': 'apartment',
    'apartamento': 'apartment',
    'ático': 'penthouse',
    'duplex': 'duplex',
    'casa': 'house',
    'chalet': 'house',
    'ático': 'penthouse',
    'estudio': 'studio',
    'loft': 'loft',
    'bungalow': 'bungalow'
}

def normalize_property_type(type_str):
    """
    Standardize property type descriptions
    """
    if not type_str:
        return None
        
    type_clean = type_str.lower().strip()
    return PROPERTY_TYPE_MAPPING.get(type_clean, type_clean)
```

## Data Quality Metrics

### Completeness Score
Calculate a score based on how many critical fields are filled:
- Price: 25 points
- Surface area: 20 points
- Rooms: 15 points
- Location: 20 points
- Description: 10 points
- Images: 10 points

### Consistency Checks
- Verify price per sqm is within reasonable bounds
- Check if room count is proportional to surface area
- Validate geographic coordinates match stated location

## Deduplication Strategy
- Identify duplicate listings across sources
- Use combination of address, price, and surface area
- Track which source has the most complete information
- Merge information from multiple sources for same property

## Error Handling and Logging
- Log all cleaning operations
- Track rejected records with reasons
- Monitor data quality metrics over time
- Alert on significant changes in data patterns

## Automated Validation
- Set up validation rules for each field
- Create alerts for outliers or unusual patterns
- Regular reporting on data quality metrics
- Monitor source reliability over time