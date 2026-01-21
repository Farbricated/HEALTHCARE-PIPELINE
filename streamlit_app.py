import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path
import time

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

# Enhanced CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.5rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .success-box {
        padding: 1.5rem;
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 5px solid #28a745;
        border-radius: 10px;
        margin: 1.5rem 0;
    }
    
    .warning-box {
        padding: 1.5rem;
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border-left: 5px solid #ffc107;
        border-radius: 10px;
        margin: 1.5rem 0;
    }
    
    .error-box {
        padding: 1.5rem;
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border-left: 5px solid #dc3545;
        border-radius: 10px;
        margin: 1.5rem 0;
    }
    
    .info-box {
        padding: 1.5rem;
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border-left: 5px solid #17a2b8;
        border-radius: 10px;
        margin: 1.5rem 0;
    }
    
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'ml_training' not in st.session_state:
    st.session_state.ml_training = False


@st.cache_data(ttl=300)
def load_data_from_db():
    """Load data from Supabase"""
    try:
        loader = DataLoader()
        response = loader.supabase.table('supply_chain_data').select("*").execute()
        df = pd.DataFrame(response.data)
        
        if len(df) == 0:
            return None
        
        # Convert dates
        for col in ['expiry_date', 'manufacture_date', 'created_at']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Add enrichment if missing
        if 'total_value' not in df.columns:
            df['total_value'] = df['quantity'] * df['unit_price']
        
        if 'days_until_expiry' not in df.columns and 'expiry_date' in df.columns:
            df['days_until_expiry'] = (df['expiry_date'] - pd.Timestamp.now()).dt.days
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None


def main():
    """Main application"""
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <div style="font-size: 4rem;">🏥</div>
            <h2 style="margin-top: 0.5rem;">Healthcare Supply Chain</h2>
        </div>
        """, unsafe_allow_html=True)
        
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
        
        try:
            metrics = SystemMetrics.get_system_health()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("CPU", f"{metrics['cpu_percent']:.0f}%")
            with col2:
                st.metric("Memory", f"{metrics['memory_percent']:.0f}%")
        except:
            st.info("Metrics unavailable")
    
    # Route to pages
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
    """Dashboard page"""
    st.markdown('<p class="main-header">🏠 Dashboard</p>', unsafe_allow_html=True)
    
    df = load_data_from_db()
    
    if df is None or len(df) == 0:
        st.warning("⚠️ No data available. Please load sample data first.")
        
        if st.button("📥 Load Sample Data", type="primary"):
            with st.spinner("Loading..."):
                try:
                    extractor = DataExtractor()
                    df_sample = extractor.extract_from_csv("data/sample/sample_supply_chain.csv")
                    
                    transformer = DataTransformer()
                    df_clean = transformer.clean_data(df_sample)
                    df_enriched = transformer.enrich_data(df_clean)
                    
                    loader = DataLoader()
                    rows = loader.load_to_database(df_enriched)
                    
                    st.success(f"✅ Loaded {rows} records!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        return
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Products", len(df['product_id'].unique()))
    with col2:
        st.metric("Total Inventory", f"{df['quantity'].sum():,}")
    with col3:
        st.metric("Total Value", f"${df['total_value'].sum():,.0f}")
    with col4:
        expiring = len(df[df['days_until_expiry'] < 30]) if 'days_until_expiry' in df.columns else 0
        st.metric("Expiring Soon", expiring)
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📦 Inventory by Warehouse")
        warehouse_data = df.groupby('warehouse_location')['quantity'].sum().reset_index()
        fig = px.bar(warehouse_data, x='warehouse_location', y='quantity', color='quantity')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("💰 Top Products by Value")
        top_products = df.nlargest(10, 'total_value')[['product_name', 'total_value']]
        fig = px.pie(top_products, values='total_value', names='product_name', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.subheader("📋 Recent Inventory")
    st.dataframe(df.head(10), use_container_width=True)


def show_etl_pipeline():
    """ETL Pipeline page"""
    st.markdown('<p class="main-header">📊 ETL Pipeline</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h3>🔄 Pipeline Stages</h3>
        <ol>
            <li><strong>Extract:</strong> Load data from CSV/JSON/Excel/API</li>
            <li><strong>Transform:</strong> Clean, validate, and enrich data</li>
            <li><strong>Load:</strong> Save to Supabase database</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("▶️ Run ETL Pipeline", use_container_width=True, type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Extract
            status_text.markdown("### 📥 Extracting...")
            progress_bar.progress(25)
            extractor = DataExtractor()
            df = extractor.extract_from_csv("data/sample/sample_supply_chain.csv")
            st.success(f"✅ Extracted {len(df)} records")
            
            # Transform
            status_text.markdown("### 🔄 Transforming...")
            progress_bar.progress(50)
            transformer = DataTransformer()
            df_clean = transformer.clean_data(df)
            df_enriched = transformer.enrich_data(df_clean)
            st.success(f"✅ Transformed {len(df_enriched)} records")
            
            # Load
            status_text.markdown("### 💾 Loading...")
            progress_bar.progress(75)
            loader = DataLoader()
            rows_loaded = loader.load_to_database(df_enriched)
            st.success(f"✅ Loaded {rows_loaded} records")
            
            progress_bar.progress(100)
            status_text.markdown("### ✨ Complete!")
            st.balloons()
            
            st.cache_data.clear()
            
        except Exception as e:
            st.error(f"❌ Failed: {e}")
    
    # Pipeline logs
    st.markdown("---")
    st.subheader("📜 Recent Runs")
    try:
        loader = DataLoader()
        response = loader.supabase.table('pipeline_logs').select("*").order('created_at', desc=True).limit(5).execute()
        
        if response.data:
            st.dataframe(pd.DataFrame(response.data), use_container_width=True)
        else:
            st.info("No logs yet")
    except:
        st.info("Logs unavailable")


def show_data_quality():
    """Data Quality page"""
    st.markdown('<p class="main-header">✅ Data Quality</p>', unsafe_allow_html=True)
    
    df = load_data_from_db()
    
    if df is None or len(df) == 0:
        st.warning("No data available")
        return
    
    if st.button("🔍 Run Quality Checks", use_container_width=True, type="primary"):
        with st.spinner("Checking..."):
            checker = DataQualityChecker()
            results = checker.validate_all(df)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Checks", results['total_checks'])
            with col2:
                st.metric("Passed", results['passed'])
            with col3:
                st.metric("Failed", results['failed'])
            
            success_rate = results['success_rate']
            
            if success_rate >= 95:
                st.markdown(f'<div class="success-box">✅ Excellent! Quality Score: {success_rate}%</div>', 
                           unsafe_allow_html=True)
            elif success_rate >= 80:
                st.markdown(f'<div class="warning-box">⚠️ Good. Quality Score: {success_rate}%</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="error-box">❌ Needs improvement. Score: {success_rate}%</div>', 
                           unsafe_allow_html=True)
            
            st.subheader("📋 Details")
            for detail in results['details']:
                emoji = "✅" if detail['status'] == 'PASS' else "❌"
                st.write(f"{emoji} {detail['message']}")


def show_ml_predictions():
    """ML Predictions page - FIXED VERSION"""
    st.markdown('<p class="main-header">🤖 ML Predictions</p>', unsafe_allow_html=True)
    
    df = load_data_from_db()
    
    if df is None or len(df) == 0:
        st.warning("No data available")
        return
    
    tab1, tab2, tab3 = st.tabs(["📈 Demand Forecasting", "🚨 Anomaly Detection", "📊 Reorder Points"])
    
    with tab1:
        st.subheader("Demand Forecasting")
        st.info("💡 Uses Random Forest to predict future demand")
        
        if len(df) < 5:
            st.warning("Need at least 5 records for predictions")
            return
        
        if st.button("🎯 Train & Predict", key="train_model", type="primary"):
            with st.spinner("Training model..."):
                try:
                    # Prepare data
                    df_prep = df.copy()
                    
                    # Ensure dates
                    for col in ['expiry_date', 'manufacture_date']:
                        if col in df_prep.columns:
                            df_prep[col] = pd.to_datetime(df_prep[col], errors='coerce')
                    
                    # Add enrichment
                    if 'total_value' not in df_prep.columns:
                        df_prep['total_value'] = df_prep['quantity'] * df_prep['unit_price']
                    
                    if 'days_until_expiry' not in df_prep.columns and 'expiry_date' in df_prep.columns:
                        df_prep['days_until_expiry'] = (df_prep['expiry_date'] - pd.Timestamp.now()).dt.days
                    
                    # Train
                    forecaster = DemandForecaster()
                    metrics = forecaster.train(df_prep)
                    
                    st.success("✅ Model trained!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("R² Score", f"{metrics['test_r2']:.4f}")
                    with col2:
                        st.metric("MAE", f"{metrics['mae']:.2f}")
                    with col3:
                        st.metric("RMSE", f"{metrics['rmse']:.2f}")
                    
                    # Predictions
                    predictions = forecaster.predict(df_prep)
                    
                    st.markdown("---")
                    st.subheader("📊 Predictions")
                    
                    pred_display = predictions[['product_name', 'quantity', 'predicted_demand']].copy()
                    pred_display['needs_reorder'] = pred_display['predicted_demand'] > pred_display['quantity']
                    
                    st.dataframe(pred_display.head(10), use_container_width=True)
                    
                    # Chart
                    top_10 = pred_display.head(10)
                    fig = go.Figure()
                    fig.add_trace(go.Bar(name='Current', x=top_10['product_name'], y=top_10['quantity']))
                    fig.add_trace(go.Bar(name='Predicted', x=top_10['product_name'], y=top_10['predicted_demand']))
                    fig.update_layout(barmode='group', title='Current vs Predicted Demand')
                    st.plotly_chart(fig, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    with st.expander("Show error details"):
                        st.exception(e)
    
    with tab2:
        st.subheader("Anomaly Detection")
        st.info("💡 Detects unusual patterns using Isolation Forest")
        
        if st.button("🔍 Detect Anomalies", key="detect_anomalies", type="primary"):
            with st.spinner("Detecting..."):
                try:
                    df_prep = df.copy()
                    
                    if 'total_value' not in df_prep.columns:
                        df_prep['total_value'] = df_prep['quantity'] * df_prep['unit_price']
                    
                    if 'days_until_expiry' not in df_prep.columns and 'expiry_date' in df_prep.columns:
                        df_prep['expiry_date'] = pd.to_datetime(df_prep['expiry_date'], errors='coerce')
                        df_prep['days_until_expiry'] = (df_prep['expiry_date'] - pd.Timestamp.now()).dt.days
                    
                    detector = AnomalyDetector(contamination=0.1)
                    result_df = detector.detect_anomalies(df_prep)
                    
                    anomalies = result_df[result_df['is_anomaly'] == 1]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Records", len(result_df))
                    with col2:
                        st.metric("Anomalies", len(anomalies))
                    
                    if len(anomalies) > 0:
                        st.subheader("🚨 Anomalous Records")
                        st.dataframe(
                            anomalies[['product_name', 'quantity', 'unit_price', 'anomaly_score']].head(10),
                            use_container_width=True
                        )
                        
                        fig = px.scatter(
                            anomalies.head(20),
                            x='quantity',
                            y='unit_price',
                            color='anomaly_score',
                            hover_data=['product_name']
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.success("✅ No anomalies detected!")
                    
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    with st.expander("Show error details"):
                        st.exception(e)
    
    with tab3:
        st.subheader("Reorder Point Calculation")
        st.info("💡 Calculates optimal reorder points")
        
        if st.button("📈 Calculate", key="calc_reorder", type="primary"):
            with st.spinner("Calculating..."):
                try:
                    calculator = ReorderPointCalculator(safety_stock_days=7)
                    reorder_df = calculator.calculate_reorder_points(df)
                    
                    needs_reorder = reorder_df[reorder_df['needs_reorder'] == 1]
                    
                    st.metric("Products Needing Reorder", len(needs_reorder))
                    
                    if len(needs_reorder) > 0:
                        st.subheader("⚠️ Below Reorder Point")
                        st.dataframe(
                            needs_reorder[['product_name', 'quantity', 'reorder_point', 'reorder_quantity']],
                            use_container_width=True
                        )
                    else:
                        st.success("✅ All products above reorder points!")
                    
                except Exception as e:
                    st.error(f"❌ Error: {e}")


def show_analytics():
    """Analytics page"""
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
    
    # Warehouse stats
    st.subheader("🏪 Warehouse Performance")
    
    warehouse_stats = df.groupby('warehouse_location').agg({
        'quantity': 'sum',
        'total_value': 'sum',
        'product_id': 'nunique'
    }).reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.dataframe(warehouse_stats, use_container_width=True)
    
    with col2:
        fig = px.bar(warehouse_stats, x='warehouse_location', y='quantity')
        st.plotly_chart(fig, use_container_width=True)


def show_alerts():
    """Alerts page"""
    st.markdown('<p class="main-header">🔔 Alerts</p>', unsafe_allow_html=True)
    
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
                st.markdown(f'<div class="info-box">ℹ️ INFO: {message}</div>', 
                           unsafe_allow_html=True)
    else:
        st.success("✅ No alerts - All systems normal")


if __name__ == "__main__":
    main()