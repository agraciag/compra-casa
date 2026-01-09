#!/usr/bin/env python3
"""
Test script to verify the database and scraper setup
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.database import PropertyDatabase
from src.utils.models import PropertyModel
from src.scraper.basic_scraper import PropertyScraper
from src.utils.deduplication import PropertyDeduplicator

def test_database():
    """Test database creation and basic operations"""
    print("Testing database setup...")
    
    # Create database instance
    db = PropertyDatabase()
    
    # Test inserting a sample property
    sample_property = {
        'external_id': 'TEST123',
        'source': 'test_source',
        'url': 'https://example.com/test_property',
        'title': 'Test Property',
        'description': 'This is a test property for demonstration purposes.',
        'address': 'Calle Falsa 123, Zaragoza',
        'city': 'Zaragoza',
        'district': 'Centro',
        'postal_code': '50001',
        'property_type': 'apartment',
        'price': 250000,
        'currency': 'EUR',
        'surface_area': 100,
        'rooms': 4,
        'bedrooms': 3,
        'bathrooms': 2,
        'has_elevator': True,
        'has_parking': False,
        'has_terrace': True,
        'has_balcony': True,
        'has_garden': False,
        'has_pool': False,
        'energy_certificate_rating': 'B',
        'latitude': 41.6488,
        'longitude': -0.8851,
        'floor_number': 2,
        'total_floors': 4,
        'construction_year': 2010,
        'parking_price': None,
        'is_active': True,
        'first_seen_date': '2023-01-01',
        'last_seen_date': '2023-01-01',
        'scraped_at': '2023-01-01T00:00:00'
    }
    
    property_id = db.insert_property(sample_property)
    print(f"Inserted property with ID: {property_id}")
    
    # Retrieve the property
    retrieved = db.get_property_by_external_id('TEST123', 'test_source')
    print(f"Retrieved property: {retrieved['title']} - €{retrieved['price']:,}")
    
    # Close database
    db.close()
    print("Database test completed successfully!\n")

def test_models():
    """Test data models"""
    print("Testing data models...")
    
    # Create a property model
    prop = PropertyModel(
        external_id='MODEL_TEST123',
        source='test_source',
        title='Model Test Property',
        price=300000,
        surface_area=120,
        bedrooms=4,
        bathrooms=3,
        address='Avenida Principal 456, Zaragoza',
        city='Zaragoza',
        district='Delicias',
        has_parking=True,
        has_elevator=True
    )
    
    print(f"Created property model: {prop.title}")
    print(f"Price per sqm: €{prop.calculate_price_per_sqm():.2f}")
    print(f"Features: {prop.get_features_list()}")
    
    # Convert to dict and back
    prop_dict = prop.to_dict()
    prop_from_dict = PropertyModel.from_dict(prop_dict)
    print(f"Round-trip conversion successful: {prop_from_dict.title}")
    
    print("Model test completed successfully!\n")

def test_deduplication():
    """Test deduplication functionality"""
    print("Testing deduplication...")
    
    db = PropertyDatabase()
    deduplicator = PropertyDeduplicator(db)
    
    # Create two similar properties
    prop1 = PropertyModel(
        external_id='DUPE_TEST1',
        source='idealista',
        title='Similar Property 1',
        price=250000,
        surface_area=100,
        bedrooms=3,
        address='Calle Falsa 123, Zaragoza',
        city='Zaragoza',
        district='Centro'
    )
    
    prop2 = PropertyModel(
        external_id='DUPE_TEST2',
        source='fotocasa',
        title='Similar Property 2',
        price=252000,  # Slightly different price
        surface_area=102,  # Slightly different area
        bedrooms=3,
        address='Calle Falsa 123, Zaragoza',  # Same address
        city='Zaragoza',
        district='Centro'
    )
    
    # Calculate similarity
    similarity = prop1.similarity_score(prop2)
    print(f"Similarity between properties: {similarity:.2f}")
    
    # Insert first property
    db.insert_property(prop1.to_dict())
    
    # Find potential duplicates for second property
    potential_dupes = deduplicator.find_potential_duplicates(prop2)
    print(f"Potential duplicates found: {len(potential_dupes)}")
    
    db.close()
    print("Deduplication test completed successfully!\n")

def main():
    print("Running system tests...\n")
    
    try:
        test_database()
        test_models()
        test_deduplication()
        
        print("All tests completed successfully!")
        print("\nSystem is ready for data collection.")
        print("Run 'python src/data_collection.py' to start collecting property data.")
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()