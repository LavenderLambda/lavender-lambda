import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import sqlite3

# --- 1. MOBILE PAGE CONFIG ---
st.set_page_config(page_title="LL Scanner", page_icon="💜", layout="centered")

# --- 2. ASSET WATCHLIST ---
WATCHLIST = {
    "Crypto": ["BTC-AUD", "ETH-AUD", "SOL-AUD"],
    "US Equity": ["SPY", "NVDA", "TSLA", "AAPL"],
    "ASX (AU)": ["CBA.AX", "BHP.AX", "VAS.AX"],
    "Commodities": ["GC=F", "SI=F"],
    "FX & Macro": ["AUDUSD=X", "^TNX", "^VIX"]
}

# --- 3. DATABASE ---
def get_db():
    conn = sqlite3.connect('lavender_v2.db', check_same_thread=False)
    conn.execute('CREATE TABLE IF NOT EXISTS system_state (id INTEGER PRIMARY KEY, override BOOLEAN)')
    conn.execute('INSERT OR IGNORE INTO system_state (id, override) VALUES (1, 0)')
    conn.commit()
    return conn

db = get_db()

# --- 4. LOGIC ---
def is_override():
    res = db.execute('SELECT override FROM system_state WHERE id=1').fetchone()
    return res[0] if res else False

@st.cache_data(ttl=300)
def scan_markets(assets):
    results = []
    tickers = [item for sublist in assets.values() for item in sublist]
    # Fetching 3 days to ensure we have enough data for a 24h delta
    data = yf.download(tickers, period="3d", interval="1d", group_by='ticker', progress=False)
    
    for sector, items in assets.items():
        for ticker in items:
            try:
                target = data[ticker] if len(tickers) > 1 else data
                close = target['Close'].iloc[-1]
                prev_close = target['Close'].iloc[-2]
                change = ((close - prev_close) / prev_close) * 100
                results.append({"Sector": sector, "Asset": ticker, "Price": close, "Delta %": round(change, 2)})
            except:
                continue
    return pd.DataFrame(results)

# --- 5. MOBILE UI (Clean Version) ---
st.title("💜 Lavender Lambda")

# System Status - Using Native Streamlit Tags (Better for Mobile)
override_active = is_override()
if override_active:
    st.error("SYSTEM STATUS: INACTIVE (OVERRIDE ON)")
else:
    st.success("SYSTEM STATUS: ACTIVE")

# Override Toggle
if st.toggle("🚨 GLOBAL OVERRIDE", value=override_active):
    db.execute('UPDATE system_state SET override = 1 WHERE id=1')
    db.commit()
    if not override_active: st.rerun()
else:
    db.execute('UPDATE system_state SET override = 0 WHERE id=1')
    db.commit()
    if override_active: st.rerun()

st.divider()

# Scanner Execution
try:
    df_scan = scan_markets(WATCHLIST)
    
    # Intelligence Highlights
    st.subheader("🔥 Market Anomalies (>3%)")
    alerts = df_scan[abs(df_scan['Delta %']) > 3]
    
    if not alerts.empty:
        for _, alert in alerts.iterrows():
            st.warning(f"**{alert['Asset']}** moved **{alert['Delta %']}%**")
    else:
        st.info("No major anomalies detected. Markets stable.")

    # Sector View
    st.subheader("📋 Full Scanner")
    selected_sector = st.selectbox("Select Sector", list(WATCHLIST.keys()))
    sector_df = df_scan[df_scan['Sector'] == selected_sector]
    st.dataframe(sector_df[["Asset", "Price", "Delta %"]], hide_index=True, use_container_width=True)

except Exception as e:
    st.error("Connectivity issue. Please refresh.")
    if st.button("🔄 Force Refresh"):
        st.cache_data.clear()
        st.rerun()

st.caption(f"Last Refresh: {datetime.now().strftime('%H:%M:%S')} AUD")
