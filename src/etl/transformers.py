import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataTransformer:
    """Transform and clean data"""
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate data"""
        logger.info("Starting data cleaning...")
        initial_count = len(df)
        
        # Remove duplicates
        df = df.drop_duplicates()
        logger.info(f"Removed {initial_count - len(df)} duplicate records")
        
        # Handle missing values
        df = self._handle_nulls(df)
        
        # Standardize column names
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        # Convert data types
        df = self._convert_datatypes(df)
        
        # Validate data
        df = self._validate_data(df)
        
        logger.info(f"Data cleaning complete. Final records: {len(df)}")
        return df
    
    def _handle_nulls(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle null values"""
        # Fill numeric nulls with 0
        numeric_cols = df.select_dtypes(include=['number']).columns
        df[numeric_cols] = df[numeric_cols].fillna(0)
        
        # Fill string nulls with 'Unknown'
        string_cols = df.select_dtypes(include=['object']).columns
        df[string_cols] = df[string_cols].fillna('Unknown')
        
        return df
    
    def _convert_datatypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert columns to appropriate data types"""
        # Convert date columns
        date_columns = ['expiry_date', 'manufacture_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Convert numeric columns
        if 'quantity' in df.columns:
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        
        if 'unit_price' in df.columns:
            df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
        
        return df
    
    def _validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate data quality"""
        initial_count = len(df)
        
        # Remove records with negative quantities
        if 'quantity' in df.columns:
            df = df[df['quantity'] >= 0]
            logger.info(f"Removed {initial_count - len(df)} records with negative quantity")
        
        # Remove records with invalid dates
        if 'expiry_date' in df.columns and 'manufacture_date' in df.columns:
            initial_count = len(df)
            df = df[df['expiry_date'] > df['manufacture_date']]
            logger.info(f"Removed {initial_count - len(df)} records with invalid dates")
        
        return df
    
    def enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add calculated columns"""
        logger.info("Enriching data with calculated fields...")
        
        # Calculate days until expiry
        if 'expiry_date' in df.columns:
            df['days_until_expiry'] = (df['expiry_date'] - pd.Timestamp.now()).dt.days
            logger.info("Added 'days_until_expiry' column")
        
        # Calculate total value
        if 'quantity' in df.columns and 'unit_price' in df.columns:
            df['total_value'] = df['quantity'] * df['unit_price']
            logger.info("Added 'total_value' column")
        
        # Add alert flags
        if 'days_until_expiry' in df.columns:
            df['expiry_alert'] = df['days_until_expiry'] < 30
            df['expiry_critical'] = df['days_until_expiry'] < 7
            logger.info("Added expiry alert columns")
        
        # Add stock level categorization
        if 'quantity' in df.columns:
            df['stock_level'] = pd.cut(
                df['quantity'],
                bins=[0, 100, 1000, 5000, float('inf')],
                labels=['Low', 'Medium', 'High', 'Very High']
            )
            logger.info("Added 'stock_level' categorization")
        
        return df

if __name__ == "__main__":
    # Test transformation
    from extractors import DataExtractor
    
    extractor = DataExtractor()
    transformer = DataTransformer()
    
    df = extractor.extract_from_csv("data/sample/sample_supply_chain.csv")
    print("\n=== Original Data ===")
    print(df.head())
    
    df_clean = transformer.clean_data(df)
    print("\n=== After Cleaning ===")
    print(df_clean.info())
    
    df_enriched = transformer.enrich_data(df_clean)
    print("\n=== After Enrichment ===")
    print(df_enriched.head())
    print(f"\nNew columns: {df_enriched.columns.tolist()}")