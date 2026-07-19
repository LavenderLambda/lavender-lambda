import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from supabase import create_client, Client

# --- 1. CONFIG & CLOUD CONNECTION ---
st.set_page_config(page_title="Lavender Lambda Cloud", page_icon="💜", layout="wide")

@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- 2. WATCHLIST ---
WATCHLIST = {
    "Crypto": ["BTC-AUD", "ETH-AUD"],
    "Equities": ["SPY", "VAS.AX", "NVDA"],
    "Commodities": ["GC=F", "SI=F"],
    "Macro": ["AUDUSD=X", "^TNX"]
}
ALL_TICKERS = [t for sub in WATCHLIST.values() for t in sub]

# --- 3. CLOUD DATABASE LOGIC ---
def get_override():
    try:
        res = supabase.table("system_state").select("override").eq("id", 1).execute()
        return res.data[0]["override"] if res.data else False
    except: return False

def set_override(val):
    supabase.table("system_state").update({"override": val}).eq("id", 1).execute()

def save_knowledge(asset, event, context, date_str=None):
    data = {"asset": asset, "event": event, "context": context}
    if date_str:
        data["created_at"] = date_str
    supabase.table("knowledge_ledger").insert(data).execute()

# --- 4. BACKFILL TOOL (The "History Puller") ---
def run_backfill():
    st.sidebar.info("Scanning last 30 days...")
    # Fetch 1 month of history
    hist = yf.download(ALL_TICKERS, period="1mo", interval="1d", progress=False)['Close']
    deltas = hist.pct_change() * 100
    
    count = 0
    for ticker in ALL_TICKERS:
        # Find days where this asset moved > 5%
        anomalies = deltas[abs(deltas[ticker]) > 5.0][ticker]
        for date, val in anomalies.items():
            save_knowledge(
                ticker, 
                "Historical Volatility", 
                f"Backfilled: Move of {val:.2f}%",
                date.strftime('%Y-%m-%dT%H:%M:%SZ')
            )
            count += 1
    st.sidebar.success(f"Successfully taught AI {count} historical events!")

# --- 5. UI LAYOUT ---
st.title("💜 Lavender Lambda v1.6.1")

# Sidebar
with st.sidebar:
    st.header("Constitution")
    current_ov = get_override()
    if st.toggle("🚨 GLOBAL OVERRIDE", value=current_ov):
        set_override(True)
    else:
        set_override(False)
    
    st.divider()
    st.header("Admin Tools")
    if st.button("📥 Backfill 30-Day History"):
        run_backfill()
    st.caption("Use this once to populate your Cloud Brain.")

# Data Engine
@st.cache_data(ttl=3600)
def get_current_data():
    return yf.download(ALL_TICKERS, period="1mo", interval="1d", progress=False)['Close']

hist_df = get_current_data()

tab_scan, tab_intel, tab_perf = st.tabs(["📡 Scanner", "🧠 Intelligence", "📈 Performance"])

with tab_scan:
    if hist_df is not None:
        for sector, tickers in WATCHLIST.items():
            st.subheader(sector)
            cols = st.columns(len(tickers))
            for i, t in enumerate(tickers):
                try:
                    price = hist_df[t].iloc[-1]
                    prev = hist_df[t].iloc[-2]
                    delta = ((price - prev) / prev) * 100
                    cols[i].metric(t.replace("-AUD", ""), f"${price:,.2f}", f"{delta:.2f}%")
                except: continue

with tab_intel:
    st.subheader("Inter-market Analysis")
    if hist_df is not None:
        corr = hist_df.pct_change().corr()
        btc_link = corr['BTC-AUD'].sort_values(ascending=False)
        st.success(f"**BTC-AUD** Correlation: Synced with **{btc_link.index[1]}** ({btc_link.iloc[1]:.2f})")
    
    st.divider()
    st.subheader("Permanent Knowledge Ledger (Cloud)")
    # Show the latest 10 events from Supabase
    logs = supabase.table("knowledge_ledger").select("*").order("created_at", desc=True).limit(10).execute()
    if logs.data:
        st.dataframe(pd.DataFrame(logs.data)[["created_at", "asset", "context"]], use_container_width=True)
    else:
        st.write("Brain is empty. Hit the 'Backfill' button in the sidebar to teach the AI history!")

with tab_perf:
    st.subheader("System Accuracy")
    # Performance chart logic remains pending real grading data
    st.info("Performance data will populate as you use the app over the next 7 days.")

st.caption(f"Last Sync: {datetime.now().strftime('%H:%M:%S')} AUD")
