# Database Schema Design

## Overview
The database will store property listings from various sources with standardized fields for comparison and analysis.

## Tables

### 1. Properties Table
Main table storing property information:

```sql
CREATE TABLE properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT UNIQUE,              -- ID from the source website
    source TEXT NOT NULL,                 -- Source website (idealista, fotocasa, etc.)
    url TEXT,                             -- Original listing URL
    title TEXT,                           -- Property title
    description TEXT,                     -- Property description
    
    -- Location
    address TEXT,
    city TEXT DEFAULT 'Zaragoza',
    district TEXT,                        -- Neighborhood/district
    postal_code TEXT,
    latitude REAL,
    longitude REAL,
    
    -- Property details
    property_type TEXT,                   -- apartment, house, studio, etc.
    price REAL,
    currency TEXT DEFAULT 'EUR',
    surface_area REAL,                    -- Total area in sq meters
    rooms INTEGER,                        -- Number of rooms
    bedrooms INTEGER,
    bathrooms INTEGER,
    floor_number INTEGER,                 -- Floor level
    total_floors INTEGER,                 -- Building height
    construction_year INTEGER,
    
    -- Features
    has_elevator BOOLEAN,
    has_parking BOOLEAN,
    parking_price REAL,
    has_terrace BOOLEAN,
    has_balcony BOOLEAN,
    has_garden BOOLEAN,
    has_pool BOOLEAN,
    energy_certificate_rating TEXT,       -- Energy efficiency rating
    
    -- Status and metadata
    is_active BOOLEAN DEFAULT TRUE,       -- Is the listing still active?
    first_seen_date DATE,
    last_seen_date DATE,
    scraped_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Historical Prices Table
Track price changes over time:

```sql
CREATE TABLE historical_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER,
    price REAL NOT NULL,
    date_recorded DATE NOT NULL,
    FOREIGN KEY (property_id) REFERENCES properties(id)
);
```

### 3. Sources Table
Information about data sources:

```sql
CREATE TABLE sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,            -- idealista, fotocasa, etc.
    base_url TEXT,
    last_scraped DATETIME,
    is_active BOOLEAN DEFAULT TRUE
);
```

### 4. Scraping Logs Table
Track scraping activities:

```sql
CREATE TABLE scraping_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    url TEXT,
    status_code INTEGER,
    response_time REAL,
    error_message TEXT,
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 5. Market Statistics Table
Aggregated market data from official sources:

```sql
CREATE TABLE market_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    district TEXT,
    avg_price_per_sqm REAL,
    median_price_per_sqm REAL,
    transaction_count INTEGER,
    period_start DATE,                    -- Start of reporting period
    period_end DATE,                      -- End of reporting period
    source TEXT,                          -- Official source (penotariado, tinsa, etc.)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Indexes for Performance

```sql
-- Indexes for faster queries
CREATE INDEX idx_properties_city ON properties(city);
CREATE INDEX idx_properties_district ON properties(district);
CREATE INDEX idx_properties_price ON properties(price);
CREATE INDEX idx_properties_surface_area ON properties(surface_area);
CREATE INDEX idx_properties_rooms ON properties(rooms);
CREATE INDEX idx_properties_bedrooms ON properties(bedrooms);
CREATE INDEX idx_properties_property_type ON properties(property_type);
CREATE INDEX idx_properties_coordinates ON properties(latitude, longitude);
CREATE INDEX idx_properties_is_active ON properties(is_active);
CREATE INDEX idx_properties_source ON properties(source);

-- Composite indexes
CREATE INDEX idx_properties_location_price ON properties(city, district, price);
CREATE INDEX idx_properties_type_price ON properties(property_type, price);
```

## Relationships
- Each property belongs to one source
- Multiple historical prices can exist for one property
- Market stats provide benchmark data for comparison

## Data Types Considerations
- Use REAL for prices and measurements to handle decimals
- Use BOOLEAN for yes/no features
- Use TEXT for flexible string fields
- Use INTEGER for counts and IDs
- Use DATETIME for timestamps

## Constraints
- Price should be positive
- Surface area should be positive
- Room counts should be non-negative
- Coordinates should be within valid ranges for Zaragoza