import pandas as pd
import logging
from typing import Dict, List, Any
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataQualityChecker:
    """Comprehensive data quality validation"""
    
    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.results = []
    
    def validate_all(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Run all validation checks"""
        logger.info("🔍 Starting data quality validation...")
        
        self.results = []
        self.checks_passed = 0
        self.checks_failed = 0
        
        # Run all checks
        self._check_completeness(df)
        self._check_uniqueness(df)
        self._check_validity(df)
        self._check_consistency(df)
        self._check_accuracy(df)
        
        success_rate = (self.checks_passed / (self.checks_passed + self.checks_failed)) * 100
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_checks': self.checks_passed + self.checks_failed,
            'passed': self.checks_passed,
            'failed': self.checks_failed,
            'success_rate': round(success_rate, 2),
            'status': 'PASS' if success_rate >= 95 else 'FAIL',
            'details': self.results
        }
        
        logger.info(f"✅ Validation complete: {success_rate:.2f}% success rate")
        return summary
    
    def _check_completeness(self, df: pd.DataFrame):
        """Check for missing values"""
        logger.info("Checking completeness...")
        
        critical_columns = ['product_id', 'product_name', 'quantity', 'batch_number']
        
        for col in critical_columns:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                null_pct = (null_count / len(df)) * 100
                
                if null_count == 0:
                    self._log_check('PASS', f"Completeness: {col} has no null values")
                else:
                    self._log_check('FAIL', f"Completeness: {col} has {null_count} nulls ({null_pct:.2f}%)")
    
    def _check_uniqueness(self, df: pd.DataFrame):
        """Check for duplicates"""
        logger.info("Checking uniqueness...")
        
        # Check batch numbers
        if 'batch_number' in df.columns:
            duplicates = df['batch_number'].duplicated().sum()
            if duplicates == 0:
                self._log_check('PASS', f"Uniqueness: No duplicate batch numbers")
            else:
                self._log_check('FAIL', f"Uniqueness: {duplicates} duplicate batch numbers found")
        
        # Check product_id + batch_number combination
        if 'product_id' in df.columns and 'batch_number' in df.columns:
            duplicates = df.duplicated(subset=['product_id', 'batch_number']).sum()
            if duplicates == 0:
                self._log_check('PASS', "Uniqueness: No duplicate product-batch combinations")
            else:
                self._log_check('FAIL', f"Uniqueness: {duplicates} duplicate combinations")
    
    def _check_validity(self, df: pd.DataFrame):
        """Check data validity"""
        logger.info("Checking validity...")
        
        # Check quantity is positive
        if 'quantity' in df.columns:
            invalid = (df['quantity'] < 0).sum()
            if invalid == 0:
                self._log_check('PASS', "Validity: All quantities are non-negative")
            else:
                self._log_check('FAIL', f"Validity: {invalid} negative quantities found")
        
        # Check unit_price is positive
        if 'unit_price' in df.columns:
            invalid = (df['unit_price'] < 0).sum()
            if invalid == 0:
                self._log_check('PASS', "Validity: All unit prices are non-negative")
            else:
                self._log_check('FAIL', f"Validity: {invalid} negative prices found")
        
        # Check date formats
        if 'expiry_date' in df.columns:
            try:
                pd.to_datetime(df['expiry_date'], errors='raise')
                self._log_check('PASS', "Validity: All expiry dates are valid")
            except:
                self._log_check('FAIL', "Validity: Invalid expiry date format found")
    
    def _check_consistency(self, df: pd.DataFrame):
        """Check data consistency"""
        logger.info("Checking consistency...")
        
        # Check expiry > manufacture date
        if 'expiry_date' in df.columns and 'manufacture_date' in df.columns:
            df_temp = df.copy()
            df_temp['expiry_date'] = pd.to_datetime(df_temp['expiry_date'])
            df_temp['manufacture_date'] = pd.to_datetime(df_temp['manufacture_date'])
            
            invalid = (df_temp['expiry_date'] <= df_temp['manufacture_date']).sum()
            if invalid == 0:
                self._log_check('PASS', "Consistency: All expiry dates > manufacture dates")
            else:
                self._log_check('FAIL', f"Consistency: {invalid} records with expiry <= manufacture")
        
        # Check warehouse locations are standardized
        if 'warehouse_location' in df.columns:
            valid_warehouses = ['Warehouse A', 'Warehouse B', 'Warehouse C', 'Unknown']
            invalid = (~df['warehouse_location'].isin(valid_warehouses)).sum()
            if invalid == 0:
                self._log_check('PASS', "Consistency: All warehouse locations are valid")
            else:
                self._log_check('WARN', f"Consistency: {invalid} non-standard warehouse locations")
    
    def _check_accuracy(self, df: pd.DataFrame):
        """Check data accuracy"""
        logger.info("Checking accuracy...")
        
        # Check quantity ranges
        if 'quantity' in df.columns:
            suspicious = ((df['quantity'] == 0) | (df['quantity'] > 1000000)).sum()
            if suspicious == 0:
                self._log_check('PASS', "Accuracy: All quantities are in reasonable range")
            else:
                self._log_check('WARN', f"Accuracy: {suspicious} quantities are suspicious (0 or >1M)")
        
        # Check price ranges
        if 'unit_price' in df.columns:
            suspicious = ((df['unit_price'] == 0) | (df['unit_price'] > 100000)).sum()
            if suspicious == 0:
                self._log_check('PASS', "Accuracy: All prices are in reasonable range")
            else:
                self._log_check('WARN', f"Accuracy: {suspicious} prices are suspicious (0 or >100k)")
    
    def _log_check(self, status: str, message: str):
        """Log check result"""
        self.results.append({
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
        if status == 'PASS':
            self.checks_passed += 1
            logger.info(f"✓ {message}")
        elif status == 'FAIL':
            self.checks_failed += 1
            logger.error(f"✗ {message}")
        else:  # WARN
            self.checks_passed += 1  # Count as pass but flag
            logger.warning(f"⚠ {message}")


# Great Expectations alternative
class GreatExpectationsValidator:
    """Validation using Great Expectations framework"""
    
    def __init__(self):
        self.results = []
    
    def create_expectation_suite(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create and run expectation suite"""
        expectations = []
        
        # Completeness expectations
        expectations.append(self._expect_column_values_to_not_be_null(df, 'product_id'))
        expectations.append(self._expect_column_values_to_not_be_null(df, 'quantity'))
        
        # Range expectations
        expectations.append(self._expect_column_values_to_be_between(df, 'quantity', 0, 1000000))
        expectations.append(self._expect_column_values_to_be_between(df, 'unit_price', 0, 100000))
        
        # Uniqueness expectations
        expectations.append(self._expect_column_values_to_be_unique(df, 'batch_number'))
        
        success_count = sum(1 for e in expectations if e['success'])
        
        return {
            'success': all(e['success'] for e in expectations),
            'statistics': {
                'evaluated_expectations': len(expectations),
                'successful_expectations': success_count,
                'unsuccessful_expectations': len(expectations) - success_count,
                'success_percent': (success_count / len(expectations)) * 100
            },
            'results': expectations
        }
    
    def _expect_column_values_to_not_be_null(self, df: pd.DataFrame, column: str) -> Dict:
        null_count = df[column].isnull().sum()
        return {
            'expectation_type': 'expect_column_values_to_not_be_null',
            'column': column,
            'success': null_count == 0,
            'result': {
                'element_count': len(df),
                'unexpected_count': null_count,
                'unexpected_percent': (null_count / len(df)) * 100
            }
        }
    
    def _expect_column_values_to_be_between(self, df: pd.DataFrame, column: str, 
                                           min_value: float, max_value: float) -> Dict:
        out_of_range = ((df[column] < min_value) | (df[column] > max_value)).sum()
        return {
            'expectation_type': 'expect_column_values_to_be_between',
            'column': column,
            'success': out_of_range == 0,
            'kwargs': {'min_value': min_value, 'max_value': max_value},
            'result': {
                'element_count': len(df),
                'unexpected_count': out_of_range
            }
        }
    
    def _expect_column_values_to_be_unique(self, df: pd.DataFrame, column: str) -> Dict:
        duplicate_count = df[column].duplicated().sum()
        return {
            'expectation_type': 'expect_column_values_to_be_unique',
            'column': column,
            'success': duplicate_count == 0,
            'result': {
                'element_count': len(df),
                'unexpected_count': duplicate_count
            }
        }