from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from datetime import timedelta
import sys
import os
import pandas as pd
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.etl.loaders import DataLoader
from src.validation.data_quality import DataQualityChecker, GreatExpectationsValidator

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'data-quality',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email': ['dq-alerts@healthcare.com'],
    'email_on_failure': True,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}


def fetch_latest_data_task(**context):
    """Fetch latest data from database"""
    logger.info("Fetching latest data...")
    
    loader = DataLoader()
    response = loader.supabase.table('supply_chain_data') \
        .select("*") \
        .order('created_at', desc=True) \
        .limit(1000) \
        .execute()
    
    df = pd.DataFrame(response.data)
    context['task_instance'].xcom_push(key='data', value=df.to_json(orient='records'))
    
    logger.info(f"Fetched {len(df)} records")
    return len(df)


def run_quality_checks_task(**context):
    """Run comprehensive quality checks"""
    logger.info("Running quality checks...")
    
    data_json = context['task_instance'].xcom_pull(key='data', task_ids='fetch_latest_data')
    df = pd.read_json(data_json, orient='records')
    
    # Run basic checks
    checker = DataQualityChecker()
    basic_results = checker.validate_all(df)
    
    # Run Great Expectations checks
    ge_validator = GreatExpectationsValidator()
    ge_results = ge_validator.create_expectation_suite(df)
    
    results = {
        'basic_checks': basic_results,
        'great_expectations': ge_results,
        'overall_status': 'PASS' if basic_results['status'] == 'PASS' and ge_results['success'] else 'FAIL'
    }
    
    context['task_instance'].xcom_push(key='quality_results', value=results)
    
    if results['overall_status'] == 'FAIL':
        logger.error("Quality checks failed!")
        raise ValueError("Data quality below threshold")
    
    logger.info("Quality checks passed!")
    return results


def generate_quality_report_task(**context):
    """Generate quality report"""
    results = context['task_instance'].xcom_pull(key='quality_results', task_ids='run_quality_checks')
    
    report = f"""
    ====================================
    DATA QUALITY REPORT
    ====================================
    Date: {context['execution_date']}
    Status: {results['overall_status']}
    
    Basic Checks:
    - Total Checks: {results['basic_checks']['total_checks']}
    - Passed: {results['basic_checks']['passed']}
    - Failed: {results['basic_checks']['failed']}
    - Success Rate: {results['basic_checks']['success_rate']}%
    
    Great Expectations:
    - Success: {results['great_expectations']['success']}
    - Success Percent: {results['great_expectations']['statistics']['success_percent']:.2f}%
    
    ====================================
    """
    
    logger.info(report)
    return report


with DAG(
    'data_quality_monitoring',
    default_args=default_args,
    description='Monitor data quality metrics',
    schedule_interval='0 */6 * * *',  # Every 6 hours
    catchup=False,
    tags=['data-quality', 'monitoring'],
) as dag:
    
    fetch_latest_data = PythonOperator(
        task_id='fetch_latest_data',
        python_callable=fetch_latest_data_task,
        provide_context=True,
    )
    
    run_quality_checks = PythonOperator(
        task_id='run_quality_checks',
        python_callable=run_quality_checks_task,
        provide_context=True,
    )
    
    generate_quality_report = PythonOperator(
        task_id='generate_quality_report',
        python_callable=generate_quality_report_task,
        provide_context=True,
    )
    
    fetch_latest_data >> run_quality_checks >> generate_quality_report