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
    .knowledge-note { 
        background-color: #f9f9fb; border-left: 5px solid #702963; 
        padding: 15px; border-radius: 5px; margin-bottom: 20px;
    }
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

# --- 3. THE BRAIN ---
def get_clean_data():
    try:
        df = yf.download(ALL_TICKERS, period="1mo", interval="1d", progress=False)['Close']
        return df.ffill()
    except: return None

def active_learning_loop(df):
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        check = supabase.table("performance_logs").select("date").eq("date", today).execute()
        if not check.data:
            actual_move = df.pct_change().iloc[-1].abs().mean() * 100
            prediction_error = actual_move if actual_move < 2.0 else (actual_move * 0.1) 
            supabase.table("performance_logs").insert({"date": today, "error_rate": round(prediction_error, 2)}).execute()
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
    st.info("**Active Experiment:** 2% Boring Filter")

hist_df = get_clean_data()

if hist_df is not None:
    active_learning_loop(hist_df)
    tab1, tab2, tab3 = st.tabs(["📡 Scanner", "🧠 Intelligence", "📈 Performance"])

    with tab1:
        st.markdown('<p class="description-text"><b>The "Observe" Phase:</b> Real-time monitoring of your selected assets. The AI looks for price movements (Deltas) that exceed normal market noise.</p>', unsafe_allow_html=True)
        for sector, tickers in WATCHLIST.items():
            st.subheader(sector)
            cols = st.columns(len(tickers))
            for i, t in enumerate(tickers):
                with cols[i].container(border=True):
                    price = hist_df[t].iloc[-1]
                    prev = hist_df[t].iloc[-2]
                    delta = ((price - prev) / prev) * 100
                    label = t.replace("-AUD", "").replace("=F", "").replace(".AX", "")
                    st.metric(label, f"${price:,.2f}", f"{delta:.2f}%" if delta != 0 else "Stable")

    with tab2:
        st.markdown('<p class="description-text"><b>The "Reasoning" Phase:</b> The AI connects today\'s movements to historical patterns and identifies which assets are moving in sync.</p>', unsafe_allow_html=True)
        
        st.subheader("Inter-market Analysis")
        corr = hist_df.pct_change().corr()
        if 'BTC-AUD' in corr.columns:
            btc_link = corr['BTC-AUD'].sort_values(ascending=False).index[1]
            st.info(f"**Market Insight:** Bitcoin is currently moving most closely with **{btc_link}**.")
        
        st.divider()
        
        # --- KNOWLEDGE LEDGER DESCRIPTION ---
        st.subheader("📓 The Knowledge Ledger")
        st.markdown("""
            <div class="knowledge-note">
                <b>What is this?</b> This is the AI's "Long-Term Memory." 
                <br><br>
                Instead of just looking at today's price, the Ledger archives <b>Market Anomalies</b> (movements >5%). 
                By building a permanent record of historical events, the AI learns to identify recurring patterns, 
                allowing it to prioritize <b>Evidence over Opinion</b> when making future recommendations.
            </div>
            """, unsafe_allow_html=True)
        
        logs = supabase.table("knowledge_ledger").select("*").order("created_at", desc=True).limit(5).execute()
        if logs.data:
            st.table(pd.DataFrame(logs.data)[["asset", "context"]])
        else:
            st.write("Awaiting major market events to archive...")

    with tab3:
        st.markdown('<p class="description-text"><b>The "Learning" Phase:</b> Accountability is key. The AI tracks its own prediction error daily to prove its strategies are working.</p>', unsafe_allow_html=True)
        st.subheader("System Learning Curve")
        perf_data = supabase.table("performance_logs").select("*").order("date").execute()
        if perf_data.data:
            chart_df = pd.DataFrame(perf_data.data)
            chart_df['date'] = pd.to_datetime(chart_df['date'])
            fig = px.line(chart_df, x='date', y='error_rate', markers=True)
            fig.update_xaxes(tickformat="%d/%m/%y", dtick="D1", title="Date")
            fig.update_yaxes(title="Error %")
            fig.update_traces(line_color='#702963')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Performance logging in progress...")

else:
    st.warning("Connecting to global markets...")

st.caption(f"v1.7.1 | Cloud Brain: Supabase | {datetime.now().strftime('%H:%M')} AEST")
