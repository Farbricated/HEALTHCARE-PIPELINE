import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
from pathlib import Path
import time

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoader:
    """Load data using Supabase client"""
    
    def __init__(self):
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY required in .env")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("✅ Supabase client connected successfully")
    
    def load_to_database(self, df: pd.DataFrame, table_name: str = 'supply_chain_data') -> int:
        """Load dataframe to Supabase table"""
        try:
            logger.info(f"Loading {len(df)} records to table: {table_name}")
            
            # Prepare data
            df_prepared = self._prepare_for_loading(df)
            logger.info(f"Prepared {len(df_prepared)} records with {len(df_prepared.columns)} columns")
            
            # Convert to list of dicts
            records = df_prepared.to_dict('records')
            
            # Insert in batches of 100
            batch_size = 100
            total_loaded = 0
            
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                response = self.supabase.table(table_name).insert(batch).execute()
                total_loaded += len(batch)
                logger.info(f"✓ Loaded batch {i//batch_size + 1}: {len(batch)} records")
            
            logger.info(f"✅ Successfully loaded {total_loaded} records")
            return total_loaded
            
        except Exception as e:
            logger.error(f"❌ Error loading data: {e}")
            raise
    
    def _prepare_for_loading(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare dataframe for database loading"""
        columns_to_keep = [
            'product_id', 'product_name', 'batch_number', 
            'quantity', 'unit_price', 'warehouse_location',
            'expiry_date', 'manufacture_date', 'status'
        ]
        
        df_prepared = df[[col for col in columns_to_keep if col in df.columns]].copy()
        
        # Convert dates to ISO format strings
        for col in ['expiry_date', 'manufacture_date']:
            if col in df_prepared.columns:
                df_prepared[col] = pd.to_datetime(df_prepared[col]).dt.strftime('%Y-%m-%d')
        
        # Handle NaN values
        df_prepared = df_prepared.fillna({
            'warehouse_location': 'Unknown',
            'unit_price': 0.0,
            'status': 'active'
        })
        
        return df_prepared
    
    def verify_data(self, table_name: str = 'supply_chain_data') -> int:
        """Verify data was loaded"""
        try:
            response = self.supabase.table(table_name).select("*", count='exact').execute()
            count = response.count
            logger.info(f"✅ Verified: {count} total records in database")
            return count
        except Exception as e:
            logger.error(f"Error verifying data: {e}")
            return 0

    def log_pipeline_execution(self, pipeline_name: str, status: str, 
                               records_processed: int, errors_count: int,
                               execution_time: float, error_message: str = None):
        """Log pipeline execution"""
        try:
            log_data = {
                'pipeline_name': pipeline_name,
                'status': status,
                'records_processed': records_processed,
                'errors_count': errors_count,
                'execution_time_seconds': execution_time,
                'error_message': error_message
            }
            
            self.supabase.table('pipeline_logs').insert(log_data).execute()
            logger.info("📝 Pipeline execution logged")
            
        except Exception as e:
            logger.error(f"Error logging pipeline: {e}")


def main():
    """Run complete ETL pipeline"""
    start_time = time.time()
    
    try:
        print("\n" + "="*60)
        print("🚀 HEALTHCARE SUPPLY CHAIN ETL PIPELINE")
        print("="*60 + "\n")
        
        # Import here to avoid circular imports
        from extractors import DataExtractor
        from transformers import DataTransformer
        
        # Step 1: Extract
        print("📥 STEP 1: Extracting data...")
        extractor = DataExtractor()
        df = extractor.extract_from_csv("data/sample/sample_supply_chain.csv")
        print(f"   ✓ Extracted {len(df)} records\n")
        
        # Step 2: Transform
        print("🔄 STEP 2: Transforming data...")
        transformer = DataTransformer()
        df_clean = transformer.clean_data(df)
        df_enriched = transformer.enrich_data(df_clean)
        print(f"   ✓ Transformed {len(df_enriched)} records\n")
        
        # Step 3: Load
        print("💾 STEP 3: Loading to database...")
        loader = DataLoader()
        rows_loaded = loader.load_to_database(df_enriched, 'supply_chain_data')
        print(f"   ✓ Loaded {rows_loaded} records\n")
        
        # Step 4: Verify
        print("✅ STEP 4: Verifying data...")
        total_records = loader.verify_data('supply_chain_data')
        print(f"   ✓ Total records in database: {total_records}\n")
        
        # Log success
        execution_time = time.time() - start_time
        loader.log_pipeline_execution(
            pipeline_name='healthcare_etl',
            status='success',
            records_processed=rows_loaded,
            errors_count=0,
            execution_time=execution_time
        )
        
        print("="*60)
        print(f"✨ Pipeline completed in {execution_time:.2f} seconds")
        print("="*60 + "\n")
        
    except Exception as e:
        execution_time = time.time() - start_time
        print(f"\n❌ Pipeline failed: {e}\n")
        
        # Try to log failure
        try:
            loader = DataLoader()
            loader.log_pipeline_execution(
                pipeline_name='healthcare_etl',
                status='failed',
                records_processed=0,
                errors_count=1,
                execution_time=execution_time,
                error_message=str(e)
            )
        except:
            pass

if __name__ == "__main__":
    main()