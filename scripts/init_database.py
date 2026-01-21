#!/usr/bin/env python3
"""
Initialize database schema
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.etl.loaders import DataLoader
from supabase import create_client
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


def read_sql_file(file_path: str) -> str:
    """Read SQL file content"""
    with open(file_path, 'r') as f:
        return f.read()


def execute_sql_statements(supabase_client, sql_content: str):
    """Execute SQL statements (note: Supabase has limitations on direct SQL)"""
    logger.info("Note: Supabase uses REST API, not direct SQL execution")
    logger.info("Please run SQL files directly in Supabase SQL Editor:")
    logger.info("1. Go to your Supabase Dashboard")
    logger.info("2. Navigate to SQL Editor")
    logger.info("3. Copy and paste the SQL from data/schemas/")
    logger.info("4. Execute the statements")
    

def init_database():
    """Initialize database with schema"""
    try:
        logger.info("=" * 60)
        logger.info("DATABASE INITIALIZATION")
        logger.info("=" * 60)
        
        # Check environment
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        
        # Connect to Supabase
        supabase = create_client(supabase_url, supabase_key)
        logger.info("✅ Connected to Supabase")
        
        # Get SQL files
        base_dir = Path(__file__).parent.parent
        schema_dir = base_dir / 'data' / 'schemas'
        
        sql_files = [
            'create_tables.sql',
            'star_schema.sql',
            'indexes.sql'
        ]
        
        logger.info("\n📋 SQL Files to execute:")
        for sql_file in sql_files:
            file_path = schema_dir / sql_file
            if file_path.exists():
                logger.info(f"  ✓ {sql_file}")
                sql_content = read_sql_file(str(file_path))
                logger.info(f"    Lines: {len(sql_content.splitlines())}")
            else:
                logger.warning(f"  ✗ {sql_file} not found")
        
        execute_sql_statements(supabase, "")
        
        logger.info("\n" + "=" * 60)
        logger.info("✨ Database initialization guide displayed")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        raise


if __name__ == "__main__":
    init_database()