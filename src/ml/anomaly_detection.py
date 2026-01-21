import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detect anomalies in supply chain data"""
    
    def __init__(self, contamination=0.1):
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
    
    def detect_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect anomalies in the dataset"""
        logger.info("Detecting anomalies...")
        
        # Prepare features
        feature_cols = ['quantity', 'unit_price']
        if 'days_until_expiry' in df.columns:
            feature_cols.append('days_until_expiry')
        
        # Calculate total_value if not present
        if 'total_value' not in df.columns and all(col in df.columns for col in ['quantity', 'unit_price']):
            df['total_value'] = df['quantity'] * df['unit_price']
            feature_cols.append('total_value')
        
        X = df[feature_cols].fillna(0)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Fit and predict
        anomaly_labels = self.model.fit_predict(X_scaled)
        anomaly_scores = self.model.score_samples(X_scaled)
        
        # Add results to dataframe
        result = df.copy()
        result['is_anomaly'] = (anomaly_labels == -1).astype(int)
        result['anomaly_score'] = anomaly_scores
        
        anomaly_count = result['is_anomaly'].sum()
        logger.info(f"Detected {anomaly_count} anomalies ({anomaly_count/len(result)*100:.2f}%)")
        
        self.is_fitted = True
        return result
    
    def get_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get only anomalous records"""
        df_with_anomalies = self.detect_anomalies(df)
        return df_with_anomalies[df_with_anomalies['is_anomaly'] == 1]