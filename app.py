import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
from supabase import create_client, Client
import plotly.express as px

# --- 1. SETTINGS & THEME ---
st.set_page_config(page_title="Lavender Lambda Master", page_icon="💜", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #702963; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f0f2f6; border-radius: 10px; padding: 10px 20px; }
    .description-text { color: #555555; font-size: 0.9rem; margin-bottom: 20px; line-height: 1.4; }
    .knowledge-note { background-color: #f9f9fb; border-left: 5px solid #702963; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

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

# --- 3. DATA ENGINE ---
@st.cache_data(ttl=3600)
def get_market_data():
    try:
        df = yf.download(ALL_TICKERS, period="1mo", interval="1d", progress=False)['Close']
        return df.ffill()
    except: return None

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
    st.info("Active Strategy: Sprint 5 (Filtered Learning)")

hist_df = get_market_data()

if hist_df is not None:
    tab1, tab2, tab3 = st.tabs(["📡 Scanner", "🧠 Intelligence", "📈 Scorecard"])

    # --- TAB 1: SCANNER (THE OBSERVE PHASE) ---
    with tab1:
        st.markdown('<p class="description-text"><b>Observe Phase:</b> Monitoring the Circle of Competence for anomalies.</p>', unsafe_allow_html=True)
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
                        st.metric(label, f"${price:,.2f}", f"{delta:.2f}%" if delta != 0 else "Stable")
                    except: st.caption(f"{t} offline")

    # --- TAB 2: INTELLIGENCE (THE REASONING PHASE) ---
    with tab2:
        st.markdown('<p class="description-text"><b>Reasoning Phase:</b> Connecting dots between global assets.</p>', unsafe_allow_html=True)
        corr = hist_df.pct_change().corr()
        if 'BTC-AUD' in corr.columns:
            btc_link = corr['BTC-AUD'].sort_values(ascending=False).index[1]
            st.info(f"**Market Insight:** Bitcoin is currently moving most closely with **{btc_link}**.")
        
        st.divider()
        st.subheader("📓 Knowledge Ledger")
        st.markdown('<div class="knowledge-note"><b>Long-Term Memory:</b> This archives market anomalies (>5%) to build <b>Evidence over Opinion</b>.</div>', unsafe_allow_html=True)
        logs = supabase.table("knowledge_ledger").select("*").order("created_at", desc=True).limit(5).execute()
        if logs.data:
            st.table(pd.DataFrame(logs.data)[["asset", "context"]])

    # --- TAB 3: SCORECARD (THE LEARNING PHASE) ---
    with tab3:
        st.markdown('<p class="description-text"><b>Learning Phase:</b> Self-accountability through accuracy and error tracking.</p>', unsafe_allow_html=True)
        
        # Fetch Scorecard Data
        logs_res = supabase.table("performance_logs").select("*").order("date").execute()
        preds_res = supabase.table("daily_predictions").select("date, confidence").execute()
        
        if logs_res.data:
            df_logs = pd.DataFrame(logs_res.data)
            df_preds = pd.DataFrame(preds_res.data) if preds_res.data else pd.DataFrame(columns=['date', 'confidence'])
            
            # Merge and Clean
            df = pd.merge(df_logs, df_preds, on="date", how="left")
            df['date'] = pd.to_datetime(df['date'])
            df['was_hit'] = df['was_hit'].fillna(False)
            df['hit_int'] = df['was_hit'].astype(int)

            # 1. Error Graph
            st.subheader("↘️ Prediction Error (7-Day Avg)")
            df['error_sma'] = df['error_rate'].rolling(window=7, min_periods=1).mean()
            fig1 = px.line(df, x='date', y='error_sma', markers=True)
            fig1.update_xaxes(tickformat="%d/%m/%y")
            fig1.update_traces(line_color='#702963')
            st.plotly_chart(fig1, use_container_width=True)

            col_a, col_b = st.columns(2)
            with col_a:
                # 2. Accuracy
                st.subheader("↗️ Directional Accuracy")
                acc = (df['hit_int'].sum() / len(df)) * 100
                st.metric("AI Hit Rate", f"{acc:.1f}%")
                st.bar_chart(df.tail(10), x='date', y='hit_int')
            
            with col_b:
                # 3. Strategy Growth
                st.subheader("📈 AI Strategy vs Hold")
                df['returns'] = df['was_hit'].apply(lambda x: 1.02 if x else 0.98).cumprod() * 100000
                fig2 = px.area(df, x='date', y='returns')
                fig2.update_traces(line_color='#4B0082')
                st.plotly_chart(fig2, use_container_width=True)

            # 4. Calibration
            st.divider()
            st.subheader("🎯 Confidence Calibration")
            if 'confidence' in df.columns and df['confidence'].notna().any():
                df['conf_group'] = (df['confidence'].astype(float) * 10).round() / 10
                calib = df.groupby('conf_group')['hit_int'].mean().reset_index()
                st.bar_chart(calib, x='conf_group', y='hit_int')
            else:
                st.info("Confidence data gathering in progress...")
        else:
            st.warning("Robot shift data pending...")

else:
    st.warning("Connecting to global markets...")

st.caption(f"Sync: {datetime.now().strftime('%H:%M')} AEST | Master Dashboard v2.0.4")
