#!/usr/bin/env python3
"""
Scoped Data Collection Script for Property Purchase Project

Scrapes Idealista and Fotocasa using pre-filtered URLs so only
in-scope properties (price, bedrooms, bathrooms, parking) are fetched.
"""

import os
import sys
import time
import random
from datetime import datetime
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.database import PropertyDatabase
from src.scraper.basic_scraper import PropertyScraper
from src.utils.deduplication import PropertyDeduplicator
from config.settings import LOGGING_CONFIG, SEARCH_SCOPE, FILTERED_SEARCH_URLS


def setup_logging():
    log_dir = LOGGING_CONFIG.get('log_dir', 'logs/')
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, LOGGING_CONFIG.get('level', 'INFO')),
        format=LOGGING_CONFIG.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.FileHandler(f"{log_dir}data_collection.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def main():
    logger = setup_logging()
    sources = SEARCH_SCOPE.get('sources', ['idealista', 'fotocasa'])
    max_pages = SEARCH_SCOPE.get('max_pages', 2)

    logger.info("=" * 60)
    logger.info("Scoped data collection starting")
    logger.info(f"  Sources: {', '.join(sources)}")
    logger.info(f"  Pages per source: {max_pages}")
    logger.info(f"  Price: {SEARCH_SCOPE.get('min_price', '?')} - {SEARCH_SCOPE.get('max_price', '?')} EUR")
    logger.info(f"  Bedrooms: {SEARCH_SCOPE.get('min_bedrooms', '?')}+")
    logger.info(f"  Bathrooms: {SEARCH_SCOPE.get('min_bathrooms', '?')}+")
    logger.info(f"  Parking: {'required' if SEARCH_SCOPE.get('has_parking') else 'optional'}")
    logger.info("=" * 60)

    db = PropertyDatabase()
    scraper = PropertyScraper(db)
    deduplicator = PropertyDeduplicator(db)

    try:
        for source in sources:
            if source not in FILTERED_SEARCH_URLS:
                logger.warning(f"No filtered URL for {source}, skipping")
                continue

            logger.info(f"Scraping {source}...")
            logger.info(f"  Base URL: {FILTERED_SEARCH_URLS[source][:80]}...")

            try:
                scraper.scrape_zaragoza_listings(source, max_pages=max_pages)
            except Exception as e:
                logger.error(f"Error scraping {source}: {e}")

            # Delay between sources
            if source != sources[-1]:
                delay = random.uniform(20, 40)
                logger.info(f"Waiting {delay:.0f}s before next source...")
                time.sleep(delay)

        # Report results
        stats = db.get_duplicate_stats()
        logger.info("=" * 60)
        logger.info("Collection complete!")
        logger.info(f"  Total properties in DB: {stats['total_properties']}")
        logger.info(f"  Active: {stats['active_properties']}")

        # Show recently scraped
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT source, COUNT(*) FROM properties
            WHERE is_active = 1 AND source != 'demo_source'
            GROUP BY source
        """)
        by_source = cursor.fetchall()
        for row in by_source:
            logger.info(f"  {row[0]}: {row[1]} properties")

        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        scraper.close()
        db.close()
        logger.info("Done")


if __name__ == "__main__":
    print(f"Scope: {SEARCH_SCOPE}")
    print(f"URLs:")
    for src, url in FILTERED_SEARCH_URLS.items():
        if src in SEARCH_SCOPE.get('sources', []):
            print(f"  {src}: {url[:90]}...")
    print()
    main()
