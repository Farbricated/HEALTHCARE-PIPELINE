import pytest
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_data():
    """Create sample supply chain data"""
    data = {
        'product_id': ['PROD001', 'PROD002', 'PROD003'],
        'product_name': ['Paracetamol 500mg', 'Amoxicillin 250mg', 'Insulin Injection'],
        'batch_number': ['BATCH-001', 'BATCH-002', 'BATCH-003'],
        'quantity': [5000, 3000, 1500],
        'unit_price': [2.50, 5.75, 25.00],
        'warehouse_location': ['Warehouse A', 'Warehouse B', 'Warehouse A'],
        'expiry_date': [
            datetime.now() + timedelta(days=365),
            datetime.now() + timedelta(days=180),
            datetime.now() + timedelta(days=90)
        ],
        'manufacture_date': [
            datetime.now() - timedelta(days=30),
            datetime.now() - timedelta(days=45),
            datetime.now() - timedelta(days=60)
        ],
        'status': ['active', 'active', 'active']
    }
    return pd.DataFrame(data)


@pytest.fixture
def invalid_data():
    """Create invalid data for testing validation"""
    data = {
        'product_id': ['PROD001', None, 'PROD003'],
        'product_name': ['Product 1', 'Product 2', None],
        'batch_number': ['BATCH-001', 'BATCH-001', 'BATCH-003'],  # Duplicate
        'quantity': [1000, -500, 2000],  # Negative value
        'unit_price': [10.0, 20.0, -5.0],  # Negative value
        'warehouse_location': ['Warehouse A', 'Warehouse B', 'Invalid'],
        'expiry_date': [
            datetime.now() + timedelta(days=100),
            datetime.now() - timedelta(days=10),  # Expired
            datetime.now() + timedelta(days=200)
        ],
        'manufacture_date': [
            datetime.now() - timedelta(days=50),
            datetime.now() + timedelta(days=50),  # Future date
            datetime.now() - timedelta(days=30)
        ],
        'status': ['active', 'active', 'inactive']
    }
    return pd.DataFrame(data)


@pytest.fixture
def mock_supabase_client(monkeypatch):
    """Mock Supabase client for testing"""
    class MockResponse:
        def __init__(self, data):
            self.data = data
            self.count = len(data) if isinstance(data, list) else 1
    
    class MockTable:
        def __init__(self):
            self.data = []
        
        def select(self, *args, **kwargs):
            return self
        
        def insert(self, data):
            if isinstance(data, list):
                self.data.extend(data)
            else:
                self.data.append(data)
            return self
        
        def execute(self):
            return MockResponse(self.data)
        
        def order(self, *args, **kwargs):
            return self
        
        def limit(self, *args, **kwargs):
            return self
    
    class MockSupabase:
        def table(self, name):
            return MockTable()
    
    return MockSupabase()


@pytest.fixture
def temp_csv_file(tmp_path, sample_data):
    """Create temporary CSV file for testing"""
    csv_path = tmp_path / "test_data.csv"
    sample_data.to_csv(csv_path, index=False)
    return str(csv_path)