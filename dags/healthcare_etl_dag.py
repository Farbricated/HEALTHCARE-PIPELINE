from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta
import sys
import os
import pandas as pd
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.etl.extractors import DataExtractor
from src.etl.transformers import DataTransformer
from src.etl.loaders import DataLoader
from src.validation.data_quality import DataQualityChecker

logger = logging.getLogger(__name__)

# Default arguments
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email': ['alerts@healthcare.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}

def extract_data_task(**context):
    """Extract data from source"""
    logger.info("Starting data extraction...")
    
    extractor = DataExtractor()
    
    # Extract from multiple sources
    df_csv = extractor.extract_from_csv("data/sample/sample_supply_chain.csv")
    
    # Store in XCom for next task
    context['task_instance'].xcom_push(key='raw_data', value=df_csv.to_json(orient='records'))
    
    logger.info(f"Extracted {len(df_csv)} records")
    return len(df_csv)


def validate_raw_data_task(**context):
    """Validate extracted data"""
    logger.info("Validating raw data...")
    
    # Get data from previous task
    raw_data_json = context['task_instance'].xcom_pull(key='raw_data', task_ids='extract_data')
    df = pd.read_json(raw_data_json, orient='records')
    
    # Run validation
    checker = DataQualityChecker()
    validation_result = checker.validate_all(df)
    
    # Store validation results
    context['task_instance'].xcom_push(key='validation_result', value=validation_result)
    
    if validation_result['status'] == 'FAIL':
        raise ValueError(f"Data quality check failed: {validation_result['success_rate']}% success")
    
    logger.info(f"Validation passed: {validation_result['success_rate']}%")
    return validation_result['success_rate']


def transform_data_task(**context):
    """Transform and clean data"""
    logger.info("Transforming data...")
    
    # Get raw data
    raw_data_json = context['task_instance'].xcom_pull(key='raw_data', task_ids='extract_data')
    df = pd.read_json(raw_data_json, orient='records')
    
    # Transform
    transformer = DataTransformer()
    df_clean = transformer.clean_data(df)
    df_enriched = transformer.enrich_data(df_clean)
    
    # Store transformed data
    context['task_instance'].xcom_push(
        key='transformed_data', 
        value=df_enriched.to_json(orient='records')
    )
    
    logger.info(f"Transformed {len(df_enriched)} records")
    return len(df_enriched)


def validate_transformed_data_task(**context):
    """Validate transformed data"""
    logger.info("Validating transformed data...")
    
    transformed_data_json = context['task_instance'].xcom_pull(
        key='transformed_data', 
        task_ids='transform_data'
    )
    df = pd.read_json(transformed_data_json, orient='records')
    
    # Check for enriched columns
    required_columns = ['days_until_expiry', 'total_value', 'stock_level']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"Missing enriched columns: {missing_columns}")
    
    logger.info("Transformed data validation passed")
    return True


def load_data_task(**context):
    """Load data to database"""
    logger.info("Loading data to database...")
    
    # Get transformed data
    transformed_data_json = context['task_instance'].xcom_pull(
        key='transformed_data', 
        task_ids='transform_data'
    )
    df = pd.read_json(transformed_data_json, orient='records')
    
    # Load to database
    loader = DataLoader()
    rows_loaded = loader.load_to_database(df, table_name='supply_chain_data')
    
    logger.info(f"Loaded {rows_loaded} records to database")
    return rows_loaded


def verify_load_task(**context):
    """Verify data was loaded correctly"""
    logger.info("Verifying loaded data...")
    
    loader = DataLoader()
    total_records = loader.verify_data('supply_chain_data')
    
    expected_count = context['task_instance'].xcom_pull(
        key='return_value', 
        task_ids='load_data'
    )
    
    logger.info(f"Verification complete: {total_records} total records in database")
    return total_records


def log_pipeline_execution_task(**context):
    """Log pipeline execution metrics"""
    logger.info("Logging pipeline execution...")
    
    # Get metrics from previous tasks
    extracted_count = context['task_instance'].xcom_pull(
        key='return_value', 
        task_ids='extract_data'
    )
    loaded_count = context['task_instance'].xcom_pull(
        key='return_value', 
        task_ids='load_data'
    )
    validation_score = context['task_instance'].xcom_pull(
        key='return_value', 
        task_ids='validate_raw_data'
    )
    
    # Calculate execution time
    execution_date = context['execution_date']
    current_time = datetime.now()
    execution_time = (current_time - execution_date).total_seconds()
    
    # Log to database
    loader = DataLoader()
    loader.log_pipeline_execution(
        pipeline_name='healthcare_etl_dag',
        status='success',
        records_processed=loaded_count,
        errors_count=0,
        execution_time=execution_time
    )
    
    logger.info("Pipeline execution logged successfully")
    return {
        'extracted': extracted_count,
        'loaded': loaded_count,
        'validation_score': validation_score,
        'execution_time': execution_time
    }


def send_success_notification_task(**context):
    """Send success notification"""
    metrics = context['task_instance'].xcom_pull(
        key='return_value', 
        task_ids='log_pipeline_execution'
    )
    
    logger.info(f"✅ Pipeline Success! Metrics: {metrics}")
    # Here you could send email, Slack, etc.
    return "Notification sent"


# Define the DAG
with DAG(
    'healthcare_supply_chain_etl',
    default_args=default_args,
    description='Healthcare Supply Chain ETL Pipeline with Data Quality Checks',
    schedule_interval='0 2 * * *',  # Run daily at 2 AM
    catchup=False,
    max_active_runs=1,
    tags=['healthcare', 'supply-chain', 'etl', 'production'],
) as dag:
    
    # Task 1: Extract data
    extract_data = PythonOperator(
        task_id='extract_data',
        python_callable=extract_data_task,
        provide_context=True,
    )
    
    # Task 2: Validate raw data
    validate_raw_data = PythonOperator(
        task_id='validate_raw_data',
        python_callable=validate_raw_data_task,
        provide_context=True,
    )
    
    # Task 3: Transform data
    transform_data = PythonOperator(
        task_id='transform_data',
        python_callable=transform_data_task,
        provide_context=True,
    )
    
    # Task 4: Validate transformed data
    validate_transformed_data = PythonOperator(
        task_id='validate_transformed_data',
        python_callable=validate_transformed_data_task,
        provide_context=True,
    )
    
    # Task 5: Load data
    load_data = PythonOperator(
        task_id='load_data',
        python_callable=load_data_task,
        provide_context=True,
    )
    
    # Task 6: Verify load
    verify_load = PythonOperator(
        task_id='verify_load',
        python_callable=verify_load_task,
        provide_context=True,
    )
    
    # Task 7: Log execution
    log_pipeline_execution = PythonOperator(
        task_id='log_pipeline_execution',
        python_callable=log_pipeline_execution_task,
        provide_context=True,
    )
    
    # Task 8: Send notification
    send_success_notification = PythonOperator(
        task_id='send_success_notification',
        python_callable=send_success_notification_task,
        provide_context=True,
    )
    
    # Define task dependencies
    extract_data >> validate_raw_data >> transform_data >> validate_transformed_data
    validate_transformed_data >> load_data >> verify_load >> log_pipeline_execution
    log_pipeline_execution >> send_success_notification


# Error handling DAG
def handle_failure(context):
    """Handle DAG failure"""
    logger.error(f"DAG failed: {context['exception']}")
    
    # Log failure to database
    try:
        loader = DataLoader()
        loader.log_pipeline_execution(
            pipeline_name='healthcare_etl_dag',
            status='failed',
            records_processed=0,
            errors_count=1,
            execution_time=0,
            error_message=str(context['exception'])
        )
    except Exception as e:
        logger.error(f"Failed to log error: {e}")