import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime
import sqlite3
import plotly.express as px

# --- 1. CONFIG ---
st.set_page_config(page_title="Lavender Lambda Intelligence", page_icon="💜", layout="wide")

# --- 2. DATABASE ---
def init_db():
    conn = sqlite3.connect('lavender_v3.db', check_same_thread=False)
    conn.execute('''CREATE TABLE IF NOT EXISTS system_state (id INTEGER PRIMARY KEY, override BOOLEAN)''')
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
def get_correlations():
    try:
        data = yf.download(ALL_TICKERS, period="1mo", interval="1d", progress=False)['Close']
        if data.empty: return None
        corr = data.pct_change().corr()
        return corr
    except:
        return None

def get_context_news(ticker):
    try:
        t = yf.Ticker(ticker)
        return t.news[:3]
    except:
        return []

# --- 5. UI ---
st.title("💜 Lavender Lambda v1.5.1")

# Status Sidebar
with st.sidebar:
    st.header("Constitution")
    override_val = db.execute('SELECT override FROM system_state').fetchone()[0]
    if st.toggle("🚨 GLOBAL OVERRIDE", value=bool(override_val)):
        db.execute('UPDATE system_state SET override = 1')
    else:
        db.execute('UPDATE system_state SET override = 0')
    db.commit()
    st.write("Risk Budget: **20% (FIXED)**")

# Data Load
with st.spinner("Syncing Intelligence..."):
    data_load = yf.download(ALL_TICKERS, period="2d", group_by='ticker', progress=False)

tab_scan, tab_intel, tab_perf = st.tabs(["📡 Scanner", "🧠 Intelligence", "📈 Performance"])

with tab_scan:
    for sector, tickers in WATCHLIST.items():
        st.subheader(sector)
        cols = st.columns(len(tickers))
        for i, t in enumerate(tickers):
            try:
                inst = data_load[t] if len(ALL_TICKERS) > 1 else data_load
                price = inst['Close'].iloc[-1]
                prev = inst['Close'].iloc[-2]
                delta = ((price - prev) / prev) * 100
                cols[i].metric(t.replace("-AUD", ""), f"${price:,.2f}", f"{delta:.2f}%")
            except:
                cols[i].write(f"{t}: Data Pending")

with tab_intel:
    st.subheader("Inter-market Analysis")
    corr_matrix = get_correlations()
    
    if corr_matrix is not None and 'BTC-AUD' in corr_matrix.columns:
        # Fixed the KeyError by using .iloc (position) instead of label
        btc_corr = corr_matrix['BTC-AUD'].sort_values(ascending=False)
        if len(btc_corr) > 1:
            top_partner = btc_corr.index[1]
            strength = btc_corr.iloc[1]
