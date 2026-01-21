import pytest
import pandas as pd
from src.etl.extractors import DataExtractor
from src.etl.transformers import DataTransformer
from datetime import datetime


class TestDataExtractor:
    """Test data extraction functionality"""
    
    def test_extract_from_csv(self, temp_csv_file):
        """Test CSV extraction"""
        extractor = DataExtractor()
        df = extractor.extract_from_csv(temp_csv_file)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'product_id' in df.columns
    
    def test_extract_from_csv_missing_file(self):
        """Test extraction with missing file"""
        extractor = DataExtractor()
        
        with pytest.raises(Exception):
            extractor.extract_from_csv('nonexistent.csv')
    
    def test_extract_from_json(self, tmp_path):
        """Test JSON extraction"""
        json_data = [
            {'product_id': 'PROD001', 'quantity': 100},
            {'product_id': 'PROD002', 'quantity': 200}
        ]
        
        json_path = tmp_path / "test.json"
        pd.DataFrame(json_data).to_json(json_path, orient='records')
        
        extractor = DataExtractor()
        df = extractor.extract_from_json(str(json_path))
        
        assert len(df) == 2
        assert 'product_id' in df.columns


class TestDataTransformer:
    """Test data transformation functionality"""
    
    def test_clean_data(self, sample_data):
        """Test data cleaning"""
        transformer = DataTransformer()
        df_clean = transformer.clean_data(sample_data)
        
        assert len(df_clean) > 0
        assert df_clean['quantity'].dtype in ['int64', 'float64']
    
    def test_remove_duplicates(self):
        """Test duplicate removal"""
        data = pd.DataFrame({
            'product_id': ['PROD001', 'PROD001', 'PROD002'],
            'quantity': [100, 100, 200]
        })
        
        transformer = DataTransformer()
        df_clean = transformer.clean_data(data)
        
        assert len(df_clean) == 2  # One duplicate removed
    
    def test_enrich_data(self, sample_data):
        """Test data enrichment"""
        transformer = DataTransformer()
        df_clean = transformer.clean_data(sample_data)
        df_enriched = transformer.enrich_data(df_clean)
        
        assert 'days_until_expiry' in df_enriched.columns
        assert 'total_value' in df_enriched.columns
        assert 'stock_level' in df_enriched.columns
    
    def test_calculate_total_value(self, sample_data):
        """Test total value calculation"""
        transformer = DataTransformer()
        df_clean = transformer.clean_data(sample_data)
        df_enriched = transformer.enrich_data(df_clean)
        
        expected_value = sample_data.iloc[0]['quantity'] * sample_data.iloc[0]['unit_price']
        actual_value = df_enriched.iloc[0]['total_value']
        
        assert actual_value == expected_value
    
    def test_handle_missing_values(self):
        """Test missing value handling"""
        data = pd.DataFrame({
            'product_id': ['PROD001', None, 'PROD003'],
            'quantity': [100, 200, None],
            'unit_price': [10.0, None, 30.0]
        })
        
        transformer = DataTransformer()
        df_clean = transformer.clean_data(data)
        
        # Check that nulls are handled
        assert df_clean['quantity'].isnull().sum() == 0
        assert df_clean['unit_price'].isnull().sum() == 0
    
    def test_validate_negative_quantities(self):
        """Test validation removes negative quantities"""
        data = pd.DataFrame({
            'product_id': ['PROD001', 'PROD002'],
            'quantity': [100, -50],
            'unit_price': [10.0, 20.0]
        })
        
        transformer = DataTransformer()
        df_clean = transformer.clean_data(data)
        
        # Negative quantity should be removed
        assert len(df_clean) == 1
        assert df_clean.iloc[0]['quantity'] > 0


class TestDataValidation:
    """Test data validation"""
    
    def test_date_validation(self, invalid_data):
        """Test that invalid dates are caught"""
        transformer = DataTransformer()
        df_clean = transformer.clean_data(invalid_data)
        
        # Should remove records where expiry <= manufacture
        for idx, row in df_clean.iterrows():
            if pd.notna(row['expiry_date']) and pd.notna(row['manufacture_date']):
                assert row['expiry_date'] > row['manufacture_date']