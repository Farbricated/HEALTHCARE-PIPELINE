import pandas as pd
import requests
from typing import Dict, Any, Optional
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataExtractor:
    """Extract data from multiple sources"""
    
    def extract_from_csv(self, file_path: str) -> pd.DataFrame:
        """Extract data from CSV file"""
        try:
            logger.info(f"Extracting data from CSV: {file_path}")
            df = pd.read_csv(file_path)
            logger.info(f"Successfully extracted {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Error extracting CSV: {e}")
            raise
    
    def extract_from_json(self, file_path: str) -> pd.DataFrame:
        """Extract data from JSON file"""
        try:
            logger.info(f"Extracting data from JSON: {file_path}")
            df = pd.read_json(file_path)
            logger.info(f"Successfully extracted {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Error extracting JSON: {e}")
            raise
    
    def extract_from_excel(self, file_path: str, sheet_name: str = 0) -> pd.DataFrame:
        """Extract data from Excel file"""
        try:
            logger.info(f"Extracting data from Excel: {file_path}")
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            logger.info(f"Successfully extracted {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Error extracting Excel: {e}")
            raise
    
    def extract_from_api(self, url: str, headers: Optional[Dict] = None) -> pd.DataFrame:
        """Extract data from REST API"""
        try:
            logger.info(f"Extracting data from API: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Try common API response patterns
                if 'data' in data:
                    df = pd.DataFrame(data['data'])
                elif 'results' in data:
                    df = pd.DataFrame(data['results'])
                else:
                    df = pd.DataFrame([data])
            else:
                raise ValueError(f"Unexpected API response format: {type(data)}")
            
            logger.info(f"Successfully extracted {len(df)} records from API")
            return df
        except Exception as e:
            logger.error(f"Error extracting from API: {e}")
            raise

if __name__ == "__main__":
    # Test extraction
    extractor = DataExtractor()
    df = extractor.extract_from_csv("data/sample/sample_supply_chain.csv")
    print("\n=== Sample Data ===")
    print(df.head())
    print(f"\nShape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")