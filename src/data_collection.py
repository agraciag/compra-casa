#!/usr/bin/env python3
"""
Initial Data Collection Script for Property Purchase Project

This script initializes the database, sets up the scraper, and begins collecting 
property data from various sources in Zaragoza with careful rate limiting.
"""

import os
import sys
import time
import random
from datetime import datetime
import logging

# Add the project root to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.database import PropertyDatabase
from src.scraper.basic_scraper import PropertyScraper
from src.utils.models import PropertyModel
from src.utils.deduplication import PropertyDeduplicator
from config.settings import SCRAPING_CONFIG, SOURCE_CONFIGS, LOCATION_FILTERS


def setup_logging():
    """Set up logging for the data collection process"""
    log_dir = SCRAPING_CONFIG.get('log_dir', 'logs/')
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, SCRAPING_CONFIG.get('level', 'INFO')),
        format=SCRAPING_CONFIG.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.FileHandler(f"{log_dir}data_collection.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def initialize_systems():
    """Initialize database, scraper, and other systems"""
    logger = setup_logging()
    logger.info("Initializing property data collection system...")
    
    # Initialize database
    logger.info("Setting up database...")
    db = PropertyDatabase()
    
    # Initialize deduplicator
    logger.info("Setting up deduplication system...")
    deduplicator = PropertyDeduplicator(db)
    
    # Initialize scraper
    logger.info("Setting up scraper...")
    scraper = PropertyScraper(db)
    
    logger.info("All systems initialized successfully!")
    
    return db, deduplicator, scraper, logger


def collect_sample_data(scraper, logger):
    """Collect sample data from configured sources"""
    logger.info("Starting sample data collection...")
    
    # Define sample URLs for testing (these would need to be real URLs in practice)
    sample_urls = {
        'idealista': [
            # These are example URLs - would need real URLs in practice
        ],
        'fotocasa': [
            # These are example URLs - would need real URLs in practice
        ],
        'habitaclia': [
            # These are example URLs - would need real URLs in practice
        ]
    }
    
    # For now, let's focus on scraping listing pages instead of individual properties
    sources_to_scrape = ['idealista', 'fotocasa', 'habitaclia']  # Only sources we have parsers for
    
    for source in sources_to_scrape:
        logger.info(f"Scraping listings from {source}...")
        
        try:
            # Scrape a limited number of pages per source (very conservatively)
            max_pages = SOURCE_CONFIGS.get(source, {}).get('max_pages_per_session', 3)
            logger.info(f"Scraping {max_pages} pages from {source}")
            
            scraper.scrape_zaragoza_listings(source, max_pages=max_pages)
            
            # Add a significant delay between sources to be respectful
            delay = random.uniform(30, 60)  # 30-60 second delay between sources
            logger.info(f"Waiting {delay:.2f} seconds before scraping next source...")
            time.sleep(delay)
            
        except Exception as e:
            logger.error(f"Error scraping {source}: {str(e)}")
            continue
    
    logger.info("Sample data collection completed!")


def verify_data(db, logger):
    """Verify that data was collected correctly"""
    logger.info("Verifying collected data...")
    
    cursor = db.conn.cursor()
    
    # Count total properties
    cursor.execute("SELECT COUNT(*) FROM properties")
    total_props = cursor.fetchone()[0]
    
    # Count active properties
    cursor.execute("SELECT COUNT(*) FROM properties WHERE is_active = 1")
    active_props = cursor.fetchone()[0]
    
    # Count properties by source
    cursor.execute("SELECT source, COUNT(*) FROM properties GROUP BY source")
    props_by_source = cursor.fetchall()
    
    # Count properties by city (should be mostly Zaragoza)
    cursor.execute("SELECT city, COUNT(*) FROM properties GROUP BY city")
    props_by_city = cursor.fetchall()
    
    logger.info(f"Data verification results:")
    logger.info(f"  Total properties: {total_props}")
    logger.info(f"  Active properties: {active_props}")
    logger.info(f"  Properties by source: {dict(props_by_source)}")
    logger.info(f"  Properties by city: {dict(props_by_city)}")
    
    # Show duplicate statistics
    dup_stats = db.get_duplicate_stats()
    logger.info(f"  Duplicate statistics: {dup_stats}")


def display_sample_properties(db, logger, limit=5):
    """Display some sample properties from the database"""
    logger.info(f"Displaying sample of {limit} properties...")
    
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT id, source, title, price, surface_area, bedrooms, district, address 
        FROM properties 
        WHERE is_active = 1 
        ORDER BY scraped_at DESC 
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    
    for row in rows:
        logger.info(f"  Property ID {row[0]} ({row[1]}):")
        logger.info(f"    Title: {row[2][:50]}{'...' if len(row[2]) > 50 else ''}")
        logger.info(f"    Price: €{row[3]:,} | Area: {row[4]} m² | Bedrooms: {row[5]}")
        logger.info(f"    District: {row[6]} | Address: {row[7][:30]}{'...' if len(row[7]) > 30 else ''}")
        logger.info("")


def main():
    """Main function to run the initial data collection"""
    print("Starting initial data collection for property purchase project...")
    print("="*60)
    
    # Initialize all systems
    db, deduplicator, scraper, logger = initialize_systems()
    
    try:
        # Collect sample data
        collect_sample_data(scraper, logger)
        
        # Verify the data
        verify_data(db, logger)
        
        # Display sample properties
        display_sample_properties(db, logger)
        
        # Show deduplication statistics
        dup_stats = deduplicator.get_duplicate_stats()
        logger.info(f"Deduplication statistics: {dup_stats}")
        
        print("\n" + "="*60)
        print("Initial data collection completed successfully!")
        print(f"Database file: {db.db_path}")
        print(f"Total properties collected: {dup_stats['total_properties']}")
        print(f"Active properties: {dup_stats['active_properties']}")
        print("="*60)
        
    except KeyboardInterrupt:
        logger.info("Data collection interrupted by user")
    except Exception as e:
        logger.error(f"An error occurred during data collection: {str(e)}")
        print(f"Error: {str(e)}")
    finally:
        # Clean up resources
        scraper.close()
        db.close()
        logger.info("Systems shut down gracefully")


def show_project_status():
    """Show the current status of the project"""
    print("\nPROJECT STATUS:")
    print("-" * 20)
    print("✅ Database schema created (SQLite)")
    print("✅ Configuration for slow scraping set up")
    print("✅ Data models created")
    print("✅ Deduplication logic implemented")
    print("✅ Basic scraper with rate limiting implemented")
    print("✅ Initial data collection script created")
    print("")
    print("NEXT STEPS:")
    print("- Run this script to begin collecting data")
    print("- Monitor logs for any issues")
    print("- Gradually increase scraping volume as needed")
    print("- Implement additional source parsers if needed")
    print("- Set up periodic runs using scheduler")


if __name__ == "__main__":
    # Show project status
    show_project_status()
    
    # Ask user if they want to proceed with data collection
    response = input("\nWould you like to proceed with initial data collection? (y/n): ")
    
    if response.lower() in ['y', 'yes']:
        main()
    else:
        print("Data collection skipped. You can run this script later with: python src/data_collection.py")