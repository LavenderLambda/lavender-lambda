import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import plotly.express as px

# --- 1. CONFIG ---
st.set_page_config(page_title="Lavender Lambda Intelligence", page_icon="💜", layout="wide")

# --- 2. DATABASE ---
def init_db():
    conn = sqlite3.connect('lavender_v4.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS system_state (id INTEGER PRIMARY KEY, override BOOLEAN)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS performance_logs (date TEXT PRIMARY KEY, error_rate REAL)''')
    conn.execute('INSERT OR IGNORE INTO system_state (id, override) VALUES (1, 0)')
    conn.commit()
    return conn

db = init_db()

# --- 3. WATCHLIST ---
WATCHLIST = {
    "Crypto": ["BTC-AUD", "ETH-AUD"],
    "Equities": ["SPY", "VAS.AX", "NVDA"],
    "Commodities": ["GC=F", "SI=F"],
    "Macro": ["AUDUSD=X", "^TNX"]
}
ALL_TICKERS = [t for sub in WATCHLIST.values() for t in sub]

# --- 4. INTELLIGENCE FUNCTIONS ---

@st.cache_data(ttl=3600)
def get_intel_data():
    """Fetches 30 days of data so the Intelligence tab isn't empty."""
    try:
        data = yf.download(ALL_TICKERS, period="1mo", interval="1d", progress=False)['Close']
        return data
    except:
        return None

def get_context_news(ticker):
    try:
        return yf.Ticker(ticker).news[:3]
    except:
        return []

# --- 5. UI LAYOUT ---
st.title("💜 Lavender Lambda v1.5.2")

# Status Sidebar
with st.sidebar:
    st.header("Constitution")
    override_val = db.execute('SELECT override FROM system_state').fetchone()[0]
    if st.toggle("🚨 GLOBAL OVERRIDE", value=bool(override_val)):
        db.execute('UPDATE system_state SET override = 1')
    else:
        db.execute('UPDATE system_state SET override = 0')
    db.commit()
    st.info("Autonomy Mode: Watching & Learning")

# Data Engine
intel_df = get_intel_data()

tab_scan, tab_intel, tab_perf = st.tabs(["📡 Scanner", "🧠 Intelligence", "📈 Performance"])

with tab_scan:
    if intel_df is not None:
        for sector, tickers in WATCHLIST.items():
            st.subheader(sector)
            cols = st.columns(len(tickers))
            for i, t in enumerate(tickers):
                try:
                    price = intel_df[t].iloc[-1]
                    prev = intel_df[t].iloc[-2]
                    delta = ((price - prev) / prev) * 100
                    cols[i].metric(t.replace("-AUD", ""), f"${price:,.2f}", f"{delta:.2f}%")
                except:
                    continue
    else:
        st.error("Market data link down. Check internet connection.")

with tab_intel:
    st.subheader("Inter-market Analysis (Past 30 Days)")
    if intel_df is not None:
        corr_matrix = intel_df.pct_change().corr()
        btc_corr = corr_matrix['BTC-AUD'].sort_values(ascending=False)
        
        # Display the 'Best Friend'
        partner = btc_corr.index[1]
        strength = btc_corr.iloc[1]
        
        st.success(f"**BTC-AUD** is currently tracking **{partner}** (Correlation: {strength:.2f})")
        
        # News Context
        st.divider()
        asset = st.selectbox("Get News Context for:", ALL_TICKERS)
        for n in get_context_news(asset):
            st.write(f"🔗 **[{n['title']}]({n['link']})**")
    else:
        st.warning("Insufficient data to calculate relationships.")

with tab_perf:
    st.subheader("System Learning Curve")
    st.write("This chart tracks the gap between the AI's predictions and reality.")
    
    # We fetch the logs from the DB
    logs = pd.read_sql("SELECT * FROM performance_logs", db)
    
    if len(logs) < 2:
        st.info("📊 **Observation Phase:** The system needs 48 hours of uptime to generate the first 'Error Grade'. Check back tomorrow!")
        # Placeholder so the page isn't blank
        dummy_data = pd.DataFrame({'Day': ['Starting...'], 'Error %': [20]})
        st.line_chart(dummy_data, x='Day', y='Error %')
    else:
        st.line_chart(logs, x='date', y='error_rate')

st.caption(f"Last Sync: {datetime.now().strftime('%H:%M:%S')} AUD")
