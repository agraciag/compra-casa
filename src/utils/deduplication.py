import re
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
from .models import PropertyModel
from .database import PropertyDatabase


class PropertyDeduplicator:
    """
    Handles detection and management of duplicate properties across different sources
    """
    
    def __init__(self, db: PropertyDatabase, similarity_threshold: float = 0.85):
        self.db = db
        self.similarity_threshold = similarity_threshold
    
    def find_potential_duplicates(self, new_property: PropertyModel) -> List[Dict]:
        """
        Find potential duplicate properties for a new listing
        """
        potential_duplicates = []
        
        # First, try to find by external_id if it's from the same source
        existing_by_external_id = self.db.get_property_by_external_id(
            new_property.external_id, 
            new_property.source
        )
        
        if existing_by_external_id:
            # This is the same property from the same source, just an update
            return [existing_by_external_id]
        
        # Look for similar properties based on multiple criteria
        similar_by_address = self._find_by_address(new_property)
        similar_by_coordinates = self._find_by_coordinates(new_property)
        similar_by_details = self._find_by_details(new_property)
        
        # Combine all potential duplicates
        all_candidates = []
        all_candidates.extend(similar_by_address)
        all_candidates.extend(similar_by_coordinates)
        all_candidates.extend(similar_by_details)
        
        # Remove duplicates from the candidate list
        unique_candidates = {}
        for candidate in all_candidates:
            key = f"{candidate['source']}_{candidate['external_id']}"
            if key not in unique_candidates:
                unique_candidates[key] = candidate
        
        # Calculate similarity scores for each candidate
        for candidate in unique_candidates.values():
            candidate_property = PropertyModel.from_dict(candidate)
            similarity = new_property.similarity_score(candidate_property)
            
            if similarity >= self.similarity_threshold:
                candidate['similarity_score'] = similarity
                potential_duplicates.append(candidate)
        
        # Sort by similarity score (highest first)
        potential_duplicates.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        return potential_duplicates
    
    def _find_by_address(self, property_model: PropertyModel) -> List[Dict]:
        """
        Find properties with similar addresses
        """
        if not property_model.address:
            return []
        
        # Normalize the address for comparison
        normalized_address = self._normalize_address(property_model.address)
        
        # Query for properties with similar addresses
        cursor = self.db.conn.cursor()
        cursor.execute(
            "SELECT * FROM properties WHERE address LIKE ? AND is_active = 1",
            (f"%{normalized_address}%",)
        )
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def _find_by_coordinates(self, property_model: PropertyModel) -> List[Dict]:
        """
        Find properties with similar coordinates (within a tolerance)
        """
        if not property_model.latitude or not property_model.longitude:
            return []
        
        # Define a small tolerance for coordinate matching (approx. 100 meters)
        lat_tolerance = 0.001  # degrees
        lon_tolerance = 0.001  # degrees
        
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT * FROM properties 
            WHERE is_active = 1
            AND latitude BETWEEN ? AND ?
            AND longitude BETWEEN ? AND ?
        ''', (
            property_model.latitude - lat_tolerance,
            property_model.latitude + lat_tolerance,
            property_model.longitude - lon_tolerance,
            property_model.longitude + lon_tolerance
        ))
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def _find_by_details(self, property_model: PropertyModel) -> List[Dict]:
        """
        Find properties with similar price, size, and room count
        """
        if not all([property_model.price, property_model.surface_area, property_model.bedrooms]):
            return []
        
        # Define tolerances for matching
        price_tolerance = 0.1  # 10% tolerance
        size_tolerance = 0.15  # 15% tolerance
        room_tolerance = 1     # 1 room tolerance
        
        min_price = property_model.price * (1 - price_tolerance)
        max_price = property_model.price * (1 + price_tolerance)
        
        min_surface = property_model.surface_area * (1 - size_tolerance)
        max_surface = property_model.surface_area * (1 + size_tolerance)
        
        min_bedrooms = max(0, property_model.bedrooms - room_tolerance)
        max_bedrooms = property_model.bedrooms + room_tolerance
        
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT * FROM properties 
            WHERE is_active = 1
            AND price BETWEEN ? AND ?
            AND surface_area BETWEEN ? AND ?
            AND bedrooms BETWEEN ? AND ?
        ''', (min_price, max_price, min_surface, max_surface, min_bedrooms, max_bedrooms))
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def _normalize_address(self, address: str) -> str:
        """
        Normalize address for comparison purposes
        """
        if not address:
            return ""
        
        # Convert to lowercase
        normalized = address.lower()
        
        # Remove common address prefixes/suffixes
        prefixes = [
            'calle ', 'cl ', 'c/', 'avenida ', 'avda ', 'av ', 'plaza ', 'pl ', 
            'paseo ', 'pg ', 'glorieta ', 'gl ', 'travesia ', 'tv ', 'carretera ', 'cr '
        ]
        
        for prefix in prefixes:
            normalized = normalized.replace(prefix, '')
        
        # Remove extra whitespace and common separators
        normalized = re.sub(r'\s+', ' ', normalized.strip())
        
        # Remove special characters except for numbers and letters
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        
        return normalized
    
    def handle_duplicate_property(self, new_property: PropertyModel, 
                                  duplicates: List[Dict]) -> Tuple[bool, Optional[int]]:
        """
        Handle a property that has been identified as a duplicate
        
        Returns:
        - bool: True if this is a duplicate update, False if it's a new property
        - int or None: ID of the existing property if it's a duplicate, None otherwise
        """
        if not duplicates:
            # No duplicates found, this is a new property
            return False, None
        
        # Get the highest similarity match
        best_match = duplicates[0]
        existing_id = best_match['id']
        
        # Update the existing property with new information
        updated_property = self._merge_property_data(
            PropertyModel.from_dict(best_match), 
            new_property
        )
        
        # Update the database record
        cursor = self.db.conn.cursor()
        cursor.execute('''
            UPDATE properties 
            SET title = COALESCE(?, title),
                description = COALESCE(?, description),
                price = COALESCE(?, price),
                surface_area = COALESCE(?, surface_area),
                rooms = COALESCE(?, rooms),
                bedrooms = COALESCE(?, bedrooms),
                bathrooms = COALESCE(?, bathrooms),
                has_elevator = COALESCE(?, has_elevator),
                has_parking = COALESCE(?, has_parking),
                has_terrace = COALESCE(?, has_terrace),
                has_balcony = COALESCE(?, has_balcony),
                has_garden = COALESCE(?, has_garden),
                has_pool = COALESCE(?, has_pool),
                energy_certificate_rating = COALESCE(?, energy_certificate_rating),
                property_condition = COALESCE(?, property_condition),
                is_active = 1,
                last_seen_date = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            updated_property.title,
            updated_property.description,
            updated_property.price,
            updated_property.surface_area,
            updated_property.rooms,
            updated_property.bedrooms,
            updated_property.bathrooms,
            updated_property.has_elevator,
            updated_property.has_parking,
            updated_property.has_terrace,
            updated_property.has_balcony,
            updated_property.has_garden,
            updated_property.has_pool,
            updated_property.energy_certificate_rating,
            updated_property.property_condition,
            updated_property.last_seen_date,
            existing_id
        ))
        
        self.db.conn.commit()
        
        # Record the price if it changed
        if new_property.price and new_property.price != best_match.get('price'):
            self._record_price_change(existing_id, new_property.price)
        
        return True, existing_id
    
    def _merge_property_data(self, existing: PropertyModel, 
                           new_data: PropertyModel) -> PropertyModel:
        """
        Merge new property data with existing data, prioritizing non-null values
        """
        # Create a new property with existing data as base
        merged = PropertyModel(
            external_id=existing.external_id,
            source=existing.source,
            url=new_data.url or existing.url,
            title=new_data.title or existing.title,
            description=new_data.description or existing.description,
            address=existing.address,  # Keep original address to maintain consistency
            city=existing.city,
            district=new_data.district or existing.district,
            postal_code=new_data.postal_code or existing.postal_code,
            latitude=new_data.latitude or existing.latitude,
            longitude=new_data.longitude or existing.longitude,
            property_type=new_data.property_type or existing.property_type,
            price=new_data.price or existing.price,
            currency=existing.currency,  # Keep original currency
            surface_area=new_data.surface_area or existing.surface_area,
            rooms=new_data.rooms or existing.rooms,
            bedrooms=new_data.bedrooms or existing.bedrooms,
            bathrooms=new_data.bathrooms or existing.bathrooms,
            floor_number=new_data.floor_number or existing.floor_number,
            total_floors=new_data.total_floors or existing.total_floors,
            construction_year=new_data.construction_year or existing.construction_year,
            has_elevator=new_data.has_elevator if new_data.has_elevator is not None else existing.has_elevator,
            has_parking=new_data.has_parking if new_data.has_parking is not None else existing.has_parking,
            parking_price=new_data.parking_price or existing.parking_price,
            has_terrace=new_data.has_terrace if new_data.has_terrace is not None else existing.has_terrace,
            has_balcony=new_data.has_balcony if new_data.has_balcony is not None else existing.has_balcony,
            has_garden=new_data.has_garden if new_data.has_garden is not None else existing.has_garden,
            has_pool=new_data.has_pool if new_data.has_pool is not None else existing.has_pool,
            energy_certificate_rating=new_data.energy_certificate_rating or existing.energy_certificate_rating,
            property_condition=new_data.property_condition or existing.property_condition,
            is_active=True,  # Always set to active when updating
            first_seen_date=existing.first_seen_date,
            last_seen_date=new_data.last_seen_date,
            scraped_at=new_data.scraped_at
        )
        
        return merged
    
    def _record_price_change(self, property_id: int, new_price: float):
        """
        Record a price change for historical tracking
        """
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO historical_prices (property_id, price, date_recorded)
            VALUES (?, ?, DATE('now'))
        ''', (property_id, new_price))
        
        self.db.conn.commit()
    
    def mark_property_inactive(self, external_id: str, source: str):
        """
        Mark a property as inactive (removed from source)
        """
        cursor = self.db.conn.cursor()
        cursor.execute('''
            UPDATE properties 
            SET is_active = 0, last_seen_date = DATE('now')
            WHERE external_id = ? AND source = ?
        ''', (external_id, source))
        
        self.db.conn.commit()
    
    def get_duplicate_stats(self) -> Dict[str, int]:
        """
        Get statistics about duplicate detection
        """
        cursor = self.db.conn.cursor()
        
        # Count active properties
        cursor.execute("SELECT COUNT(*) FROM properties WHERE is_active = 1")
        active_count = cursor.fetchone()[0]
        
        # Count inactive properties
        cursor.execute("SELECT COUNT(*) FROM properties WHERE is_active = 0")
        inactive_count = cursor.fetchone()[0]
        
        # Count total properties
        cursor.execute("SELECT COUNT(*) FROM properties")
        total_count = cursor.fetchone()[0]
        
        return {
            'total_properties': total_count,
            'active_properties': active_count,
            'inactive_properties': inactive_count
        }


def calculate_address_similarity(addr1: str, addr2: str) -> float:
    """
    Calculate similarity between two addresses using sequence matching
    """
    if not addr1 or not addr2:
        return 0.0
    
    # Normalize addresses
    norm_addr1 = re.sub(r'[^a-zA-Z0-9\s]', '', addr1.lower().strip())
    norm_addr2 = re.sub(r'[^a-zA-Z0-9\s]', '', addr2.lower().strip())
    
    return SequenceMatcher(None, norm_addr1, norm_addr2).ratio()


def find_exact_duplicate(db: PropertyDatabase, external_id: str, source: str) -> Optional[Dict]:
    """
    Find an exact duplicate by external_id and source
    """
    return db.get_property_by_external_id(external_id, source)