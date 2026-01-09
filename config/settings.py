# Configuration for Property Scraper
import os
from datetime import timedelta

# Database configuration
DATABASE_PATH = "data/properties.db"

# Scraping configuration - Very conservative settings to avoid bans
SCRAPING_CONFIG = {
    # Rate limiting - very slow to be respectful
    'min_delay_between_requests': 5.0,      # Minimum seconds between requests
    'max_delay_between_requests': 10.0,     # Maximum seconds between requests
    'random_delay_factor': 0.5,             # Additional random delay factor
    
    # Retry configuration
    'max_retries': 3,                       # Number of retries for failed requests
    'retry_delay': 5.0,                     # Delay between retries in seconds
    
    # Request configuration
    'timeout': 30,                          # Request timeout in seconds
    'user_agents': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ],
    
    # Headers to appear more like a real user
    'headers': {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    },
    
    # Session management
    'session_persistence': True,            # Whether to maintain sessions
    'cookie_jar_enabled': True,             # Whether to store and reuse cookies
    
    # Error handling
    'error_log_file': 'logs/scraping_errors.log',
    'success_log_file': 'logs/scraping_success.log',
}

# Source-specific configurations
SOURCE_CONFIGS = {
    'idealista': {
        'base_url': 'https://www.idealista.com',
        'request_delay': (7, 12),           # Min, max delay in seconds
        'pagination_delay': (10, 15),       # Delay between pagination requests
        'max_pages_per_session': 10,        # Max pages to scrape per session
        'respect_robots_txt': True,
    },
    'fotocasa': {
        'base_url': 'https://www.fotocasa.es',
        'request_delay': (8, 15),
        'pagination_delay': (12, 20),
        'max_pages_per_session': 8,
        'respect_robots_txt': True,
    },
    'habitaclia': {
        'base_url': 'https://www.habitaclia.com',
        'request_delay': (6, 12),
        'pagination_delay': (10, 18),
        'max_pages_per_session': 12,
        'respect_robots_txt': True,
    },
    'pisoscom': {
        'base_url': 'https://www.pisos.com',
        'request_delay': (9, 16),
        'pagination_delay': (15, 25),
        'max_pages_per_session': 7,
        'respect_robots_txt': True,
    }
}

# Geographic focus for Zaragoza
LOCATION_FILTERS = {
    'city': 'Zaragoza',
    'province': 'Zaragoza',
    'region': 'Aragon',
    'allowed_districts': [  # Specific neighborhoods in Zaragoza
        'Casco Histórico', 'Almozara', 'Oliver', 'Parque Venecia', 
        'San José', 'Delicias', 'Miralbueno', 'La Jota', 'Santa Isabel',
        'San Pablo', 'San Gregorio', 'Las Fuentes', 'Montecanal',
        'Valdespartera', 'Cuarte', 'Aljafería', 'Portillo', 'Torresolinas'
    ]
}

# Property filters
PROPERTY_FILTERS = {
    'min_price': 30000,                     # Minimum property price
    'max_price': 500000,                    # Maximum property price
    'min_surface_area': 30,                 # Minimum surface area in sqm
    'max_surface_area': 300,                # Maximum surface area in sqm
    'property_types': ['apartment', 'flat', 'piso', 'house', 'chalet', 'ático', 'duplex'],
}

# Data validation thresholds
DATA_VALIDATION = {
    'min_price_per_sqm': 1000,              # Minimum price per sqm for validation
    'max_price_per_sqm': 8000,              # Maximum price per sqm for validation
    'max_rooms_for_sqm_ratio': 0.15,        # Max rooms per sqm (e.g., 3 rooms / 60 sqm = 0.05)
    'coordinates_tolerance_km': 50,          # Tolerance for location validation in km
}

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'datefmt': '%Y-%m-%d %H:%M:%S',
    'log_dir': 'logs/',
}

# Deduplication settings
DEDUPLICATION_CONFIG = {
    'similarity_threshold': 0.85,           # Threshold for considering properties as duplicates
    'match_fields': ['address', 'price', 'surface_area', 'bedrooms'],  # Fields to match on
    'external_id_priority': True,            # Prefer matching by external ID when available
}

# Schedule configuration (for periodic runs)
SCHEDULE_CONFIG = {
    'daily_run_time': '02:00',              # Time to run daily scraping (2 AM)
    'pages_per_day_per_source': 20,         # Max pages to scrape per day per source
    'weekly_sources_rotation': True,         # Rotate sources weekly to be extra respectful
}