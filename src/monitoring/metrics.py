import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import psutil
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemMetrics:
    """Collect system and pipeline metrics"""
    
    @staticmethod
    def get_system_health() -> Dict[str, Any]:
        """Get current system health metrics"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'status': 'healthy'
        }
    
    @staticmethod
    def calculate_pipeline_metrics(df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate pipeline processing metrics"""
        metrics = {
            'total_records': len(df),
            'total_value': 0,
            'avg_quantity': 0,
            'low_stock_items': 0,
            'expiring_soon': 0,
            'data_quality_score': 100
        }
        
        if 'quantity' in df.columns:
            metrics['avg_quantity'] = df['quantity'].mean()
            metrics['low_stock_items'] = (df['quantity'] < 100).sum()
        
        if 'total_value' in df.columns:
            metrics['total_value'] = df['total_value'].sum()
        elif 'quantity' in df.columns and 'unit_price' in df.columns:
            metrics['total_value'] = (df['quantity'] * df['unit_price']).sum()
        
        if 'days_until_expiry' in df.columns:
            metrics['expiring_soon'] = (df['days_until_expiry'] < 30).sum()
        
        # Data quality score
        completeness = (1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        metrics['data_quality_score'] = round(completeness, 2)
        
        return metrics


class PerformanceMonitor:
    """Monitor pipeline performance"""
    
    def __init__(self):
        self.start_time = None
        self.metrics = {}
    
    def start(self):
        """Start monitoring"""
        self.start_time = time.time()
        logger.info("Performance monitoring started")
    
    def stop(self) -> Dict[str, Any]:
        """Stop monitoring and return metrics"""
        if self.start_time is None:
            raise ValueError("Monitor not started")
        
        execution_time = time.time() - self.start_time
        
        self.metrics = {
            'execution_time_seconds': round(execution_time, 2),
            'execution_time_minutes': round(execution_time / 60, 2),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Performance monitoring stopped. Execution time: {execution_time:.2f}s")
        return self.metrics


class DataQualityMetrics:
    """Track data quality metrics over time"""
    
    def __init__(self):
        self.history = []
    
    def record_quality_score(self, df: pd.DataFrame, pipeline_name: str):
        """Record quality metrics for a dataset"""
        metrics = {
            'pipeline_name': pipeline_name,
            'timestamp': datetime.now().isoformat(),
            'record_count': len(df),
            'null_count': df.isnull().sum().sum(),
            'null_percentage': (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100,
            'duplicate_count': df.duplicated().sum(),
            'columns': len(df.columns)
        }
        
        self.history.append(metrics)
        return metrics
    
    def get_quality_trends(self) -> pd.DataFrame:
        """Get quality trends over time"""
        if not self.history:
            return pd.DataFrame()
        
        return pd.DataFrame(self.history)