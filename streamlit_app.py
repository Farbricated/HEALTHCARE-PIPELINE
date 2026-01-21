import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path
import time
import numpy as np

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
    page_title="NEXUS • Medical Supply Intelligence",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 MEDICAL FUTURISM CSS - Cyberpunk meets Clinical Precision
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&family=Rajdhani:wght@300;400;600;700&display=swap');
    
    /* Global Dark Theme with Holographic Elements */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0a0e27 0%, #16213e 50%, #0a0e27 100%);
        position: relative;
        overflow: hidden;
    }
    
    [data-testid="stAppViewContainer"]::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
            radial-gradient(circle at 20% 50%, rgba(0, 255, 204, 0.03) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(0, 153, 255, 0.03) 0%, transparent 50%),
            radial-gradient(circle at 40% 20%, rgba(153, 0, 255, 0.02) 0%, transparent 50%);
        pointer-events: none;
        animation: hologram 20s ease-in-out infinite;
    }
    
    @keyframes hologram {
        0%, 100% { opacity: 1; transform: translateY(0px); }
        50% { opacity: 0.8; transform: translateY(-10px); }
    }
    
    /* Scanline Effect */
    [data-testid="stAppViewContainer"]::after {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: repeating-linear-gradient(
            0deg,
            rgba(0, 255, 204, 0.03) 0px,
            transparent 2px,
            transparent 4px,
            rgba(0, 255, 204, 0.03) 4px
        );
        pointer-events: none;
        animation: scan 8s linear infinite;
        opacity: 0.3;
    }
    
    @keyframes scan {
        0% { transform: translateY(0); }
        100% { transform: translateY(100%); }
    }
    
    /* Typography */
    html, body, [class*="css"] {
        font-family: 'Rajdhani', sans-serif;
        color: #e0e6ed;
    }
    
    h1, h2, h3, .main-header {
        font-family: 'Orbitron', monospace !important;
        font-weight: 900;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #00ffcc;
        text-shadow: 
            0 0 10px rgba(0, 255, 204, 0.5),
            0 0 20px rgba(0, 255, 204, 0.3),
            0 0 30px rgba(0, 255, 204, 0.1);
        animation: glow 3s ease-in-out infinite;
    }
    
    @keyframes glow {
        0%, 100% { text-shadow: 0 0 10px rgba(0, 255, 204, 0.5), 0 0 20px rgba(0, 255, 204, 0.3); }
        50% { text-shadow: 0 0 20px rgba(0, 255, 204, 0.8), 0 0 30px rgba(0, 255, 204, 0.5), 0 0 40px rgba(0, 255, 204, 0.3); }
    }
    
    .mono-text {
        font-family: 'Share Tech Mono', monospace;
        color: #00ffcc;
        letter-spacing: 1px;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1729 0%, #1a2332 100%);
        border-right: 2px solid rgba(0, 255, 204, 0.2);
        box-shadow: 5px 0 30px rgba(0, 255, 204, 0.1);
    }
    
    [data-testid="stSidebar"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, transparent, #00ffcc, transparent);
        animation: sidebar-glow 2s ease-in-out infinite;
    }
    
    @keyframes sidebar-glow {
        0%, 100% { opacity: 0.5; }
        50% { opacity: 1; }
    }
    
    /* Holographic Cards */
    .holo-card {
        background: rgba(15, 23, 42, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 255, 204, 0.2);
        border-radius: 15px;
        padding: 2rem;
        position: relative;
        overflow: hidden;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.4),
            inset 0 1px 0 rgba(255, 255, 255, 0.1),
            0 0 20px rgba(0, 255, 204, 0.1);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .holo-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(
            45deg,
            transparent 30%,
            rgba(0, 255, 204, 0.05) 50%,
            transparent 70%
        );
        animation: holo-shine 3s linear infinite;
    }
    
    @keyframes holo-shine {
        0% { transform: rotate(0deg) translate(-50%, -50%); }
        100% { transform: rotate(360deg) translate(-50%, -50%); }
    }
    
    .holo-card:hover {
        border-color: rgba(0, 255, 204, 0.5);
        box-shadow: 
            0 12px 40px rgba(0, 0, 0, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.2),
            0 0 30px rgba(0, 255, 204, 0.3);
        transform: translateY(-4px);
    }
    
    /* Metric Cards - Neon Style */
    [data-testid="stMetricValue"] {
        font-family: 'Orbitron', monospace !important;
        font-size: 2.5rem !important;
        font-weight: 900 !important;
        color: #00ffcc !important;
        text-shadow: 0 0 10px rgba(0, 255, 204, 0.8);
    }
    
    [data-testid="stMetricLabel"] {
        font-family: 'Rajdhani', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-size: 0.85rem !important;
        color: #8892b0 !important;
    }
    
    /* Buttons - Cyberpunk Style */
    .stButton>button {
        font-family: 'Orbitron', monospace;
        background: linear-gradient(135deg, rgba(0, 255, 204, 0.1) 0%, rgba(0, 153, 255, 0.1) 100%);
        border: 2px solid #00ffcc;
        color: #00ffcc;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        padding: 0.75rem 2rem;
        border-radius: 0;
        clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        box-shadow: 
            0 0 20px rgba(0, 255, 204, 0.2),
            inset 0 0 20px rgba(0, 255, 204, 0.05);
    }
    
    .stButton>button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(0, 255, 204, 0.3), transparent);
        transition: left 0.5s ease;
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, rgba(0, 255, 204, 0.2) 0%, rgba(0, 153, 255, 0.2) 100%);
        box-shadow: 
            0 0 30px rgba(0, 255, 204, 0.5),
            inset 0 0 30px rgba(0, 255, 204, 0.1);
        transform: translateY(-2px);
        border-color: #00ff99;
    }
    
    .stButton>button:hover::before {
        left: 100%;
    }
    
    .stButton>button:active {
        transform: translateY(0px);
    }
    
    /* Alert Boxes - Medical Emergency Style */
    .success-box {
        background: rgba(0, 255, 136, 0.05);
        border: 2px solid #00ff88;
        border-left: 6px solid #00ff88;
        border-radius: 0;
        padding: 1.5rem;
        margin: 1.5rem 0;
        position: relative;
        clip-path: polygon(0 0, calc(100% - 15px) 0, 100% 15px, 100% 100%, 15px 100%, 0 calc(100% - 15px));
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
        animation: pulse-success 2s ease-in-out infinite;
    }
    
    @keyframes pulse-success {
        0%, 100% { box-shadow: 0 0 20px rgba(0, 255, 136, 0.2); }
        50% { box-shadow: 0 0 30px rgba(0, 255, 136, 0.4); }
    }
    
    .warning-box {
        background: rgba(255, 191, 0, 0.05);
        border: 2px solid #ffbf00;
        border-left: 6px solid #ffbf00;
        border-radius: 0;
        padding: 1.5rem;
        margin: 1.5rem 0;
        clip-path: polygon(0 0, calc(100% - 15px) 0, 100% 15px, 100% 100%, 15px 100%, 0 calc(100% - 15px));
        box-shadow: 0 0 20px rgba(255, 191, 0, 0.2);
        animation: pulse-warning 2s ease-in-out infinite;
    }
    
    @keyframes pulse-warning {
        0%, 100% { box-shadow: 0 0 20px rgba(255, 191, 0, 0.2); }
        50% { box-shadow: 0 0 30px rgba(255, 191, 0, 0.4); }
    }
    
    .error-box {
        background: rgba(255, 51, 102, 0.05);
        border: 2px solid #ff3366;
        border-left: 6px solid #ff3366;
        border-radius: 0;
        padding: 1.5rem;
        margin: 1.5rem 0;
        clip-path: polygon(0 0, calc(100% - 15px) 0, 100% 15px, 100% 100%, 15px 100%, 0 calc(100% - 15px));
        box-shadow: 0 0 20px rgba(255, 51, 102, 0.2);
        animation: pulse-error 1s ease-in-out infinite;
    }
    
    @keyframes pulse-error {
        0%, 100% { box-shadow: 0 0 20px rgba(255, 51, 102, 0.2); }
        50% { box-shadow: 0 0 40px rgba(255, 51, 102, 0.5); }
    }
    
    .info-box {
        background: rgba(0, 153, 255, 0.05);
        border: 2px solid #0099ff;
        border-left: 6px solid #0099ff;
        border-radius: 0;
        padding: 1.5rem;
        margin: 1.5rem 0;
        clip-path: polygon(0 0, calc(100% - 15px) 0, 100% 15px, 100% 100%, 15px 100%, 0 calc(100% - 15px));
        box-shadow: 0 0 20px rgba(0, 153, 255, 0.2);
    }
    
    /* Data Tables - Terminal Style */
    [data-testid="stDataFrame"] {
        background: rgba(10, 14, 39, 0.6);
        border: 1px solid rgba(0, 255, 204, 0.3);
        border-radius: 8px;
        font-family: 'Share Tech Mono', monospace;
        backdrop-filter: blur(10px);
    }
    
    /* Progress Bars */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #00ffcc 0%, #0099ff 50%, #9933ff 100%);
        box-shadow: 0 0 10px rgba(0, 255, 204, 0.5);
    }
    
    /* Radio Buttons */
    [data-testid="stSidebar"] .stRadio > label {
        font-family: 'Rajdhani', sans-serif;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #8892b0;
        transition: all 0.3s ease;
    }
    
    [data-testid="stSidebar"] .stRadio > label:hover {
        color: #00ffcc;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(15, 23, 42, 0.5);
        border-radius: 8px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-family: 'Orbitron', monospace;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #8892b0;
        background: transparent;
        border: 1px solid rgba(0, 255, 204, 0.2);
        border-radius: 4px;
        padding: 0.75rem 1.5rem;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #00ffcc;
        border-color: rgba(0, 255, 204, 0.5);
        background: rgba(0, 255, 204, 0.05);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(0, 255, 204, 0.15) 0%, rgba(0, 153, 255, 0.15) 100%);
        color: #00ffcc !important;
        border-color: #00ffcc;
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.3);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        font-family: 'Rajdhani', sans-serif;
        font-weight: 600;
        background: rgba(0, 255, 204, 0.05);
        border: 1px solid rgba(0, 255, 204, 0.2);
        border-radius: 4px;
        color: #00ffcc;
    }
    
    /* Main Header with Animated Border */
    .main-header {
        font-size: 3rem;
        font-weight: 900;
        text-align: center;
        padding: 2rem;
        position: relative;
        margin-bottom: 2rem;
    }
    
    .main-header::before,
    .main-header::after {
        content: '';
        position: absolute;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00ffcc, transparent);
    }
    
    .main-header::before {
        top: 0;
        animation: border-flow 3s linear infinite;
    }
    
    .main-header::after {
        bottom: 0;
        animation: border-flow 3s linear infinite reverse;
    }
    
    @keyframes border-flow {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    /* Status Indicator */
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s ease-in-out infinite;
    }
    
    .status-online { background: #00ff88; box-shadow: 0 0 10px #00ff88; }
    .status-warning { background: #ffbf00; box-shadow: 0 0 10px #ffbf00; }
    .status-error { background: #ff3366; box-shadow: 0 0 10px #ff3366; }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(15, 23, 42, 0.5);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #00ffcc 0%, #0099ff 100%);
        border-radius: 5px;
        box-shadow: 0 0 10px rgba(0, 255, 204, 0.5);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #00ff99 0%, #00ccff 100%);
    }
    
    /* Loading Animation */
    @keyframes data-stream {
        0% { opacity: 0.3; transform: translateY(0); }
        50% { opacity: 1; transform: translateY(-10px); }
        100% { opacity: 0.3; transform: translateY(0); }
    }
    
    .loading-indicator {
        animation: data-stream 1.5s ease-in-out infinite;
    }
    
    /* Custom Metric Card */
    .metric-card-custom {
        background: rgba(15, 23, 42, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(0, 255, 204, 0.2);
        border-radius: 8px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    .metric-card-custom:hover {
        border-color: rgba(0, 255, 204, 0.5);
        box-shadow: 0 0 20px rgba(0, 255, 204, 0.2);
        transform: translateY(-2px);
    }
    
    .metric-value {
        font-family: 'Orbitron', monospace;
        font-size: 2.5rem;
        font-weight: 900;
        color: #00ffcc;
        text-shadow: 0 0 10px rgba(0, 255, 204, 0.5);
        margin: 0;
    }
    
    .metric-label {
        font-family: 'Rajdhani', sans-serif;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #8892b0;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'ml_training' not in st.session_state:
    st.session_state.ml_training = False
if 'system_status' not in st.session_state:
    st.session_state.system_status = 'online'


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
        st.error(f"⚠️ Data Link Error: {e}")
        return None


def create_custom_chart(df, chart_type='bar'):
    """Create custom Plotly charts with cyberpunk theme"""
    layout = dict(
        plot_bgcolor='rgba(10, 14, 39, 0.6)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        font=dict(family='Rajdhani', color='#e0e6ed'),
        title_font=dict(family='Orbitron', size=16, color='#00ffcc'),
        xaxis=dict(gridcolor='rgba(0, 255, 204, 0.1)', showgrid=True),
        yaxis=dict(gridcolor='rgba(0, 255, 204, 0.1)', showgrid=True),
        hovermode='x unified',
    )
    return layout


def main():
    """Main application with enhanced UI"""
    
    # Sidebar with futuristic header
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0 1rem 0;">
            <div style="font-family: 'Orbitron', monospace; font-size: 3rem; color: #00ffcc; 
                        text-shadow: 0 0 20px rgba(0, 255, 204, 0.8); margin-bottom: 0.5rem;">
                ⚕️
            </div>
            <div style="font-family: 'Orbitron', monospace; font-size: 1.5rem; font-weight: 900; 
                        color: #00ffcc; letter-spacing: 3px; text-shadow: 0 0 10px rgba(0, 255, 204, 0.5);">
                NEXUS
            </div>
            <div style="font-family: 'Rajdhani', sans-serif; font-size: 0.75rem; 
                        text-transform: uppercase; letter-spacing: 2px; color: #8892b0; margin-top: 0.5rem;">
                Medical Supply Intelligence
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation with icons
        page = st.radio(
            "◉ SYSTEM MODULES",
            [
                "◈ Command Center",
                "◈ Pipeline Control", 
                "◈ Quality Assurance",
                "◈ AI Analytics",
                "◈ Data Observatory",
                "◈ Alert System"
            ],
            label_visibility="visible"
        )
        
        st.markdown("---")
        
        # System status
        st.markdown("### ◉ SYSTEM STATUS")
        
        try:
            metrics = SystemMetrics.get_system_health()
            status_class = "status-online" if metrics['cpu_percent'] < 80 else "status-warning"
            
            st.markdown(f"""
            <div style="margin: 1rem 0;">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <span class="status-indicator {status_class}"></span>
                    <span class="mono-text" style="font-size: 0.9rem;">OPERATIONAL</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="metric-card-custom" style="padding: 1rem;">
                    <div style="font-size: 1.5rem; font-family: 'Orbitron'; color: #00ffcc;">
                        {metrics['cpu_percent']:.0f}%
                    </div>
                    <div style="font-size: 0.7rem; color: #8892b0; margin-top: 0.3rem;">CPU</div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="metric-card-custom" style="padding: 1rem;">
                    <div style="font-size: 1.5rem; font-family: 'Orbitron'; color: #00ffcc;">
                        {metrics['memory_percent']:.0f}%
                    </div>
                    <div style="font-size: 0.7rem; color: #8892b0; margin-top: 0.3rem;">MEMORY</div>
                </div>
                """, unsafe_allow_html=True)
        except:
            st.markdown("""
            <div style="margin: 1rem 0;">
                <div style="display: flex; align-items: center;">
                    <span class="status-indicator status-warning"></span>
                    <span class="mono-text" style="font-size: 0.9rem;">METRICS UNAVAILABLE</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; margin-top: 2rem; padding: 1rem; 
                    background: rgba(0, 255, 204, 0.05); border-radius: 8px;">
            <div class="mono-text" style="font-size: 0.8rem;">v2.0.NEXUS</div>
            <div style="font-size: 0.7rem; color: #8892b0; margin-top: 0.3rem;">
                BUILD 2026.01
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Route to pages
    if page == "◈ Command Center":
        show_dashboard()
    elif page == "◈ Pipeline Control":
        show_etl_pipeline()
    elif page == "◈ Quality Assurance":
        show_data_quality()
    elif page == "◈ AI Analytics":
        show_ml_predictions()
    elif page == "◈ Data Observatory":
        show_analytics()
    elif page == "◈ Alert System":
        show_alerts()


def show_dashboard():
    """Enhanced Dashboard with holographic cards"""
    st.markdown("""
    <div class="main-header">
        ◈ COMMAND CENTER
    </div>
    """, unsafe_allow_html=True)
    
    df = load_data_from_db()
    
    if df is None or len(df) == 0:
        st.markdown("""
        <div class="warning-box">
            <div style="font-family: 'Orbitron'; font-size: 1.2rem; margin-bottom: 0.5rem;">
                ⚠️ NO DATA DETECTED
            </div>
            <div style="font-family: 'Rajdhani'; color: #8892b0;">
                Initialize database with sample medical supply data
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("⚡ INITIALIZE DATABASE", use_container_width=True, type="primary"):
            with st.spinner("◉ Initializing..."):
                try:
                    extractor = DataExtractor()
                    df_sample = extractor.extract_from_csv("data/sample/sample_supply_chain.csv")
                    
                    transformer = DataTransformer()
                    df_clean = transformer.clean_data(df_sample)
                    df_enriched = transformer.enrich_data(df_clean)
                    
                    loader = DataLoader()
                    rows = loader.load_to_database(df_enriched)
                    
                    st.markdown(f"""
                    <div class="success-box">
                        <div style="font-family: 'Orbitron'; font-size: 1.2rem;">
                            ✓ DATABASE INITIALIZED
                        </div>
                        <div class="mono-text" style="margin-top: 0.5rem;">
                            {rows} RECORDS LOADED
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.markdown(f"""
                    <div class="error-box">
                        <div style="font-family: 'Orbitron'; font-size: 1.2rem;">
                            ✗ INITIALIZATION FAILED
                        </div>
                        <div class="mono-text" style="margin-top: 0.5rem; font-size: 0.85rem;">
                            {str(e)}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        return
    
    # Metrics Row with holographic cards
    col1, col2, col3, col4 = st.columns(4)
    
    metrics_data = [
        ("PRODUCTS", len(df['product_id'].unique()), "#00ffcc"),
        ("INVENTORY", f"{df['quantity'].sum():,}", "#0099ff"),
        ("TOTAL VALUE", f"${df['total_value'].sum():,.0f}", "#9933ff"),
        ("EXPIRING", len(df[df['days_until_expiry'] < 30]) if 'days_until_expiry' in df.columns else 0, "#ffbf00")
    ]
    
    for col, (label, value, color) in zip([col1, col2, col3, col4], metrics_data):
        with col:
            st.markdown(f"""
            <div class="holo-card" style="text-align: center;">
                <div style="font-size: 2.5rem; font-family: 'Orbitron'; font-weight: 900; 
                            color: {color}; text-shadow: 0 0 15px {color};">
                    {value}
                </div>
                <div style="font-family: 'Rajdhani'; font-size: 0.9rem; text-transform: uppercase; 
                            letter-spacing: 2px; color: #8892b0; margin-top: 0.8rem;">
                    {label}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
    
    # Charts Row
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ◈ WAREHOUSE DISTRIBUTION")
        warehouse_data = df.groupby('warehouse_location')['quantity'].sum().reset_index()
        
        fig = go.Figure(data=[
            go.Bar(
                x=warehouse_data['warehouse_location'],
                y=warehouse_data['quantity'],
                marker=dict(
                    color=warehouse_data['quantity'],
                    colorscale=[[0, '#00ffcc'], [0.5, '#0099ff'], [1, '#9933ff']],
                    line=dict(color='rgba(0, 255, 204, 0.5)', width=2)
                )
            )
        ])
        
        fig.update_layout(create_custom_chart(df))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### ◈ TOP PRODUCTS BY VALUE")
        top_products = df.nlargest(10, 'total_value')[['product_name', 'total_value']]
        
        fig = go.Figure(data=[
            go.Pie(
                labels=top_products['product_name'],
                values=top_products['total_value'],
                hole=0.6,
                marker=dict(
                    colors=px.colors.sequential.Viridis,
                    line=dict(color='rgba(0, 255, 204, 0.3)', width=2)
                ),
                textfont=dict(family='Rajdhani', size=12)
            )
        ])
        
        fig.update_layout(
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            font=dict(family='Rajdhani', color='#e0e6ed'),
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
    
    # Data Table
    st.markdown("### ◈ RECENT INVENTORY LOG")
    st.dataframe(
        df.head(10).style.set_properties(**{
            'background-color': 'rgba(15, 23, 42, 0.7)',
            'color': '#e0e6ed',
            'border-color': 'rgba(0, 255, 204, 0.2)'
        }),
        use_container_width=True
    )


def show_etl_pipeline():
    """Enhanced ETL Pipeline Control"""
    st.markdown("""
    <div class="main-header">
        ◈ PIPELINE CONTROL
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <div style="font-family: 'Orbitron'; font-size: 1.2rem; margin-bottom: 1rem;">
            ◉ DATA PROCESSING SEQUENCE
        </div>
        <div style="font-family: 'Rajdhani'; font-size: 1rem; line-height: 2;">
            <div style="display: flex; align-items: center; margin: 0.5rem 0;">
                <span style="color: #00ffcc; margin-right: 1rem;">01.</span>
                <span style="color: #8892b0;">EXTRACT</span>
                <span style="color: #00ffcc; margin-left: auto;">Load from CSV/JSON/Excel/API</span>
            </div>
            <div style="display: flex; align-items: center; margin: 0.5rem 0;">
                <span style="color: #00ffcc; margin-right: 1rem;">02.</span>
                <span style="color: #8892b0;">TRANSFORM</span>
                <span style="color: #00ffcc; margin-left: auto;">Clean, validate, enrich data</span>
            </div>
            <div style="display: flex; align-items: center; margin: 0.5rem 0;">
                <span style="color: #00ffcc; margin-right: 1rem;">03.</span>
                <span style="color: #8892b0;">LOAD</span>
                <span style="color: #00ffcc; margin-left: auto;">Store in Supabase database</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("⚡ INITIATE PIPELINE", use_container_width=True, type="primary"):
        progress_bar = st.progress(0)
        status_container = st.empty()
        
        try:
            # Extract
            status_container.markdown("""
            <div class="loading-indicator" style="font-family: 'Orbitron'; color: #00ffcc; font-size: 1.2rem;">
                ◉ EXTRACTING DATA...
            </div>
            """, unsafe_allow_html=True)
            progress_bar.progress(25)
            time.sleep(0.5)
            
            extractor = DataExtractor()
            df = extractor.extract_from_csv("data/sample/sample_supply_chain.csv")
            
            status_container.markdown(f"""
            <div class="success-box">
                ✓ EXTRACTION COMPLETE • {len(df)} RECORDS
            </div>
            """, unsafe_allow_html=True)
            
            # Transform
            status_container.markdown("""
            <div class="loading-indicator" style="font-family: 'Orbitron'; color: #00ffcc; font-size: 1.2rem;">
                ◉ TRANSFORMING DATA...
            </div>
            """, unsafe_allow_html=True)
            progress_bar.progress(50)
            time.sleep(0.5)
            
            transformer = DataTransformer()
            df_clean = transformer.clean_data(df)
            df_enriched = transformer.enrich_data(df_clean)
            
            status_container.markdown(f"""
            <div class="success-box">
                ✓ TRANSFORMATION COMPLETE • {len(df_enriched)} RECORDS
            </div>
            """, unsafe_allow_html=True)
            
            # Load
            status_container.markdown("""
            <div class="loading-indicator" style="font-family: 'Orbitron'; color: #00ffcc; font-size: 1.2rem;">
                ◉ LOADING TO DATABASE...
            </div>
            """, unsafe_allow_html=True)
            progress_bar.progress(75)
            time.sleep(0.5)
            
            loader = DataLoader()
            rows_loaded = loader.load_to_database(df_enriched)
            
            progress_bar.progress(100)
            status_container.markdown(f"""
            <div class="success-box">
                <div style="font-family: 'Orbitron'; font-size: 1.5rem;">
                    ✓ PIPELINE COMPLETE
                </div>
                <div class="mono-text" style="margin-top: 0.5rem; font-size: 1.1rem;">
                    {rows_loaded} RECORDS LOADED
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.balloons()
            st.cache_data.clear()
            
        except Exception as e:
            status_container.markdown(f"""
            <div class="error-box">
                <div style="font-family: 'Orbitron'; font-size: 1.2rem;">
                    ✗ PIPELINE ERROR
                </div>
                <div class="mono-text" style="margin-top: 0.5rem; font-size: 0.9rem;">
                    {str(e)}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Recent Logs
    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
    st.markdown("### ◈ EXECUTION LOG")
    
    try:
        loader = DataLoader()
        response = loader.supabase.table('pipeline_logs').select("*").order('created_at', desc=True).limit(5).execute()
        
        if response.data:
            logs_df = pd.DataFrame(response.data)
            st.dataframe(logs_df, use_container_width=True)
        else:
            st.markdown("""
            <div class="info-box">
                <span class="mono-text">NO EXECUTION LOGS AVAILABLE</span>
            </div>
            """, unsafe_allow_html=True)
    except:
        st.markdown("""
        <div class="warning-box">
            <span class="mono-text">LOGS UNAVAILABLE</span>
        </div>
        """, unsafe_allow_html=True)


def show_data_quality():
    """Enhanced Data Quality page"""
    st.markdown("""
    <div class="main-header">
        ◈ QUALITY ASSURANCE
    </div>
    """, unsafe_allow_html=True)
    
    df = load_data_from_db()
    
    if df is None or len(df) == 0:
        st.markdown("""
        <div class="warning-box">
            <span class="mono-text">NO DATA AVAILABLE FOR ANALYSIS</span>
        </div>
        """, unsafe_allow_html=True)
        return
    
    if st.button("⚡ RUN DIAGNOSTIC", use_container_width=True, type="primary"):
        with st.spinner("◉ Analyzing..."):
            checker = DataQualityChecker()
            results = checker.validate_all(df)
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div class="holo-card" style="text-align: center;">
                    <div style="font-size: 2rem; font-family: 'Orbitron'; color: #00ffcc;">
                        {results['total_checks']}
                    </div>
                    <div style="font-family: 'Rajdhani'; font-size: 0.85rem; color: #8892b0; margin-top: 0.5rem;">
                        TOTAL CHECKS
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="holo-card" style="text-align: center;">
                    <div style="font-size: 2rem; font-family: 'Orbitron'; color: #00ff88;">
                        {results['passed']}
                    </div>
                    <div style="font-family: 'Rajdhani'; font-size: 0.85rem; color: #8892b0; margin-top: 0.5rem;">
                        PASSED
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="holo-card" style="text-align: center;">
                    <div style="font-size: 2rem; font-family: 'Orbitron'; color: #ff3366;">
                        {results['failed']}
                    </div>
                    <div style="font-family: 'Rajdhani'; font-size: 0.85rem; color: #8892b0; margin-top: 0.5rem;">
                        FAILED
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Status
            success_rate = results['success_rate']
            
            if success_rate >= 95:
                st.markdown(f"""
                <div class="success-box">
                    <div style="font-family: 'Orbitron'; font-size: 1.5rem;">
                        ✓ EXCELLENT QUALITY
                    </div>
                    <div class="mono-text" style="margin-top: 0.5rem; font-size: 1.2rem;">
                        SCORE: {success_rate}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif success_rate >= 80:
                st.markdown(f"""
                <div class="warning-box">
                    <div style="font-family: 'Orbitron'; font-size: 1.5rem;">
                        ⚠ ACCEPTABLE QUALITY
                    </div>
                    <div class="mono-text" style="margin-top: 0.5rem; font-size: 1.2rem;">
                        SCORE: {success_rate}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="error-box">
                    <div style="font-family: 'Orbitron'; font-size: 1.5rem;">
                        ✗ QUALITY ISSUES DETECTED
                    </div>
                    <div class="mono-text" style="margin-top: 0.5rem; font-size: 1.2rem;">
                        SCORE: {success_rate}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Details
            st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
            st.markdown("### ◈ DIAGNOSTIC REPORT")
            
            for detail in results['details']:
                emoji = "✓" if detail['status'] == 'PASS' else "✗"
                color = "#00ff88" if detail['status'] == 'PASS' else "#ff3366"
                
                st.markdown(f"""
                <div style="padding: 0.8rem; background: rgba(15, 23, 42, 0.5); 
                            border-left: 3px solid {color}; margin: 0.5rem 0; border-radius: 4px;">
                    <span style="color: {color}; font-family: 'Orbitron'; margin-right: 1rem;">{emoji}</span>
                    <span class="mono-text">{detail['message']}</span>
                </div>
                """, unsafe_allow_html=True)


def show_ml_predictions():
    """Enhanced ML Predictions page"""
    st.markdown("""
    <div class="main-header">
        ◈ AI ANALYTICS
    </div>
    """, unsafe_allow_html=True)
    
    df = load_data_from_db()
    
    if df is None or len(df) == 0:
        st.markdown("""
        <div class="warning-box">
            <span class="mono-text">NO DATA AVAILABLE FOR ANALYSIS</span>
        </div>
        """, unsafe_allow_html=True)
        return
    
    tab1, tab2, tab3 = st.tabs(["◈ DEMAND FORECAST", "◈ ANOMALY SCAN", "◈ REORDER CALC"])
    
    with tab1:
        st.markdown("### ◉ PREDICTIVE DEMAND ANALYSIS")
        st.markdown("""
        <div class="info-box">
            <span class="mono-text">RANDOM FOREST ALGORITHM • MULTI-FEATURE ANALYSIS</span>
        </div>
        """, unsafe_allow_html=True)
        
        if len(df) < 5:
            st.warning("⚠️ Insufficient data for training (minimum 5 records required)")
            return
        
        if st.button("⚡ TRAIN MODEL", key="train_model", type="primary"):
            with st.spinner("◉ Training neural pathways..."):
                try:
                    df_prep = df.copy()
                    
                    for col in ['expiry_date', 'manufacture_date']:
                        if col in df_prep.columns:
                            df_prep[col] = pd.to_datetime(df_prep[col], errors='coerce')
                    
                    if 'total_value' not in df_prep.columns:
                        df_prep['total_value'] = df_prep['quantity'] * df_prep['unit_price']
                    
                    if 'days_until_expiry' not in df_prep.columns and 'expiry_date' in df_prep.columns:
                        df_prep['days_until_expiry'] = (df_prep['expiry_date'] - pd.Timestamp.now()).dt.days
                    
                    forecaster = DemandForecaster()
                    metrics = forecaster.train(df_prep)
                    
                    st.markdown("""
                    <div class="success-box">
                        <div style="font-family: 'Orbitron'; font-size: 1.2rem;">
                            ✓ MODEL TRAINED
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"""
                        <div class="holo-card" style="text-align: center;">
                            <div style="font-size: 1.8rem; font-family: 'Orbitron'; color: #00ffcc;">
                                {metrics['test_r2']:.4f}
                            </div>
                            <div style="font-size: 0.8rem; color: #8892b0; margin-top: 0.5rem;">R² SCORE</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
                        <div class="holo-card" style="text-align: center;">
                            <div style="font-size: 1.8rem; font-family: 'Orbitron'; color: #0099ff;">
                                {metrics['mae']:.2f}
                            </div>
                            <div style="font-size: 0.8rem; color: #8892b0; margin-top: 0.5rem;">MAE</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"""
                        <div class="holo-card" style="text-align: center;">
                            <div style="font-size: 1.8rem; font-family: 'Orbitron'; color: #9933ff;">
                                {metrics['rmse']:.2f}
                            </div>
                            <div style="font-size: 0.8rem; color: #8892b0; margin-top: 0.5rem;">RMSE</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Predictions
                    predictions = forecaster.predict(df_prep)
                    
                    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
                    st.markdown("### ◈ PREDICTION OUTPUT")
                    
                    pred_display = predictions[['product_name', 'quantity', 'predicted_demand']].head(10)
                    st.dataframe(pred_display, use_container_width=True)
                    
                    # Chart
                    top_10 = pred_display.head(10)
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        name='Current',
                        x=top_10['product_name'],
                        y=top_10['quantity'],
                        marker=dict(color='rgba(0, 255, 204, 0.6)', line=dict(color='#00ffcc', width=2))
                    ))
                    fig.add_trace(go.Bar(
                        name='Predicted',
                        x=top_10['product_name'],
                        y=top_10['predicted_demand'],
                        marker=dict(color='rgba(153, 51, 255, 0.6)', line=dict(color='#9933ff', width=2))
                    ))
                    fig.update_layout(create_custom_chart(df), barmode='group')
                    st.plotly_chart(fig, use_container_width=True)
                    
                except Exception as e:
                    st.markdown(f"""
                    <div class="error-box">
                        <div style="font-family: 'Orbitron'; font-size: 1.2rem;">
                            ✗ TRAINING FAILED
                        </div>
                        <div class="mono-text" style="margin-top: 0.5rem; font-size: 0.85rem;">
                            {str(e)}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### ◉ ANOMALY DETECTION SCAN")
        st.markdown("""
        <div class="info-box">
            <span class="mono-text">ISOLATION FOREST ALGORITHM • OUTLIER ANALYSIS</span>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("⚡ SCAN FOR ANOMALIES", key="detect_anomalies", type="primary"):
            with st.spinner("◉ Scanning data patterns..."):
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
                        st.markdown(f"""
                        <div class="holo-card" style="text-align: center;">
                            <div style="font-size: 2.5rem; font-family: 'Orbitron'; color: #00ffcc;">
                                {len(result_df)}
                            </div>
                            <div style="font-size: 0.85rem; color: #8892b0; margin-top: 0.5rem;">
                                TOTAL RECORDS
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
                        <div class="holo-card" style="text-align: center;">
                            <div style="font-size: 2.5rem; font-family: 'Orbitron'; color: #ff3366;">
                                {len(anomalies)}
                            </div>
                            <div style="font-size: 0.85rem; color: #8892b0; margin-top: 0.5rem;">
                                ANOMALIES DETECTED
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if len(anomalies) > 0:
                        st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
                        st.markdown("### ◈ ANOMALOUS RECORDS")
                        
                        st.dataframe(
                            anomalies[['product_name', 'quantity', 'unit_price', 'anomaly_score']].head(10),
                            use_container_width=True
                        )
                        
                        fig = px.scatter(
                            anomalies.head(20),
                            x='quantity',
                            y='unit_price',
                            color='anomaly_score',
                            hover_data=['product_name'],
                            color_continuous_scale=[[0, '#ff3366'], [0.5, '#ffbf00'], [1, '#00ffcc']]
                        )
                        fig.update_layout(create_custom_chart(df))
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.markdown("""
                        <div class="success-box">
                            <div style="font-family: 'Orbitron'; font-size: 1.2rem;">
                                ✓ NO ANOMALIES DETECTED
                            </div>
                            <div class="mono-text" style="margin-top: 0.5rem;">
                                ALL PATTERNS WITHIN NORMAL PARAMETERS
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.markdown(f"""
                    <div class="error-box">
                        <div style="font-family: 'Orbitron'; font-size: 1.2rem;">
                            ✗ SCAN FAILED
                        </div>
                        <div class="mono-text" style="margin-top: 0.5rem; font-size: 0.85rem;">
                            {str(e)}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab3:
        st.markdown("### ◉ REORDER POINT CALCULATION")
        st.markdown("""
        <div class="info-box">
            <span class="mono-text">EOQ ALGORITHM • SAFETY STOCK ANALYSIS</span>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("⚡ CALCULATE REORDER POINTS", key="calc_reorder", type="primary"):
            with st.spinner("◉ Calculating optimal points..."):
                try:
                    calculator = ReorderPointCalculator(safety_stock_days=7)
                    reorder_df = calculator.calculate_reorder_points(df)
                    
                    needs_reorder = reorder_df[reorder_df['needs_reorder'] == 1]
                    
                    st.markdown(f"""
                    <div class="holo-card" style="text-align: center;">
                        <div style="font-size: 2.5rem; font-family: 'Orbitron'; color: #ffbf00;">
                            {len(needs_reorder)}
                        </div>
                        <div style="font-size: 0.9rem; color: #8892b0; margin-top: 0.5rem;">
                            PRODUCTS REQUIRING REORDER
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if len(needs_reorder) > 0:
                        st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
                        st.markdown("### ⚠ BELOW REORDER THRESHOLD")
                        
                        st.dataframe(
                            needs_reorder[['product_name', 'quantity', 'reorder_point', 'reorder_quantity']],
                            use_container_width=True
                        )
                    else:
                        st.markdown("""
                        <div class="success-box">
                            <div style="font-family: 'Orbitron'; font-size: 1.2rem;">
                                ✓ ALL PRODUCTS ABOVE THRESHOLD
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.markdown(f"""
                    <div class="error-box">
                        <div style="font-family: 'Orbitron'; font-size: 1.2rem;">
                            ✗ CALCULATION FAILED
                        </div>
                        <div class="mono-text" style="margin-top: 0.5rem; font-size: 0.85rem;">
                            {str(e)}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


def show_analytics():
    """Enhanced Analytics page"""
    st.markdown("""
    <div class="main-header">
        ◈ DATA OBSERVATORY
    </div>
    """, unsafe_allow_html=True)
    
    df = load_data_from_db()
    
    if df is None or len(df) == 0:
        st.markdown("""
        <div class="warning-box">
            <span class="mono-text">NO DATA AVAILABLE FOR ANALYSIS</span>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Time series
    if 'created_at' in df.columns:
        st.markdown("### ◈ TEMPORAL ANALYSIS")
        df['date'] = pd.to_datetime(df['created_at']).dt.date
        time_series = df.groupby('date')['quantity'].sum().reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=time_series['date'],
            y=time_series['quantity'],
            mode='lines+markers',
            line=dict(color='#00ffcc', width=3, shape='spline'),
            marker=dict(size=8, color='#00ffcc', symbol='diamond'),
            fill='tozeroy',
            fillcolor='rgba(0, 255, 204, 0.1)'
        ))
        fig.update_layout(create_custom_chart(df))
        st.plotly_chart(fig, use_container_width=True)
    
    # Warehouse stats
    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)
    st.markdown("### ◈ WAREHOUSE PERFORMANCE MATRIX")
    
    warehouse_stats = df.groupby('warehouse_location').agg({
        'quantity': 'sum',
        'total_value': 'sum',
        'product_id': 'nunique'
    }).reset_index()
    warehouse_stats.columns = ['Warehouse', 'Total Quantity', 'Total Value', 'Unique Products']
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.dataframe(warehouse_stats, use_container_width=True)
    
    with col2:
        fig = go.Figure(data=[
            go.Bar(
                x=warehouse_stats['Warehouse'],
                y=warehouse_stats['Total Quantity'],
                marker=dict(
                    color=warehouse_stats['Total Quantity'],
                    colorscale=[[0, '#00ffcc'], [0.5, '#0099ff'], [1, '#9933ff']],
                    line=dict(color='rgba(0, 255, 204, 0.5)', width=2)
                ),
                text=warehouse_stats['Total Quantity'],
                textposition='outside',
                textfont=dict(family='Orbitron', size=12)
            )
        ])
        fig.update_layout(create_custom_chart(df))
        st.plotly_chart(fig, use_container_width=True)


def show_alerts():
    """Enhanced Alerts page"""
    st.markdown("""
    <div class="main-header">
        ◈ ALERT SYSTEM
    </div>
    """, unsafe_allow_html=True)
    
    df = load_data_from_db()
    
    if df is None or len(df) == 0:
        st.markdown("""
        <div class="warning-box">
            <span class="mono-text">NO DATA AVAILABLE FOR MONITORING</span>
        </div>
        """, unsafe_allow_html=True)
        return
    
    alert_manager = AlertManager()
    alerts = alert_manager.check_inventory_alerts(df)
    
    if alerts:
        st.markdown(f"""
        <div class="holo-card" style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 2.5rem; font-family: 'Orbitron'; color: #ff3366;">
                {len(alerts)}
            </div>
            <div style="font-size: 0.9rem; color: #8892b0; margin-top: 0.5rem;">
                ACTIVE ALERTS
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        for alert in alerts:
            severity = alert.get('severity', 'INFO')
            message = alert['message']
            
            if severity == 'CRITICAL':
                st.markdown(f"""
                <div class="error-box">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 1.5rem; margin-right: 1rem;">🚨</span>
                        <div>
                            <div style="font-family: 'Orbitron'; font-size: 1.2rem;">CRITICAL</div>
                            <div class="mono-text" style="margin-top: 0.3rem;">{message}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif severity == 'WARNING':
                st.markdown(f"""
                <div class="warning-box">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 1.5rem; margin-right: 1rem;">⚠️</span>
                        <div>
                            <div style="font-family: 'Orbitron'; font-size: 1.2rem;">WARNING</div>
                            <div class="mono-text" style="margin-top: 0.3rem;">{message}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="info-box">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 1.5rem; margin-right: 1rem;">ℹ️</span>
                        <div>
                            <div style="font-family: 'Orbitron'; font-size: 1.2rem;">INFO</div>
                            <div class="mono-text" style="margin-top: 0.3rem;">{message}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="success-box" style="text-align: center; padding: 3rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">✓</div>
            <div style="font-family: 'Orbitron'; font-size: 1.5rem;">ALL SYSTEMS NORMAL</div>
            <div class="mono-text" style="margin-top: 0.5rem; font-size: 1rem;">
                NO ALERTS DETECTED
            </div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()