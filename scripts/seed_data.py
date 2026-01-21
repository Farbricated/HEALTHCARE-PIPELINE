#!/usr/bin/env python3
"""
Seed database with sample data
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.etl.extractors import DataExtractor
from src.etl.transformers import DataTransformer
from src.etl.loaders import DataLoader
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_database():
    """Seed database with sample data"""
    try:
        logger.info("=" * 60)
        logger.info("DATABASE SEEDING")
        logger.info("=" * 60)
        
        # Extract sample data
        logger.info("\n📥 Step 1: Extracting sample data...")
        extractor = DataExtractor()
        df = extractor.extract_from_csv("data/sample/sample_supply_chain.csv")
        logger.info(f"  ✓ Loaded {len(df)} records")
        
        # Transform data
        logger.info("\n🔄 Step 2: Transforming data...")
        transformer = DataTransformer()
        df_clean = transformer.clean_data(df)
        df_enriched = transformer.enrich_data(df_clean)
        logger.info(f"  ✓ Transformed {len(df_enriched)} records")
        
        # Load to database
        logger.info("\n💾 Step 3: Loading to database...")
        loader = DataLoader()
        rows_loaded = loader.load_to_database(df_enriched, 'supply_chain_data')
        logger.info(f"  ✓ Loaded {rows_loaded} records")
        
        # Verify
        logger.info("\n✅ Step 4: Verifying...")
        total = loader.verify_data('supply_chain_data')
        logger.info(f"  ✓ Total records in database: {total}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✨ Database seeding completed successfully")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Error seeding database: {e}")
        raise


if __name__ == "__main__":
    seed_database()