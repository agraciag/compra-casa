from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

@dataclass
class PropertyModel:
    """
    Data class representing a property listing with all relevant information
    """
    # Identifiers
    external_id: str  # ID from the source website
    source: str       # Source website (idealista, fotocasa, etc.)
    url: Optional[str] = None
    
    # Basic Information
    title: Optional[str] = None
    description: Optional[str] = None
    
    # Location
    address: Optional[str] = None
    city: str = "Zaragoza"
    district: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Property Details
    property_type: Optional[str] = None
    price: Optional[float] = None
    currency: str = "EUR"
    surface_area: Optional[float] = None
    rooms: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    floor_number: Optional[int] = None
    total_floors: Optional[int] = None
    construction_year: Optional[int] = None
    
    # Features
    has_elevator: Optional[bool] = None
    has_parking: Optional[bool] = None
    parking_price: Optional[float] = None
    has_terrace: Optional[bool] = None
    has_balcony: Optional[bool] = None
    has_garden: Optional[bool] = None
    has_pool: Optional[bool] = None
    energy_certificate_rating: Optional[str] = None
    
    # Status and Metadata
    is_active: bool = True
    first_seen_date: Optional[str] = None
    last_seen_date: Optional[str] = None
    scraped_at: Optional[str] = None
    
    def __post_init__(self):
        """Validate and normalize data after initialization"""
        # Set timestamps if not provided
        if self.first_seen_date is None:
            self.first_seen_date = datetime.now().strftime('%Y-%m-%d')
        if self.last_seen_date is None:
            self.last_seen_date = datetime.now().strftime('%Y-%m-%d')
        if self.scraped_at is None:
            self.scraped_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass to a dictionary for database insertion"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PropertyModel':
        """Create a PropertyModel instance from a dictionary"""
        # Handle boolean conversion for SQLite compatibility
        boolean_fields = [
            'has_elevator', 'has_parking', 'has_terrace',
            'has_balcony', 'has_garden', 'has_pool', 'is_active'
        ]

        # Create a copy of the data to avoid modifying the original
        filtered_data = data.copy()

        # Remove database-specific fields that aren't part of the model
        db_fields_to_remove = ['id', 'created_at', 'updated_at']
        for field in db_fields_to_remove:
            filtered_data.pop(field, None)

        for field in boolean_fields:
            if field in filtered_data and filtered_data[field] is not None:
                if isinstance(filtered_data[field], int):
                    filtered_data[field] = bool(filtered_data[field])
                elif isinstance(filtered_data[field], str):
                    filtered_data[field] = filtered_data[field].lower() in ('true', '1', 'yes', 'on')

        return cls(**filtered_data)
    
    def calculate_price_per_sqm(self) -> Optional[float]:
        """Calculate price per square meter"""
        if self.price and self.surface_area and self.surface_area > 0:
            return round(self.price / self.surface_area, 2)
        return None
    
    def get_features_list(self) -> List[str]:
        """Get a list of all available features"""
        features = []
        if self.has_elevator: features.append('elevator')
        if self.has_parking: features.append('parking')
        if self.has_terrace: features.append('terrace')
        if self.has_balcony: features.append('balcony')
        if self.has_garden: features.append('garden')
        if self.has_pool: features.append('pool')
        return features
    
    def similarity_score(self, other: 'PropertyModel') -> float:
        """Calculate similarity score with another property (0-1)"""
        score = 0
        total_factors = 0
        
        # Address similarity (if both have addresses)
        if self.address and other.address:
            # Simple similarity based on common words
            self_words = set(self.address.lower().split())
            other_words = set(other.address.lower().split())
            if self_words and other_words:
                common_words = self_words.intersection(other_words)
                address_similarity = len(common_words) / max(len(self_words), len(other_words))
                score += address_similarity * 0.4  # 40% weight to address
                total_factors += 0.4
        
        # Price similarity (if both have prices)
        if self.price and other.price:
            price_diff = abs(self.price - other.price) / max(self.price, other.price)
            price_similarity = 1 - min(price_diff, 1.0)
            score += price_similarity * 0.2  # 20% weight to price
            total_factors += 0.2
        
        # Surface area similarity (if both have surface area)
        if self.surface_area and other.surface_area:
            area_diff = abs(self.surface_area - other.surface_area) / max(self.surface_area, other.surface_area)
            area_similarity = 1 - min(area_diff, 1.0)
            score += area_similarity * 0.2  # 20% weight to area
            total_factors += 0.2
        
        # Bedrooms similarity
        if self.bedrooms is not None and other.bedrooms is not None:
            if self.bedrooms == other.bedrooms:
                score += 0.1  # 10% weight to bedrooms match
                total_factors += 0.1
            else:
                # Partial credit for close bedroom counts
                bed_diff = abs(self.bedrooms - other.bedrooms)
                if bed_diff == 1:  # Off by 1 bedroom
                    score += 0.05
                    total_factors += 0.1
        
        # District similarity (if both have districts)
        if self.district and other.district:
            if self.district.lower() == other.district.lower():
                score += 0.1  # 10% weight to district
                total_factors += 0.1
        
        # Return normalized score
        return score / total_factors if total_factors > 0 else 0.0


@dataclass
class ScrapingLogModel:
    """Data class for scraping logs"""
    source: str
    url: str
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    scraped_at: Optional[str] = None
    
    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now().isoformat()


@dataclass
class MarketStatsModel:
    """Data class for market statistics"""
    district: str
    avg_price_per_sqm: Optional[float] = None
    median_price_per_sqm: Optional[float] = None
    transaction_count: Optional[int] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class SourceModel:
    """Data class for data sources"""
    name: str
    base_url: Optional[str] = None
    last_scraped: Optional[str] = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.last_scraped is None:
            self.last_scraped = datetime.now().isoformat()


@dataclass
class HistoricalPriceModel:
    """Data class for historical prices"""
    property_id: int
    price: float
    date_recorded: str
    
    def __post_init__(self):
        if isinstance(self.date_recorded, datetime):
            self.date_recorded = self.date_recorded.strftime('%Y-%m-%d')
        elif self.date_recorded is None:
            self.date_recorded = datetime.now().strftime('%Y-%m-%d')

# Example usage and validation functions
def validate_property_data(property_data: Dict[str, Any]) -> bool:
    """
    Validate property data before inserting into database
    """
    # Check required fields
    required_fields = ['external_id', 'source']
    for field in required_fields:
        if field not in property_data or property_data[field] is None:
            return False
    
    # Validate price if present
    if 'price' in property_data and property_data['price'] is not None:
        if not isinstance(property_data['price'], (int, float)) or property_data['price'] <= 0:
            return False
    
    # Validate surface area if present
    if 'surface_area' in property_data and property_data['surface_area'] is not None:
        if not isinstance(property_data['surface_area'], (int, float)) or property_data['surface_area'] <= 0:
            return False
    
    # Validate room counts if present
    room_fields = ['rooms', 'bedrooms', 'bathrooms']
    for field in room_fields:
        if field in property_data and property_data[field] is not None:
            if not isinstance(property_data[field], int) or property_data[field] < 0:
                return False
    
    return True


def normalize_property_address(address: str) -> str:
    """
    Normalize property address for better matching
    """
    if not address:
        return ""
    
    # Convert to lowercase and strip whitespace
    normalized = address.lower().strip()
    
    # Remove common prefixes/suffixes that don't affect location
    prefixes = ['calle ', 'avenida ', 'plaza ', 'paseo ', 'c/', 'avda ', 'pg ']
    for prefix in prefixes:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
    
    # Remove extra whitespace
    normalized = ' '.join(normalized.split())
    
    return normalized