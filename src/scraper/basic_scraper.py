import re
import requests
import time
import random
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
import logging
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.models import PropertyModel
from src.utils.database import PropertyDatabase
from src.utils.deduplication import PropertyDeduplicator
from config.settings import (
    SCRAPING_CONFIG, LOGGING_CONFIG, SOURCE_CONFIGS,
    SEARCH_SCOPE, FILTERED_SEARCH_URLS,
)


class PropertyScraper:
    """
    Basic property scraper with rate limiting to avoid bans
    """
    
    def __init__(self, db: PropertyDatabase):
        self.db = db
        self.session = requests.Session()
        self.deduplicator = PropertyDeduplicator(db)
        
        # Set up logging
        self.setup_logging()
        
        # Initialize rate limiting parameters
        self.min_delay = SCRAPING_CONFIG['min_delay_between_requests']
        self.max_delay = SCRAPING_CONFIG['max_delay_between_requests']
        self.headers = SCRAPING_CONFIG['headers'].copy()
        
        # Set initial user agent
        self.set_random_user_agent()
        
        # Track last request time for rate limiting
        self.last_request_time = 0
        
        # Track source-specific configs
        self.source_configs = SOURCE_CONFIGS
    
    def setup_logging(self):
        """Set up logging for the scraper"""
        log_dir = LOGGING_CONFIG.get('log_dir', 'logs/')
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            level=getattr(logging, LOGGING_CONFIG.get('level', 'INFO')),
            format=LOGGING_CONFIG.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            handlers=[
                logging.FileHandler(f"{log_dir}scraper.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def set_random_user_agent(self):
        """Set a random user agent from the configured list"""
        user_agent = random.choice(SCRAPING_CONFIG['user_agents'])
        self.headers['User-Agent'] = user_agent
        self.session.headers.update(self.headers)
    
    def respect_rate_limit(self, source: str = None):
        """Implement rate limiting with random delays"""
        # Determine delay based on source if specified
        if source and source in self.source_configs:
            min_delay, max_delay = self.source_configs[source]['request_delay']
        else:
            min_delay, max_delay = self.min_delay, self.max_delay
        
        # Calculate time since last request
        time_since_last = time.time() - self.last_request_time
        
        # Calculate required delay
        delay = random.uniform(min_delay, max_delay)
        
        # If we haven't waited enough time yet, sleep
        if time_since_last < delay:
            actual_sleep = delay - time_since_last
            self.logger.debug(f"Rate limiting: sleeping for {actual_sleep:.2f} seconds")
            time.sleep(actual_sleep)
        
        self.last_request_time = time.time()
    
    def check_robots_txt(self, url: str, user_agent: str = '*') -> bool:
        """Check if scraping is allowed by robots.txt"""
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            return rp.can_fetch(user_agent, url)
        except Exception as e:
            self.logger.warning(f"Could not check robots.txt for {url}: {e}")
            # If we can't check, assume it's OK to proceed cautiously
            return True
    
    def make_request(self, url: str, source: str = None, **kwargs) -> Optional[requests.Response]:
        """Make an HTTP request with rate limiting and error handling"""
        # Respect rate limiting
        self.respect_rate_limit(source)
        
        # Update headers with random user agent periodically
        if random.random() < 0.3:  # 30% chance to rotate user agent
            self.set_random_user_agent()
        
        # Add any additional headers from kwargs
        headers = kwargs.pop('headers', {})
        all_headers = {**self.session.headers, **headers}
        
        try:
            start_time = time.time()
            response = self.session.get(
                url, 
                timeout=SCRAPING_CONFIG['timeout'],
                headers=all_headers,
                **kwargs
            )
            end_time = time.time()
            
            # Log the request
            self.log_request(url, source, response.status_code, end_time - start_time)
            
            if response.status_code == 200:
                return response
            else:
                self.logger.warning(f"Request to {url} returned status {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {str(e)}")
            self.log_error(url, source, str(e))
            return None
    
    def log_request(self, url: str, source: str, status_code: int, response_time: float):
        """Log successful requests"""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO scraping_logs (source, url, status_code, response_time, scraped_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (source or 'unknown', url, status_code, response_time, datetime.now().isoformat()))
        self.db.conn.commit()
    
    def log_error(self, url: str, source: str, error_message: str):
        """Log request errors"""
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO scraping_logs (source, url, error_message, scraped_at)
            VALUES (?, ?, ?, ?)
        ''', (source or 'unknown', url, error_message, datetime.now().isoformat()))
        self.db.conn.commit()
    
    def parse_idealista_property(self, soup: BeautifulSoup, url: str) -> Optional[PropertyModel]:
        """Parse property data from Idealista"""
        try:
            # Extract basic information
            title_elem = soup.find('h1', class_='main-info__title-main')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            # Extract price
            price_elem = soup.find('span', class_='price')
            price_text = price_elem.get_text(strip=True) if price_elem else None
            price = self.extract_price(price_text) if price_text else None
            
            # Extract features
            features_container = soup.find('div', class_='details-property_features')
            features = []
            if features_elem := soup.find_all('li', class_='features__item'):
                for feat in features_elem:
                    features.append(feat.get_text(strip=True).lower())
            
            # Extract description
            desc_elem = soup.find('div', class_='details-property_description')
            description = desc_elem.get_text(strip=True) if desc_elem else None
            
            # Extract address
            address_elem = soup.find('span', class_='main-info__title-minor')
            address = address_elem.get_text(strip=True) if address_elem else None
            
            # Extract surface area
            surface_area = None
            for feat in features:
                if 'm²' in feat or 'metros' in feat:
                    surface_area = self.extract_surface_area(feat)
                    break
            
            # Extract rooms
            rooms = None
            for feat in features:
                if 'dormitorio' in feat or 'habitación' in feat or 'room' in feat:
                    rooms = self.extract_number(feat)
                    break
            
            # Extract bedrooms specifically
            bedrooms = None
            for feat in features:
                if 'dormitorio' in feat or 'bedroom' in feat:
                    bedrooms = self.extract_number(feat)
                    break
            
            # Extract bathrooms
            bathrooms = None
            for feat in features:
                if 'baño' in feat or 'bathroom' in feat or 'wc' in feat:
                    bathrooms = self.extract_number(feat)
                    break
            
            # Extract floor number
            floor_number = None
            for feat in features:
                if 'planta' in feat or 'floor' in feat:
                    floor_number = self.extract_floor_number(feat)
                    break
            
            # Detect property condition
            all_text = ' '.join([title or '', description or '', ' '.join(features)])
            property_condition = self.detect_property_condition(all_text, url)

            # Create property model
            property_data = {
                'external_id': self.extract_external_id(url, 'idealista'),
                'source': 'idealista',
                'url': url,
                'title': title,
                'description': description,
                'address': address,
                'price': price,
                'surface_area': surface_area,
                'rooms': rooms,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'floor_number': floor_number,
                'has_elevator': 'ascensor' in ' '.join(features).lower() if features else False,
                'has_parking': 'garaje' in ' '.join(features).lower() if features else False,
                'has_terrace': 'terraza' in ' '.join(features).lower() if features else False,
                'has_balcony': 'balcón' in ' '.join(features).lower() if features else False,
                'has_garden': 'jardín' in ' '.join(features).lower() if features else False,
                'property_condition': property_condition,
            }

            return PropertyModel(**property_data)

        except Exception as e:
            self.logger.error(f"Error parsing Idealista property {url}: {str(e)}")
            return None
    
    def parse_fotocasa_property(self, soup: BeautifulSoup, url: str) -> Optional[PropertyModel]:
        """Parse property data from Fotocasa (re-Detail* classes)."""
        try:
            # Title
            title_elem = soup.find('h1', class_=lambda c: c and 'DetailHeader-propertyTitle' in c)
            if not title_elem:
                title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else None

            # Price: span.re-DetailHeader-price -> "235.000 €"
            price = None
            price_elem = soup.find('span', class_=lambda c: c and 'DetailHeader-price' in c)
            if price_elem:
                price = self.extract_price(price_elem.get_text(strip=True))

            # Header features: rooms, bathrooms, surface, floor
            bedrooms = None
            bathrooms = None
            surface_area = None
            floor_number = None

            rooms_elem = soup.find('li', class_=lambda c: c and 'DetailHeader-rooms' in c)
            if rooms_elem:
                bedrooms = self.extract_number(rooms_elem.get_text(strip=True))

            bath_elem = soup.find('li', class_=lambda c: c and 'DetailHeader-bathrooms' in c)
            if bath_elem:
                bathrooms = self.extract_number(bath_elem.get_text(strip=True))

            surface_elem = soup.find('li', class_=lambda c: c and 'DetailHeader-surface' in c)
            if surface_elem:
                surface_area = self.extract_surface_area(surface_elem.get_text(strip=True))

            floor_elem = soup.find('li', class_=lambda c: c and 'floor' in c.lower())
            if floor_elem:
                floor_number = self.extract_floor_number(floor_elem.get_text(strip=True))

            # Address from title (format: "Piso en venta en STREET, DISTRICT")
            address = None
            district = None
            if title and ' en ' in title:
                # Extract everything after last "en "
                parts = title.split(' en ')
                if len(parts) >= 2:
                    location = parts[-1]
                    if ',' in location:
                        addr_part, district = location.rsplit(',', 1)
                        address = addr_part.strip()
                        district = district.strip()
                    else:
                        address = location.strip()

            # Municipality
            muni_elem = soup.find('p', class_=lambda c: c and 'municipalityTitle' in c)

            # Description
            desc_elem = soup.find('p', class_=lambda c: c and 'DetailDescription' in c)
            description = desc_elem.get_text(strip=True) if desc_elem else None

            # Energy certificate: look for re-DetailEnergyCertificate-value--X
            energy_rating = None
            cert_elem = soup.find(class_=lambda c: c and 'DetailEnergyCertificate-value--' in c)
            if cert_elem:
                for cls in cert_elem.get('class', []):
                    if 'value--' in cls:
                        energy_rating = cls.split('value--')[-1].upper()
                        break

            # Extras: li.re-DetailExtras-listItem
            extras = []
            for item in soup.find_all('li', class_=lambda c: c and 'DetailExtras-listItem' in c):
                extras.append(item.get_text(strip=True).lower())

            extras_text = ' '.join(extras)
            has_parking = 'parking' in url.lower() or 'garaje' in extras_text or 'parking' in extras_text
            has_terrace = 'terraza' in extras_text
            has_balcony = 'balcón' in extras_text or 'balcon' in extras_text
            has_garden = 'jardín' in extras_text or 'jardin' in extras_text
            has_pool = 'piscina' in extras_text
            has_elevator = 'ascensor' in extras_text or 'ascensor' in url.lower()

            # Detect condition
            all_text = ' '.join([title or '', description or '', extras_text])
            property_condition = self.detect_property_condition(all_text, url)

            property_data = {
                'external_id': self.extract_external_id(url, 'fotocasa'),
                'source': 'fotocasa',
                'url': url,
                'title': title,
                'description': description,
                'address': address,
                'district': district,
                'price': price,
                'surface_area': surface_area,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'floor_number': floor_number,
                'has_elevator': has_elevator,
                'has_parking': has_parking,
                'has_terrace': has_terrace,
                'has_balcony': has_balcony,
                'has_garden': has_garden,
                'has_pool': has_pool,
                'energy_certificate_rating': energy_rating,
                'property_condition': property_condition,
            }

            return PropertyModel(**property_data)

        except Exception as e:
            self.logger.error(f"Error parsing Fotocasa property {url}: {str(e)}")
            return None
    
    def parse_habitaclia_property(self, soup: BeautifulSoup, url: str) -> Optional[PropertyModel]:
        """Parse property data from Habitaclia"""
        try:
            # Extract title
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            # Extract price
            price_elem = soup.find('span', class_='price')
            if not price_elem:
                price_elem = soup.find(class_='precio')
            price_text = price_elem.get_text(strip=True) if price_elem else None
            price = self.extract_price(price_text) if price_text else None
            
            # Extract features
            features = []
            features_containers = soup.find_all(['ul', 'div'], 
                                              class_=lambda x: x and ('features' in x or 'caracteristicas' in x or 'details' in x))
            
            for container in features_containers:
                feature_items = container.find_all(['li', 'div', 'span'])
                for item in feature_items:
                    text = item.get_text(strip=True).lower()
                    if text:
                        features.append(text)
            
            # Extract description
            desc_elem = soup.find('div', class_='description')
            if not desc_elem:
                desc_elem = soup.find('div', class_='descripcion')
            description = desc_elem.get_text(strip=True) if desc_elem else None
            
            # Extract address
            address_elem = soup.find('span', class_='address')
            if not address_elem:
                address_elem = soup.find('div', class_='direccion')
            address = address_elem.get_text(strip=True) if address_elem else None
            
            # Extract surface area
            surface_area = None
            for feat in features:
                if 'm²' in feat or 'metros' in feat:
                    surface_area = self.extract_surface_area(feat)
                    break
            
            # Extract rooms
            rooms = None
            bedrooms = None
            for feat in features:
                if 'dormitorio' in feat or 'habitación' in feat or 'room' in feat:
                    rooms = self.extract_number(feat)
                    if 'dormitorio' in feat:
                        bedrooms = self.extract_number(feat)
                    break
            
            # Extract bathrooms
            bathrooms = None
            for feat in features:
                if 'baño' in feat or 'bathroom' in feat or 'wc' in feat:
                    bathrooms = self.extract_number(feat)
                    break
            
            # Detect property condition
            all_text = ' '.join([title or '', description or '', ' '.join(features)])
            property_condition = self.detect_property_condition(all_text, url)

            # Create property model
            property_data = {
                'external_id': self.extract_external_id(url, 'habitaclia'),
                'source': 'habitaclia',
                'url': url,
                'title': title,
                'description': description,
                'address': address,
                'price': price,
                'surface_area': surface_area,
                'rooms': rooms,
                'bedrooms': bedrooms,
                'bathrooms': bathrooms,
                'has_parking': 'garaje' in ' '.join(features).lower() if features else False,
                'has_terrace': 'terraza' in ' '.join(features).lower() if features else False,
                'has_balcony': 'balcón' in ' '.join(features).lower() if features else False,
                'has_garden': 'jardín' in ' '.join(features).lower() if features else False,
                'property_condition': property_condition,
            }

            return PropertyModel(**property_data)

        except Exception as e:
            self.logger.error(f"Error parsing Habitaclia property {url}: {str(e)}")
            return None
    
    def detect_property_condition(self, text: str, url: str) -> Optional[str]:
        """Detect property condition from text content and URL."""
        combined = (text or '').lower() + ' ' + (url or '').lower()
        construction_keywords = ['en construcción', 'en construccion', 'sobre plano', 'entrega prevista', 'prevista entrega']
        new_keywords = ['obra nueva', 'nueva construcción', 'nueva construccion', 'a estrenar', 'promoción nueva', 'promocion nueva']
        if any(kw in combined for kw in construction_keywords):
            return 'en_construccion'
        if any(kw in combined for kw in new_keywords):
            return 'obra_nueva'
        if 'segunda mano' in combined or 'second hand' in combined:
            return 'segunda_mano'
        return None

    def extract_price(self, price_text: str) -> Optional[float]:
        """Extract price from text. Handles Spanish format (235.000 €) and others."""
        if not price_text:
            return None

        # Remove currency symbols, spaces, and non-numeric chars except . and ,
        price_str = re.sub(r'[^\d,.]', '', price_text)

        if ',' in price_str and '.' in price_str:
            # Both separators: determine which is thousands vs decimal
            if price_str.index('.') < price_str.index(','):
                # Format: 1.234,56 (Spanish decimal comma)
                price_str = price_str.replace('.', '').replace(',', '.')
            else:
                # Format: 1,234.56 (English)
                price_str = price_str.replace(',', '')
        elif '.' in price_str:
            # Only dots: check if it's a thousands separator (e.g. "235.000")
            parts = price_str.split('.')
            if len(parts) == 2 and len(parts[1]) == 3:
                # Thousands separator (235.000 = 235000)
                price_str = price_str.replace('.', '')
            elif len(parts) > 2:
                # Multiple dots = thousands (1.234.567)
                price_str = price_str.replace('.', '')
            # else: single dot with != 3 decimals, treat as decimal point
        elif ',' in price_str:
            parts = price_str.split(',')
            if len(parts) == 2 and len(parts[1]) == 2:
                # Decimal comma (1234,56)
                price_str = price_str.replace(',', '.')
            else:
                # Thousands comma
                price_str = price_str.replace(',', '')

        try:
            return float(price_str)
        except ValueError:
            return None
    
    def extract_surface_area(self, feature_text: str) -> Optional[float]:
        """Extract surface area from feature text"""
        # Look for patterns like "85 m²", "120 metros", etc.
        patterns = [
            r'(\d+(?:[.,]\d+)?)\s*m²',
            r'(\d+(?:[.,]\d+)?)\s*metros',
            r'(\d+(?:[.,]\d+)?)\s*m$',
            r'^(\d+(?:[.,]\d+)?)\s*m'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, feature_text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(',', '.'))
                except ValueError:
                    continue
        return None
    
    def extract_number(self, feature_text: str) -> Optional[int]:
        """Extract a number from feature text"""
        # Look for numbers in the text
        numbers = re.findall(r'\d+', feature_text)
        if numbers:
            try:
                return int(numbers[0])
            except ValueError:
                return None
        return None
    
    def extract_floor_number(self, feature_text: str) -> Optional[int]:
        """Extract floor number from feature text"""
        # Look for floor numbers in various formats
        patterns = [
            r'(\d+)\s*(?:ª|a|st|nd|rd|th|piso|floor)',
            r'(?:planta|floor|piso)\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, feature_text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return None
    
    def extract_external_id(self, url: str, source: str) -> str:
        """Extract external ID from URL"""
        # Different patterns for different sources
        patterns = {
            'idealista': r'/(\d+)/',
            'fotocasa': r'/(\d+)/',
            'habitaclia': r'/(\d+)/',
            'pisoscom': r'/(\d+)/'
        }
        
        pattern = patterns.get(source, r'/(\d+)/')
        match = re.search(pattern, url)
        return match.group(1) if match else url.__hash__().__str__()
    
    def scrape_property(self, url: str, source: str) -> Optional[PropertyModel]:
        """Scrape a single property listing"""
        self.logger.info(f"Scraping property: {url} from {source}")
        
        # Make request
        response = self.make_request(url, source)
        if not response:
            return None
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Parse based on source
        parser_map = {
            'idealista': self.parse_idealista_property,
            'fotocasa': self.parse_fotocasa_property,
            'habitaclia': self.parse_habitaclia_property,
        }
        
        parser = parser_map.get(source)
        if not parser:
            self.logger.error(f"No parser available for source: {source}")
            return None
        
        property_model = parser(soup, url)
        if not property_model:
            self.logger.error(f"Failed to parse property from {url}")
            return None
        
        # Validate the property data
        from src.utils.models import validate_property_data
        if not validate_property_data(property_model.to_dict()):
            self.logger.error(f"Property data validation failed for {url}")
            return None
        
        return property_model
    
    def meets_scope(self, property_model: PropertyModel) -> bool:
        """Check if a property meets the active search scope criteria."""
        scope = SEARCH_SCOPE
        if property_model.price:
            if property_model.price < scope.get('min_price', 0):
                self.logger.debug(f"Skipped: price {property_model.price} below min {scope['min_price']}")
                return False
            if property_model.price > scope.get('max_price', float('inf')):
                self.logger.debug(f"Skipped: price {property_model.price} above max {scope['max_price']}")
                return False
        if scope.get('min_bedrooms') and property_model.bedrooms is not None:
            if property_model.bedrooms < scope['min_bedrooms']:
                self.logger.debug(f"Skipped: {property_model.bedrooms} bedrooms < {scope['min_bedrooms']}")
                return False
        if scope.get('min_bathrooms') and property_model.bathrooms is not None:
            if property_model.bathrooms < scope['min_bathrooms']:
                self.logger.debug(f"Skipped: {property_model.bathrooms} bathrooms < {scope['min_bathrooms']}")
                return False
        if scope.get('has_parking') and property_model.has_parking is not None:
            if not property_model.has_parking:
                self.logger.debug("Skipped: no parking")
                return False
        return True

    def save_property(self, property_model: PropertyModel):
        """Save property to database with scope validation and duplicate checking."""
        # Post-scrape scope validation
        if not self.meets_scope(property_model):
            self.logger.info(f"Out of scope, skipped: {property_model.title or property_model.url}")
            return None

        # Check for duplicates
        potential_duplicates = self.deduplicator.find_potential_duplicates(property_model)

        if potential_duplicates:
            is_duplicate, existing_id = self.deduplicator.handle_duplicate_property(
                property_model, potential_duplicates
            )
            if is_duplicate:
                self.logger.info(f"Updated existing property {existing_id} from {property_model.source}")
                return existing_id

        # New property
        property_dict = property_model.to_dict()
        property_id = self.db.insert_property(property_dict)
        self.logger.info(f"Saved new property {property_id} from {property_model.source}")
        return property_id

    def build_page_url(self, source: str, page_num: int) -> Optional[str]:
        """Build a paginated search URL using the pre-filtered base URL."""
        base_url = FILTERED_SEARCH_URLS.get(source)
        if not base_url:
            self.logger.error(f"No filtered URL configured for source: {source}")
            return None

        if source == 'idealista':
            # Idealista: insert pagina-N before trailing slash
            if page_num == 1:
                return base_url
            return base_url.rstrip('/') + f'/pagina-{page_num}.htm'
        elif source == 'fotocasa':
            # Fotocasa: append &combinedLocationIds and page param
            sep = '&' if '?' in base_url else '?'
            if page_num == 1:
                return base_url
            return f"{base_url}{sep}currentPage={page_num}"
        else:
            # Generic fallback
            sep = '&' if '?' in base_url else '?'
            return f"{base_url}{sep}page={page_num}"

    def _extract_property_urls(self, soup: BeautifulSoup, source: str, base_url: str) -> List[str]:
        """Extract unique property detail URLs from a listing page."""
        seen = set()
        urls = []

        for a in soup.find_all('a', href=True):
            href = a['href']
            if source == 'fotocasa':
                # Fotocasa detail URLs match: /es/comprar/vivienda/.../DIGITS/d
                if not re.search(r'/vivienda/.+/\d+/d', href):
                    continue
            elif source == 'idealista':
                # Idealista detail URLs match: /inmueble/DIGITS/
                if '/inmueble/' not in href:
                    continue
            else:
                if '/inmueble/' not in href and '/venta/' not in href:
                    continue

            # Normalize: strip query params for dedup
            clean = href.split('?')[0].rstrip('/')
            if clean in seen:
                continue
            seen.add(clean)
            urls.append(urljoin(base_url, clean))

        return urls

    def scrape_zaragoza_listings(self, source: str, max_pages: int = None):
        """Scrape property listings from a source for Zaragoza using pre-filtered URLs."""
        if max_pages is None:
            max_pages = SEARCH_SCOPE.get('max_pages', 2)

        self.logger.info(f"Starting filtered scrape: {max_pages} pages from {source}")

        for page_num in range(1, max_pages + 1):
            page_url = self.build_page_url(source, page_num)
            if not page_url:
                break

            self.logger.info(f"[{source}] Page {page_num}: {page_url}")

            # Pagination delay
            if page_num > 1:
                min_d, max_d = self.source_configs.get(source, {}).get('pagination_delay', (10, 15))
                delay = random.uniform(min_d, max_d)
                self.logger.debug(f"Pagination delay: {delay:.1f}s")
                time.sleep(delay)

            response = self.make_request(page_url, source)
            if not response:
                self.logger.warning(f"Failed to get page {page_num} from {source}")
                continue

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract property URLs (deduplicated by stripping query params)
            unique_urls = self._extract_property_urls(soup, source, response.url)

            if not unique_urls:
                self.logger.warning(f"No property links found on page {page_num} from {source}")
                continue

            self.logger.info(f"Found {len(unique_urls)} unique property links on page {page_num}")

            for property_url in unique_urls[:15]:

                property_model = self.scrape_property(property_url, source)
                if property_model:
                    self.save_property(property_model)

                time.sleep(random.uniform(2, 5))
    
    def close(self):
        """Close the scraper and clean up resources"""
        self.session.close()


# Example usage
if __name__ == "__main__":
    # Initialize database
    db = PropertyDatabase()
    
    # Initialize scraper
    scraper = PropertyScraper(db)
    
    # Example: Scrape a few pages from Idealista
    # scraper.scrape_zaragoza_listings('idealista', max_pages=2)
    
    # Close resources
    scraper.close()
    db.close()
    
    print("Scraper initialized successfully!")