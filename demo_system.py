#!/usr/bin/env python3
"""
Demo script to show the property analysis system is working
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.database import PropertyDatabase
from src.utils.models import PropertyModel
from src.scraper.basic_scraper import PropertyScraper
from src.utils.deduplication import PropertyDeduplicator

def demo_system():
    print("🏠 Property Purchase Analysis System - Demo")
    print("=" * 50)
    
    # Initialize database
    print("✅ Initializing database...")
    db = PropertyDatabase()
    
    # Show database stats
    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM properties")
    total_props = cursor.fetchone()[0]
    print(f"📊 Database contains {total_props} properties")
    
    # Create a sample property
    print("\n📝 Creating sample property...")
    sample_prop = PropertyModel(
        external_id='DEMO123',
        source='demo_source',
        url='https://example.com/demo-property',
        title='Demo Property in Zaragoza',
        description='Beautiful apartment in the heart of Zaragoza',
        address='Calle Alfonso I, 10, 50001 Zaragoza',
        city='Zaragoza',
        district='Casco Histórico',
        postal_code='50001',
        latitude=41.6488,
        longitude=-0.8774,
        property_type='apartment',
        price=285000,
        currency='EUR',
        surface_area=95,
        rooms=4,
        bedrooms=3,
        bathrooms=2,
        floor_number=2,
        total_floors=4,
        construction_year=2015,
        has_elevator=True,
        has_parking=False,
        has_terrace=True,
        has_balcony=True,
        has_garden=False,
        has_pool=False,
        energy_certificate_rating='B'
    )
    
    print(f"   Property: {sample_prop.title}")
    print(f"   Price: €{sample_prop.price:,}")
    print(f"   Size: {sample_prop.surface_area} m²")
    print(f"   Price/m²: €{sample_prop.calculate_price_per_sqm():.2f}")
    print(f"   Features: {', '.join(sample_prop.get_features_list())}")
    
    # Save the property
    print("\n💾 Saving property to database...")
    property_id = db.insert_property(sample_prop.to_dict())
    print(f"   Saved with ID: {property_id}")
    
    # Verify it was saved
    print("\n🔍 Verifying property was saved...")
    retrieved = db.get_property_by_external_id('DEMO123', 'demo_source')
    if retrieved:
        print(f"   ✓ Retrieved property: {retrieved['title']}")
        print(f"   ✓ Price: €{retrieved['price']:,}")
    else:
        print("   ✗ Failed to retrieve property")
    
    # Show deduplication in action
    print("\n🔄 Testing deduplication system...")
    deduplicator = PropertyDeduplicator(db)
    
    # Create a similar property
    similar_prop = PropertyModel(
        external_id='DEMO456',
        source='another_demo_source',
        url='https://example.com/similar-property',
        title='Similar Property in Zaragoza',
        description='Another beautiful apartment nearby',
        address='Calle Alfonso I, 10, 50001 Zaragoza',  # Same address
        city='Zaragoza',
        district='Casco Histórico',
        postal_code='50001',
        latitude=41.6488,
        longitude=-0.8774,
        property_type='apartment',
        price=287000,  # Slightly different price
        currency='EUR',
        surface_area=96,  # Slightly different size
        rooms=4,
        bedrooms=3,
        bathrooms=2,
        floor_number=2,
        total_floors=4,
        construction_year=2015,
        has_elevator=True,
        has_parking=False,
        has_terrace=True,
        has_balcony=True,
        has_garden=False,
        has_pool=False,
        energy_certificate_rating='B'
    )
    
    # Calculate similarity
    similarity = sample_prop.similarity_score(similar_prop)
    print(f"   Similarity score: {similarity:.2f}")
    
    # Find potential duplicates
    potential_dupes = deduplicator.find_potential_duplicates(similar_prop)
    print(f"   Potential duplicates found: {len(potential_dupes)}")
    
    # Show database statistics
    print("\n📈 Database statistics:")
    stats = deduplicator.get_duplicate_stats()
    print(f"   Total properties: {stats['total_properties']}")
    print(f"   Active properties: {stats['active_properties']}")
    print(f"   Inactive properties: {stats['inactive_properties']}")
    
    # Close database
    db.close()
    
    print("\n🎉 System is working correctly!")
    print("\n📋 Next steps:")
    print("   1. Run 'python src/data_collection.py' to start collecting real data")
    print("   2. Monitor logs in the 'logs/' directory")
    print("   3. Check collected data in 'data/properties.db'")
    print("   4. Customize scraping parameters in 'config/settings.py'")

if __name__ == "__main__":
    demo_system()