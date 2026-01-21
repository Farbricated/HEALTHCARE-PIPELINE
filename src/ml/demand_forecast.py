import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import logging
from datetime import datetime, timedelta
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DemandForecaster:
    """ML model for demand forecasting"""
    
    def __init__(self, model_path='models/demand_forecast.pkl'):
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.model_path = model_path
        self.feature_columns = []
        self.is_trained = False
    
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer features for ML model"""
        logger.info("Engineering features...")
        
        features = df.copy()
        
        # Time-based features
        if 'manufacture_date' in features.columns:
            features['manufacture_date'] = pd.to_datetime(features['manufacture_date'])
            features['month'] = features['manufacture_date'].dt.month
            features['quarter'] = features['manufacture_date'].dt.quarter
            features['day_of_week'] = features['manufacture_date'].dt.dayofweek
            features['is_weekend'] = features['day_of_week'].isin([5, 6]).astype(int)
        
        if 'expiry_date' in features.columns:
            features['expiry_date'] = pd.to_datetime(features['expiry_date'])
            features['shelf_life_days'] = (
                features['expiry_date'] - features['manufacture_date']
            ).dt.days
        
        # Product features
        if 'unit_price' in features.columns:
            features['price_category'] = pd.cut(
                features['unit_price'],
                bins=[0, 5, 20, 100, float('inf')],
                labels=[1, 2, 3, 4]  # Low, Medium, High, Premium
            ).astype(int)
        
        # Warehouse features (one-hot encoding)
        if 'warehouse_location' in features.columns:
            warehouse_dummies = pd.get_dummies(
                features['warehouse_location'], 
                prefix='warehouse'
            )
            features = pd.concat([features, warehouse_dummies], axis=1)
        
        # Historical demand (rolling average simulation)
        if 'quantity' in features.columns:
            features['demand_ma_7d'] = features.groupby('product_id')['quantity'].transform(
                lambda x: x.rolling(window=7, min_periods=1).mean()
            )
            features['demand_ma_30d'] = features.groupby('product_id')['quantity'].transform(
                lambda x: x.rolling(window=30, min_periods=1).mean()
            )
        
        # Status encoding
        if 'status' in features.columns:
            features['status_encoded'] = (features['status'] == 'active').astype(int)
        
        logger.info(f"Feature engineering complete. Shape: {features.shape}")
        return features
    
    def train(self, df: pd.DataFrame, target_column: str = 'quantity') -> dict:
        """Train the forecasting model"""
        logger.info("Training demand forecasting model...")
        
        # Prepare features
        features = self.prepare_features(df)
        
        # Select feature columns (exclude target and non-numeric)
        exclude_cols = [
            target_column, 'product_id', 'product_name', 'batch_number',
            'warehouse_location', 'expiry_date', 'manufacture_date', 
            'status', 'created_at', 'updated_at'
        ]
        
        self.feature_columns = [
            col for col in features.columns 
            if col not in exclude_cols and features[col].dtype in ['int64', 'float64']
        ]
        
        X = features[self.feature_columns]
        y = features[target_column]
        
        # Handle missing values
        X = X.fillna(0)
        
        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        logger.info(f"Training with {len(X_train)} samples...")
        self.model.fit(X_train, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        
        y_pred = self.model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X, y, cv=5, scoring='r2')
        
        metrics = {
            'train_r2': round(train_score, 4),
            'test_r2': round(test_score, 4),
            'mae': round(mae, 2),
            'rmse': round(rmse, 2),
            'cv_mean_r2': round(cv_scores.mean(), 4),
            'cv_std_r2': round(cv_scores.std(), 4),
            'feature_count': len(self.feature_columns),
            'training_samples': len(X_train)
        }
        
        logger.info(f"Training complete. Test R²: {test_score:.4f}, MAE: {mae:.2f}")
        
        self.is_trained = True
        self.save_model()
        
        return metrics
    
    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Predict demand for given data"""
        if not self.is_trained:
            logger.warning("Model not trained. Loading from file...")
            self.load_model()
        
        # Prepare features
        features = self.prepare_features(df)
        
        # Select feature columns
        X = features[self.feature_columns].fillna(0)
        
        # Predict
        predictions = self.model.predict(X)
        
        # Add predictions to dataframe
        result = df.copy()
        result['predicted_demand'] = predictions.astype(int)
        result['reorder_recommended'] = (result['predicted_demand'] > result['quantity']).astype(int)
        
        return result
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance"""
        if not self.is_trained:
            raise ValueError("Model must be trained first")
        
        importance_df = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return importance_df
    
    def save_model(self):
        """Save trained model"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'feature_columns': self.feature_columns,
            'trained_at': datetime.now().isoformat()
        }
        
        joblib.dump(model_data, self.model_path)
        logger.info(f"Model saved to {self.model_path}")
    
    def load_model(self):
        """Load trained model"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found at {self.model_path}")
        
        model_data = joblib.load(self.model_path)
        self.model = model_data['model']
        self.feature_columns = model_data['feature_columns']
        self.is_trained = True
        
        logger.info(f"Model loaded from {self.model_path}")


class ReorderPointCalculator:
    """Calculate optimal reorder points"""
    
    def __init__(self, safety_stock_days=7):
        self.safety_stock_days = safety_stock_days
    
    def calculate_reorder_points(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate reorder points for all products"""
        logger.info("Calculating reorder points...")
        
        result = df.copy()
        
        # Calculate average daily demand
        if 'quantity' in result.columns:
            result['avg_daily_demand'] = result.groupby('product_id')['quantity'].transform('mean') / 30
        
        # Lead time (assume 7 days)
        lead_time_days = 7
        
        # Safety stock
        result['safety_stock'] = result['avg_daily_demand'] * self.safety_stock_days
        
        # Reorder point = (Lead time × Average demand) + Safety stock
        result['reorder_point'] = (
            lead_time_days * result['avg_daily_demand'] + result['safety_stock']
        ).astype(int)
        
        # Reorder quantity (Economic Order Quantity - simplified)
        result['reorder_quantity'] = (result['avg_daily_demand'] * 30).astype(int)
        
        # Alert if current quantity below reorder point
        result['needs_reorder'] = (result['quantity'] < result['reorder_point']).astype(int)
        
        logger.info(f"Calculated reorder points for {len(result)} items")
        return result


if __name__ == "__main__":
    # Test the forecaster
    from src.etl.extractors import DataExtractor
    
    extractor = DataExtractor()
    df = extractor.extract_from_csv("data/sample/sample_supply_chain.csv")
    
    # Train model
    forecaster = DemandForecaster()
    metrics = forecaster.train(df)
    
    print("\n=== Training Metrics ===")
    for key, value in metrics.items():
        print(f"{key}: {value}")
    
    # Feature importance
    print("\n=== Feature Importance ===")
    importance = forecaster.get_feature_importance()
    print(importance.head(10))
    
    # Make predictions
    predictions = forecaster.predict(df)
    print("\n=== Predictions ===")
    print(predictions[['product_name', 'quantity', 'predicted_demand', 'reorder_recommended']].head())
    
    # Calculate reorder points
    calculator = ReorderPointCalculator()
    reorder_df = calculator.calculate_reorder_points(df)
    print("\n=== Reorder Points ===")
    print(reorder_df[['product_name', 'quantity', 'reorder_point', 'needs_reorder']].head())