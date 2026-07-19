import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
from supabase import create_client, Client
import plotly.express as px

# --- 1. SETTINGS & THEME ---
st.set_page_config(page_title="Lavender Intelligence", page_icon="💜", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #702963; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #f0f2f6; border-radius: 10px; padding: 10px 20px; 
    }
    .description-text { color: #555555; font-size: 0.9rem; margin-bottom: 20px; line-height: 1.4; }
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
        return df.ffill()
    except: return None

def auto_log_performance(df):
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        check = supabase.table("performance_logs").select("date").eq("date", today).execute()
        if not check.data:
            daily_vol = df.pct_change().iloc[-1].abs().mean() * 100
            supabase.table("performance_logs").insert({"date": today, "error_rate": daily_vol}).execute()
    except: pass

# --- 4. UI LAYOUT ---
st.title("💜 Lavender Lambda")

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
    st.write("Current Risk Limit: **20%**")

hist_df = get_clean_data()

if hist_df is not None:
    auto_log_performance(hist_df)
    
    tab1, tab2, tab3 = st.tabs(["📡 Scanner", "🧠 Intelligence", "📈 Performance"])

    with tab1:
        st.markdown('<p class="description-text"><b>The "Observe" Phase:</b> The AI monitors these assets for significant movements (Deltas) that require investigation.</p>', unsafe_allow_html=True)
        for sector, tickers in WATCHLIST.items():
            st.subheader(sector)
            cols = st.columns(len(tickers))
            for i, t in enumerate(tickers):
                with cols[i].container(border=True):
                    try:
                        price = hist_df[t].iloc[-1]
                        prev = hist_df[t].iloc[-2]
                        delta = ((price - prev) / prev) * 100
                        label = t.replace("-AUD", "").replace("=F", "").replace(".AX", "")
                        if pd.isna(delta) or delta == 0:
                            st.metric(label, f"${price:,.2f}", "Closed")
                        else:
                            st.metric(label, f"${price:,.2f}", f"{delta:.2f}%")
                    except:
                        st.caption(f"{t} offline")

    with tab2:
        st.markdown('<p class="description-text"><b>The "Reasoning" Phase:</b> The AI identifies relationships between assets and matches behavior against historical lessons.</p>', unsafe_allow_html=True)
        st.subheader("Inter-market Analysis")
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
            st.write("Awaiting first major market anomaly...")

    with tab3:
        st.markdown('<p class="description-text"><b>The "Learning" Phase:</b> This tracks the AI’s prediction error. A downward-sloping line indicates the system is getting smarter.</p>', unsafe_allow_html=True)
        st.subheader("System Learning Curve")
        perf_data = supabase.table("performance_logs").select("*").order("date").execute()
        if perf_data.data:
            chart_df = pd.DataFrame(perf_data.data)
            # Ensure date is a datetime object for clean formatting
            chart_df['date'] = pd.to_datetime(chart_df['date'])
            
            fig = px.line(chart_df, x='date', y='error_rate', title="Daily Prediction Error")
            # Force the X-axis to show DD/MM/YY
            fig.update_xaxes(
                tickformat="%d/%m/%y",
                dtick="D1", # Ensures a tick for every day
                title_text="Date"
            )
            fig.update_yaxes(title_text="Error %")
            fig.update_traces(line_color='#702963', mode='lines+markers')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Performance data logging in progress...")

else:
    st.warning("Connecting to global markets...")

st.caption(f"Sync: {datetime.now().strftime('%H:%M')} AEST | Cloud Connected | v1.6.4")
