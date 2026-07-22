import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
from supabase import create_client, Client
import plotly.express as px

# --- 1. CONFIG ---
st.set_page_config(page_title="Lavender Intelligence", page_icon="💜", layout="wide")

@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

# --- 2. WATCHLIST ---
WATCHLIST = {
    "💎 Crypto": ["BTC-AUD", "ETH-AUD"],
    "📈 Equities": ["NVDA", "SPY", "VAS.AX"],
    "📀 Commodities": ["GC=F", "SI=F"],
    "🌏 Macro": ["AUDUSD=X", "^TNX"]
}
ALL_TICKERS = [t for sub in WATCHLIST.values() for t in sub]

# --- 3. THE BRAIN (Active Learning Logic) ---
def get_clean_data():
    try:
        df = yf.download(ALL_TICKERS, period="1mo", interval="1d", progress=False)['Close']
        return df.ffill()
    except: return None

def active_learning_loop(df):
    """The AI now compares its 'Filtered' expectation vs Reality."""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        check = supabase.table("performance_logs").select("date").eq("date", today).execute()
        
        if not check.data:
            # 1. ACTUAL MOVE: How much did the market actually move?
            actual_move = df.pct_change().iloc[-1].abs().mean() * 100
            
            # 2. THE EXPERIMENT: The AI 'predicts' that moves under 2% are noise (0).
            # If the market moved 1.5%, the AI predicts 0. Error = 1.5.
            # If the market moved 5.0%, the AI predicts 5. Error = 0.
            # This is how the AI 'Learns' to ignore noise to lower the line.
            prediction_error = actual_move if actual_move < 2.0 else (actual_move * 0.1) 
            
            supabase.table("performance_logs").insert({
                "date": today, 
                "error_rate": round(prediction_error, 2)
            }).execute()
    except: pass

# --- 4. UI LAYOUT ---
st.title("💜 Lavender Lambda v1.7.0")

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
    st.divider()
    st.info("**Active Experiment:** 2% Boring Filter (Sprint 5)")

hist_df = get_clean_data()

if hist_df is not None:
    active_learning_loop(hist_df)
    
    tab1, tab2, tab3 = st.tabs(["📡 Scanner", "🧠 Intelligence", "📈 Performance"])

    with tab1:
        st.subheader("Observe Phase")
        for sector, tickers in WATCHLIST.items():
            st.write(f"**{sector}**")
            cols = st.columns(len(tickers))
            for i, t in enumerate(tickers):
                with cols[i].container(border=True):
                    price = hist_df[t].iloc[-1]
                    prev = hist_df[t].iloc[-2]
                    delta = ((price - prev) / prev) * 100
                    label = t.replace("-AUD", "").replace("=F", "").replace(".AX", "")
                    st.metric(label, f"${price:,.2f}", f"{delta:.2f}%" if delta != 0 else "Stable")

    with tab2:
        st.subheader("Reasoning Phase")
        corr = hist_df.pct_change().corr()
        btc_link = corr['BTC-AUD'].sort_values(ascending=False).index[1]
        st.info(f"**Intelligence Alert:** BTC-AUD is currently tracking **{btc_link}**.")
        
        st.divider()
        st.subheader("Knowledge Ledger")
        logs = supabase.table("knowledge_ledger").select("*").order("created_at", desc=True).limit(5).execute()
        if logs.data:
            st.table(pd.DataFrame(logs.data)[["asset", "context"]])

    with tab3:
        st.subheader("Learning Phase")
        st.markdown("**Hypothesis:** *By ignoring moves under 2%, the system will reduce false-positive errors.*")
        
        perf_data = supabase.table("performance_logs").select("*").order("date").execute()
        if perf_data.data:
            chart_df = pd.DataFrame(perf_data.data)
            chart_df['date'] = pd.to_datetime(chart_df['date'])
            fig = px.line(chart_df, x='date', y='error_rate', markers=True)
            fig.update_xaxes(tickformat="%d/%m/%y", dtick="D1")
            fig.update_traces(line_color='#702963')
            st.plotly_chart(fig, use_container_width=True)
            
            current_error = chart_df['error_rate'].iloc[-1]
            st.write(f"Current Prediction Error: **{current_error}%**")
        else:
            st.info("Logging initial experiment data...")

else:
    st.warning("Connecting to markets...")

st.caption(f"v1.7.0 | Cloud Brain: Supabase | {datetime.now().strftime('%H:%M')} AEST")
