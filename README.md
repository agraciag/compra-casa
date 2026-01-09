# CasaCompra - Property Purchase Analysis Tool

This project helps analyze the housing market in Zaragoza, Spain by scraping real estate websites and creating a custom comparison tool to identify the best purchase opportunities.

## Project Overview

The system collects housing data from various sources (Idealista, Fotocasa, etc.) and compares it with official data sources (Penotariado, Tinsa, etc.) to help make informed decisions about purchasing a home in Zaragoza.

## Features

- **Ethical Web Scraping**: Slow, respectful scraping to avoid bans with configurable rate limiting
- **Data Deduplication**: Intelligent detection and merging of duplicate listings across sources
- **Comprehensive Database**: SQLite database with normalized property data
- **Price Analysis**: Price per square meter calculations and market comparisons
- **Quality Metrics**: Standardized metrics for comparing properties
- **Duplicate Detection**: Identifies the same property listed on multiple portals

## Project Structure

```
compra-casa/
├── data/
│   ├── raw/          # Raw scraped data
│   └── processed/    # Cleaned and processed data
├── src/
│   ├── scraper/      # Web scraping modules
│   ├── analysis/     # Data analysis modules
│   ├── visualization/ # Data visualization modules
│   └── utils/        # Utility functions
├── docs/             # Documentation
├── config/           # Configuration files
├── logs/             # Log files
├── venv/             # Virtual environment
├── requirements.txt  # Python dependencies
└── README.md
```

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Quick Demo
Run the demo to verify the system is working:
```bash
python demo_system.py
```

### Start Data Collection
Run the main data collection script:
```bash
python src/data_collection.py
```

Follow the prompts to begin collecting property data from various sources.

### Configuration
Adjust scraping parameters in `config/settings.py`:
- Rate limiting settings
- Source-specific configurations
- Geographic filters for Zaragoza
- Property filters and validation thresholds

## Data Model

The system stores comprehensive property information including:
- Basic details (price, size, rooms, etc.)
- Location data (address, coordinates, district)
- Features (elevator, parking, terrace, etc.)
- Historical price tracking
- Source attribution and metadata

## Ethical Scraping

The system implements respectful scraping practices:
- Configurable delays between requests (5-10 seconds minimum)
- Random user agent rotation
- Robots.txt compliance checking
- Session management with cookies
- Error handling and retry mechanisms

## Data Quality

- Validation of price ranges and property characteristics
- Deduplication across sources
- Standardized address and feature extraction
- Quality scoring for property comparisons

## Next Steps

1. Begin collecting data from real sources
2. Implement additional source parsers as needed
3. Set up periodic runs using a scheduler
4. Develop visualization dashboards
5. Create property comparison tools
6. Add market trend analysis features

## Legal Notice

This project respects website terms of service and implements rate limiting to avoid placing undue burden on servers. Always check individual websites' robots.txt and terms of service before scraping.