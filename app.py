import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
from supabase import create_client, Client
import plotly.express as px

# --- 1. SETTINGS & THEME ---
st.set_page_config(page_title="Lavender Intelligence", page_icon="💜", layout="wide")

# Custom CSS for a premium mobile feel
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #702963; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #f0f2f6; border-radius: 10px; padding: 10px 20px; 
    }
    div[data-testid="stExpander"] { border: none !important; box-shadow: none !important; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

# --- 2. THE WATCHLIST ---
WATCHLIST = {
    "💎 Crypto": ["BTC-AUD", "ETH-AUD"],
    "📈 Equities": ["NVDA", "SPY", "VAS.AX"],
    "📀 Commodities": ["GC=F", "SI=F"],
    "🌏 Macro": ["AUDUSD=X", "^TNX"]
}
ALL_TICKERS = [t for sub in WATCHLIST.values() for t in sub]

# --- 3. THE BRAIN (Logic) ---

def get_clean_data():
    try:
        df = yf.download(ALL_TICKERS, period="1mo", interval="1d", progress=False)['Close']
        return df.ffill() # "Forward Fill" prevents the $nan by carrying the last known price forward
    except: return None

def auto_log_performance(df):
    """Automatically fills the graph every time you open the app."""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        # Check if today is already logged
        check = supabase.table("performance_logs").select("date").eq("date", today).execute()
        if not check.data:
            # Calculate a simple 'Volatility Error' for the graph
            daily_vol = df.pct_change().iloc[-1].abs().mean() * 100
            supabase.table("performance_logs").insert({"date": today, "error_rate": daily_vol}).execute()
    except: pass

# --- 4. UI LAYOUT ---
st.title("💜 Lavender Lambda")

# Sidebar for Governance
with st.sidebar:
    st.header("Governance")
    res = supabase.table("system_state").select("override").eq("id", 1).execute()
    ov = res.data[0]["override"] if res.data else False
    if st.toggle("🚨 GLOBAL OVERRIDE", value=ov):
        supabase.table("system_state").update({"override": True}).eq("id", 1).execute()
        st.error("System is PAUSED")
    else:
        supabase.table("system_state").update({"override": False}).eq("id", 1).execute()
        st.success("System is ACTIVE")

# Fetch Data
hist_df = get_clean_data()

if hist_df is not None:
    auto_log_performance(hist_df)
    
    # DASHBOARD TABS
    tab1, tab2, tab3 = st.tabs(["📡 Scanner", "🧠 Intelligence", "📈 Performance"])

    with tab1:
        for sector, tickers in WATCHLIST.items():
            st.subheader(sector)
            cols = st.columns(len(tickers))
            for i, t in enumerate(tickers):
                with cols[i].container(border=True):
                    try:
                        price = hist_df[t].iloc[-1]
                        prev = hist_df[t].iloc[-2]
                        delta = ((price - prev) / prev) * 100
                        # Clean label
                        label = t.replace("-AUD", "").replace("=F", "")
                        
                        if pd.isna(delta) or delta == 0:
                            st.metric(label, f"${price:,.2f}", "Closed")
                        else:
                            st.metric(label, f"${price:,.2f}", f"{delta:.2f}%")
                    except:
                        st.caption(f"{t} offline")

    with tab2:
        st.subheader("Inter-market Correlations")
        corr = hist_df.pct_change().corr()
        if 'BTC-AUD' in corr.columns:
            btc_link = corr['BTC-AUD'].sort_values(ascending=False)
            st.info(f"**Market Insight:** Bitcoin is currently moving most closely with **{btc_link.index[1]}**.")
        
        st.divider()
        st.subheader("Knowledge Ledger")
        logs = supabase.table("knowledge_ledger").select("*").order("created_at", desc=True).limit(5).execute()
        if logs.data:
            st.table(pd.DataFrame(logs.data)[["asset", "context"]])
        else:
            st.write("No anomalies detected today.")

    with tab3:
        st.subheader("Learning Accuracy")
        perf_data = supabase.table("performance_logs").select("*").order("date").execute()
        if perf_data.data:
            chart_df = pd.DataFrame(perf_data.data)
            fig = px.line(chart_df, x='date', y='error_rate', title="Daily Prediction Error")
            fig.update_traces(line_color='#702963')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("The graph will appear as soon as the first 24h cycle is logged.")

else:
    st.warning("Connecting to global markets... please refresh in a moment.")

st.caption(f"Sync: {datetime.now().strftime('%H:%M')} AEST | Version 1.6.2")
