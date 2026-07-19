import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
from supabase import create_client, Client
import plotly.express as px

# --- 1. CONFIG & CLOUD CONNECTION ---
st.set_page_config(page_title="Lavender Lambda Cloud", page_icon="💜", layout="wide")

# Connect to Supabase using your Secrets
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
    res = supabase.table("system_state").select("override").eq("id", 1).execute()
    return res.data[0]["override"] if res.data else False

def set_override(val):
    supabase.table("system_state").update({"override": val}).eq("id", 1).execute()

def save_knowledge(asset, event, context):
    supabase.table("knowledge_ledger").insert({
        "asset": asset, "event": event, "context": context
    }).execute()

# --- 4. ENGINE ---
@st.cache_data(ttl=3600)
def get_data():
    return yf.download(ALL_TICKERS, period="1mo", interval="1d", progress=False)['Close']

# --- 5. MOBILE UI ---
st.title("💜 Lavender Lambda v1.6.0")

# Sidebar Override
with st.sidebar:
    st.header("Constitution")
    current_ov = get_override()
    new_ov = st.toggle("🚨 GLOBAL OVERRIDE", value=current_ov)
    if new_ov != current_ov:
        set_override(new_ov)
        st.rerun()
    st.info("Storage: Supabase Cloud Connected")

hist_df = get_data()

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
                    
                    # AUTO-KNOWLEDGE: Save to Supabase if move > 5%
                    if abs(delta) > 5.0:
                        save_knowledge(t, "Volatility Spike", f"Move of {delta:.2f}% detected.")
                except: continue

with tab_intel:
    st.subheader("Cloud Intelligence")
    if hist_df is not None:
        corr = hist_df.pct_change().corr()
        btc_link = corr['BTC-AUD'].sort_values(ascending=False)
        st.success(f"**BTC-AUD** is currently tracking **{btc_link.index[1]}** ({btc_link.iloc[1]:.2f})")
    
    st.divider()
    st.subheader("Permanent Knowledge Ledger")
    # Pulling from Supabase Cloud
    knowledge_data = supabase.table("knowledge_ledger").select("*").order("created_at", desc=True).limit(5).execute()
    if knowledge_data.data:
        st.table(pd.DataFrame(knowledge_data.data)[["created_at", "asset", "event"]])
    else:
        st.write("Awaiting first major market anomaly...")

with tab_perf:
    st.subheader("Historical Learning")
    # This will now grow day-by-day and NEVER be deleted
    perf_data = supabase.table("performance_logs").select("*").execute()
    if perf_data.data:
        st.line_chart(pd.DataFrame(perf_data.data), x='date', y='error_rate')
    else:
        st.info("Initial Observation Phase: Recording first data points in Supabase...")

st.caption(f"Cloud Sync: {datetime.now().strftime('%H:%M:%S')} AUD")
