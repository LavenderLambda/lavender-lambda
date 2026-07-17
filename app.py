import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import sqlite3

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="Lavender Lambda Scanner", page_icon="💜", layout="wide")

st.markdown("""
    <style>
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; border-left: 5px solid #4B0082; }
    .status-active { color: green; font-weight: bold; }
    .status-inactive { color: red; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ASSET WATCHLIST ---
WATCHLIST = {
    "Crypto": ["BTC-AUD", "ETH-AUD", "SOL-AUD"],
    "US Equity": ["SPY", "NVDA", "TSLA", "AAPL"],
    "ASX (AU)": ["CBA.AX", "BHP.AX", "VAS.AX"],
    "Commodities": ["GC=F", "SI=F"], # Gold, Silver
    "FX & Macro": ["AUDUSD=X", "^TNX", "^VIX"] # FX, 10Y Yield, Volatility Index
}

# --- 3. DATABASE (State Management) ---
def get_db():
    conn = sqlite3.connect('lavender_v2.db', check_same_thread=False)
    conn.execute('CREATE TABLE IF NOT EXISTS system_state (id INTEGER PRIMARY KEY, override BOOLEAN)')
    conn.execute('INSERT OR IGNORE INTO system_state (id, override) VALUES (1, 0)')
    conn.commit()
    return conn

db = get_db()

def is_override():
    return db.execute('SELECT override FROM system_state WHERE id=1').fetchone()[0]

# --- 4. SCANNER ENGINE ---
@st.cache_data(ttl=300) # Cache data for 5 mins to save battery/data
def scan_markets(assets):
    results = []
    tickers = [item for sublist in assets.values() for item in sublist]
    data = yf.download(tickers, period="2d", interval="1d", group_by='ticker', progress=False)
    
    for sector, items in assets.items():
        for ticker in items:
            try:
                # Handle single vs multi-index dataframes from yfinance
                target = data[ticker] if len(tickers) > 1 else data
                close = target['Close'].iloc[-1]
                prev_close = target['Close'].iloc[-2]
                change = ((close - prev_close) / prev_close) * 100
                results.append({"Sector": sector, "Asset": ticker, "Price": close, "Delta %": round(change, 2)})
            except:
                continue
    return pd.DataFrame(results)

# --- 5. MOBILE UI ---
st.title("💜 Lavender Lambda Scanner")

# Header & Override
state = "INACTIVE" if is_override() else "ACTIVE"
col_h1, col_h2 = st.columns([2, 1])
with col_h1:
    st.write(f"System Status: <span class='status-{state.lower()}'>{state}</span>", unsafe_allow_html=True)
with col_h2:
    if st.button("🔄 Refresh Scan"):
        st.cache_data.clear()
        st.rerun()

# Global Override Toggle
if st.toggle("🚨 ACTIVATE GLOBAL OVERRIDE", value=is_override()):
    db.execute('UPDATE system_state SET override = 1 WHERE id=1')
    db.commit()
else:
    db.execute('UPDATE system_state SET override = 0 WHERE id=1')
    db.commit()

st.divider()

# The Scanner Table
df_scan = scan_markets(WATCHLIST)

# 6. INTELLIGENCE HIGHLIGHTS
st.subheader("🔥 Intelligence Alerts (>3% Move)")
alerts = df_scan[abs(df_scan['Delta %']) > 3]
if not alerts.empty:
    for _, alert in alerts.iterrows():
        st.warning(f"**{alert['Asset']}** ({alert['Sector']}) moved **{alert['Delta %']}%**. Analyzing impact...")
else:
    st.success("Markets stable. No major anomalies detected in the Circle of Competence.")

# 7. SECTOR TABS
tabs = st.tabs(list(WATCHLIST.keys()))
for i, sector in enumerate(WATCHLIST.keys()):
    with tabs[i]:
        sector_df = df_scan[df_scan['Sector'] == sector]
        st.dataframe(sector_df[["Asset", "Price", "Delta %"]], hide_index=True, use_container_width=True)

st.divider()
st.caption(f"Last Scan: {datetime.now().strftime('%H:%M:%S')} AUD/UTC")
