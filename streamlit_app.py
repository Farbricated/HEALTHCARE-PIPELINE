import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.etl.extractors import DataExtractor
from src.etl.transformers import DataTransformer
from src.etl.loaders import DataLoader
from src.validation.data_quality import DataQualityChecker, GreatExpectationsValidator
from src.ml.demand_forecast import DemandForecaster, ReorderPointCalculator
from src.ml.anomaly_detection import AnomalyDetector
from src.monitoring.metrics import SystemMetrics
from src.monitoring.alerts import AlertManager

# Page config
st.set_page_config(
    page_title="Healthcare Supply Chain Analytics",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'df' not in st.session_state:
    st.session_state.df = None


@st.cache_data
def load_data_from_db():
    """Load data from Supabase"""
    try:
        loader = DataLoader()
        response = loader.supabase.table('supply_chain_data').select("*").execute()
        df = pd.DataFrame(response.data)
        
        # Convert dates
        for col in ['expiry_date', 'manufacture_date', 'created_at']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


def main():
    """Main application"""
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/clouds/100/000000/hospital-3.png", width=100)
        st.title("🏥 Healthcare Supply Chain")
        st.markdown("---")
        
        page = st.radio(
            "Navigation",
            [
                "🏠 Dashboard",
                "📊 ETL Pipeline", 
                "✅ Data Quality",
                "🤖 ML Predictions",
                "📈 Analytics",
                "🔔 Alerts"
            ]
        )
        
        st.markdown("---")
        st.markdown("### 📊 System Status")
        
        # System metrics
        try:
            metrics = SystemMetrics.get_system_health()
            st.metric("CPU Usage", f"{metrics['cpu_percent']:.1f}%")
            st.metric("Memory", f"{metrics['memory_percent']:.1f}%")
            st.metric("Status", metrics['status'].upper())
        except:
            st.info("System metrics unavailable")
    
    # Main content
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "📊 ETL Pipeline":
        show_etl_pipeline()
    elif page == "✅ Data Quality":
        show_data_quality()
    elif page == "🤖 ML Predictions":
        show_ml_predictions()
    elif page == "📈 Analytics":
        show_analytics()
    elif page == "🔔 Alerts":
        show_alerts()


def show_dashboard():
    """Show main dashboard"""
    st.markdown('<p class="main-header">🏥 Healthcare Supply Chain Dashboard</p>', 
                unsafe_allow_html=True)
    
    # Load data
    df = load_data_from_db()
    
    if df is None or len(df) == 0:
        st.warning("⚠️ No data available. Please run the ETL pipeline first.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Load Sample Data", use_container_width=True):
                with st.spinner("Loading sample data..."):
                    try:
                        extractor = DataExtractor()
                        df_sample = extractor.extract_from_csv("data/sample/sample_supply_chain.csv")
                        
                        transformer = DataTransformer()
                        df_clean = transformer.clean_data(df_sample)
                        df_enriched = transformer.enrich_data(df_clean)
                        
                        loader = DataLoader()
                        rows = loader.load_to_database(df_enriched)
                        
                        st.success(f"✅ Loaded {rows} records successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        return
    
    # Key metrics
    st.subheader("📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Products", len(df['product_id'].unique()))
    with col2:
        total_qty = df['quantity'].sum()
        st.metric("Total Inventory", f"{total_qty:,}")
    with col3:
        if 'total_value' in df.columns:
            total_value = df['total_value'].sum()
        else:
            total_value = (df['quantity'] * df['unit_price']).sum()
        st.metric("Total Value", f"${total_value:,.2f}")
    with col4:
        if 'days_until_expiry' in df.columns:
            expiring_soon = len(df[df['days_until_expiry'] < 30])
        else:
            expiring_soon = 0
        st.metric("Expiring Soon (30d)", expiring_soon, 
                 delta=None if expiring_soon == 0 else "⚠️")
    
    # Charts
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📦 Inventory by Warehouse")
        warehouse_data = df.groupby('warehouse_location')['quantity'].sum().reset_index()
        fig = px.bar(warehouse_data, x='warehouse_location', y='quantity',
                    color='quantity', color_continuous_scale='Blues')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("💰 Value Distribution")
        if 'total_value' not in df.columns:
            df['total_value'] = df['quantity'] * df['unit_price']
        
        top_products = df.nlargest(10, 'total_value')[['product_name', 'total_value']]
        fig = px.pie(top_products, values='total_value', names='product_name')
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent data
    st.markdown("---")
    st.subheader("📋 Recent Inventory")
    st.dataframe(df.head(10), use_container_width=True)


def show_etl_pipeline():
    """Show ETL pipeline execution"""
    st.markdown('<p class="main-header">📊 ETL Pipeline</p>', unsafe_allow_html=True)
    
    st.markdown("""
    ### Pipeline Stages
    1. **Extract** - Load data from CSV/JSON/Excel/API
    2. **Transform** - Clean, validate, and enrich data
    3. **Load** - Save to Supabase database
    """)
    
    if st.button("▶️ Run ETL Pipeline", use_container_width=True):
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Extract
            status_text.text("📥 Extracting data...")
            progress_bar.progress(25)
            extractor = DataExtractor()
            df = extractor.extract_from_csv("data/sample/sample_supply_chain.csv")
            st.success(f"✅ Extracted {len(df)} records")
            
            # Transform
            status_text.text("🔄 Transforming data...")
            progress_bar.progress(50)
            transformer = DataTransformer()
            df_clean = transformer.clean_data(df)
            df_enriched = transformer.enrich_data(df_clean)
            st.success(f"✅ Transformed {len(df_enriched)} records")
            
            # Load
            status_text.text("💾 Loading to database...")
            progress_bar.progress(75)
            loader = DataLoader()
            rows_loaded = loader.load_to_database(df_enriched)
            st.success(f"✅ Loaded {rows_loaded} records")
            
            progress_bar.progress(100)
            status_text.text("✨ Pipeline completed successfully!")
            
            st.balloons()
            
        except Exception as e:
            st.error(f"❌ Pipeline failed: {e}")
    
    # Show pipeline logs
    st.markdown("---")
    st.subheader("📜 Recent Pipeline Runs")
    try:
        loader = DataLoader()
        response = loader.supabase.table('pipeline_logs') \
            .select("*").order('created_at', desc=True).limit(10).execute()
        
        if response.data:
            logs_df = pd.DataFrame(response.data)
            st.dataframe(logs_df, use_container_width=True)
        else:
            st.info("No pipeline logs yet")
    except:
        st.info("Pipeline logs table not created yet")


def show_data_quality():
    """Show data quality checks"""
    st.markdown('<p class="main-header">✅ Data Quality</p>', unsafe_allow_html=True)
    
    df = load_data_from_db()
    
    if df is None or len(df) == 0:
        st.warning("No data available")
        return
    
    if st.button("🔍 Run Quality Checks", use_container_width=True):
        with st.spinner("Running quality checks..."):
            # Basic checks
            checker = DataQualityChecker()
            results = checker.validate_all(df)
            
            # Display results
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Checks", results['total_checks'])
            with col2:
                st.metric("Passed", results['passed'], delta="✅")
            with col3:
                st.metric("Failed", results['failed'], 
                         delta="❌" if results['failed'] > 0 else "✅")
            
            # Success rate
            success_rate = results['success_rate']
            if success_rate >= 95:
                st.markdown(f'<div class="success-box">✅ Quality Score: {success_rate}% - EXCELLENT</div>', 
                           unsafe_allow_html=True)
            elif success_rate >= 80:
                st.markdown(f'<div class="warning-box">⚠️ Quality Score: {success_rate}% - GOOD</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="error-box">❌ Quality Score: {success_rate}% - NEEDS IMPROVEMENT</div>', 
                           unsafe_allow_html=True)
            
            # Detailed results
            st.subheader("📋 Detailed Results")
            for detail in results['details']:
                status_emoji = "✅" if detail['status'] == 'PASS' else "❌"
                st.write(f"{status_emoji} {detail['message']}")


def show_ml_predictions():
    """Show ML predictions"""
    st.markdown('<p class="main-header">🤖 ML Predictions</p>', unsafe_allow_html=True)
    
    df = load_data_from_db()
    
    if df is None or len(df) == 0:
        st.warning("No data available")
        return
    
    tab1, tab2 = st.tabs(["📈 Demand Forecasting", "🚨 Anomaly Detection"])
    
    with tab1:
        st.subheader("Demand Forecasting")
        
        if st.button("🎯 Train & Predict", use_container_width=True):
            with st.spinner("Training model..."):
                try:
                    forecaster = DemandForecaster()
                    metrics = forecaster.train(df)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("R² Score", f"{metrics['test_r2']:.4f}")
                    with col2:
                        st.metric("MAE", f"{metrics['mae']:.2f}")
                    with col3:
                        st.metric("RMSE", f"{metrics['rmse']:.2f}")
                    
                    # Predictions
                    predictions = forecaster.predict(df)
                    st.subheader("📊 Predictions")
                    st.dataframe(
                        predictions[['product_name', 'quantity', 'predicted_demand', 'reorder_recommended']].head(10),
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with tab2:
        st.subheader("Anomaly Detection")
        
        if st.button("🔍 Detect Anomalies", use_container_width=True):
            with st.spinner("Detecting anomalies..."):
                try:
                    detector = AnomalyDetector()
                    result_df = detector.detect_anomalies(df)
                    
                    anomalies = result_df[result_df['is_anomaly'] == 1]
                    
                    st.metric("Anomalies Found", len(anomalies))
                    
                    if len(anomalies) > 0:
                        st.subheader("🚨 Anomalous Records")
                        st.dataframe(anomalies[['product_name', 'quantity', 'unit_price', 'anomaly_score']], 
                                   use_container_width=True)
                    else:
                        st.success("✅ No anomalies detected")
                    
                except Exception as e:
                    st.error(f"Error: {e}")


def show_analytics():
    """Show analytics"""
    st.markdown('<p class="main-header">📈 Analytics</p>', unsafe_allow_html=True)
    
    df = load_data_from_db()
    
    if df is None or len(df) == 0:
        st.warning("No data available")
        return
    
    # Time series
    if 'created_at' in df.columns:
        st.subheader("📅 Inventory Over Time")
        df['date'] = pd.to_datetime(df['created_at']).dt.date
        time_series = df.groupby('date')['quantity'].sum().reset_index()
        
        fig = px.line(time_series, x='date', y='quantity', markers=True)
        st.plotly_chart(fig, use_container_width=True)
    
    # Warehouse comparison
    st.subheader("🏪 Warehouse Performance")
    col1, col2 = st.columns(2)
    
    with col1:
        warehouse_stats = df.groupby('warehouse_location').agg({
            'quantity': 'sum',
            'product_id': 'count'
        }).reset_index()
        warehouse_stats.columns = ['Warehouse', 'Total Quantity', 'Product Count']
        st.dataframe(warehouse_stats, use_container_width=True)
    
    with col2:
        fig = px.bar(warehouse_stats, x='Warehouse', y='Total Quantity', color='Product Count')
        st.plotly_chart(fig, use_container_width=True)


def show_alerts():
    """Show alerts"""
    st.markdown('<p class="main-header">🔔 Alerts & Monitoring</p>', unsafe_allow_html=True)
    
    df = load_data_from_db()
    
    if df is None or len(df) == 0:
        st.warning("No data available")
        return
    
    alert_manager = AlertManager()
    alerts = alert_manager.check_inventory_alerts(df)
    
    if alerts:
        for alert in alerts:
            severity = alert.get('severity', 'INFO')
            message = alert['message']
            
            if severity == 'CRITICAL':
                st.markdown(f'<div class="error-box">🚨 CRITICAL: {message}</div>', 
                           unsafe_allow_html=True)
            elif severity == 'WARNING':
                st.markdown(f'<div class="warning-box">⚠️ WARNING: {message}</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="success-box">ℹ️ INFO: {message}</div>', 
                           unsafe_allow_html=True)
    else:
        st.success("✅ No alerts - All systems normal")


if __name__ == "__main__":
    main()