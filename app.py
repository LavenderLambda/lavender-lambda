import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
from supabase import create_client, Client
import plotly.express as px

# --- 1. SETTINGS & THEME ---
st.set_page_config(page_title="Lavender Master & Creator", page_icon="💜", layout="wide")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #702963; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f0f2f6; border-radius: 10px; padding: 10px 20px; }
    .script-box { background-color: #f1f1f1; padding: 20px; border-radius: 15px; border: 1px solid #702963; font-family: 'Helvetica'; line-height: 1.6; }
    .visual-cue { color: #702963; font-weight: bold; font-size: 0.8rem; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
supabase = init_supabase()

# --- 2. DATA ENGINE ---
WATCHLIST = {
    "💎 Crypto": ["BTC-AUD", "ETH-AUD"],
    "📈 Equities": ["NVDA", "SPY", "VAS.AX"],
    "📀 Commodities": ["GC=F", "SI=F"],
    "🌏 Macro": ["AUDUSD=X", "^TNX"]
}
ALL_TICKERS = [t for sub in WATCHLIST.values() for t in sub]

@st.cache_data(ttl=3600)
def get_market_data():
    try:
        df = yf.download(ALL_TICKERS, period="1mo", interval="1d", progress=False)['Close']
        return df.ffill()
    except: return None

# --- 3. UI LAYOUT ---
st.title("💜 Lavender Lambda")

hist_df = get_market_data()

if hist_df is not None:
    tab1, tab2, tab3, tab4 = st.tabs(["📡 Scanner", "🧠 Intelligence", "📈 Scorecard", "🎬 Creator Studio"])

    # --- TAB 1 & 2 & 3 (Keeping previous logic) ---
    with tab1:
        for sector, tickers in WATCHLIST.items():
            st.subheader(sector)
            cols = st.columns(len(tickers))
            for i, t in enumerate(tickers):
                with cols[i].container(border=True):
                    price = hist_df[t].iloc[-1]
                    prev = hist_df[t].iloc[-2]
                    delta = ((price - prev) / prev) * 100
                    label = t.replace("-AUD", "").replace("=F", "").replace(".AX", "")
                    st.metric(label, f"${price:,.2f}", f"{delta:.2f}%")

    with tab2:
        corr = hist_df.pct_change().corr()
        btc_link = corr['BTC-AUD'].sort_values(ascending=False).index[1]
        st.info(f"**Market Insight:** Bitcoin is currently tracking **{btc_link}**.")
        st.subheader("📓 Knowledge Ledger")
        logs = supabase.table("knowledge_ledger").select("*").order("created_at", desc=True).limit(5).execute()
        if logs.data: st.table(pd.DataFrame(logs.data)[["asset", "context"]])

    with tab3:
        logs_res = supabase.table("performance_logs").select("*").order("date").execute()
        if logs_res.data:
            df_l = pd.DataFrame(logs_res.data)
            df_l['date'] = pd.to_datetime(df_l['date'])
            fig1 = px.line(df_l, x='date', y='error_rate', markers=True, title="Prediction Error (Accuracy Tracking)")
            fig1.update_traces(line_color='#702963')
            st.plotly_chart(fig1, use_container_width=True)
        else: st.warning("Data pending...")

    # --- TAB 4: CREATOR STUDIO (THE SCRIPT GENERATOR) ---
    with tab4:
        st.subheader("🤳 Daily Content Script")
        st.markdown("Use this script for your daily TikTok or Instagram Reel. Aim for 45-60 seconds.")
        
        # Pull latest intelligence for the script
        btc_price = hist_df['BTC-AUD'].iloc[-1]
        btc_delta = ((btc_price - hist_df['BTC-AUD'].iloc[-2]) / hist_df['BTC-AUD'].iloc[-2]) * 100
        corr = hist_df.pct_change().corr()
        btc_link = corr['BTC-AUD'].sort_values(ascending=False).index[1].replace("-AUD","").replace("=F","")
        
        # Dynamic Script logic
        sentiment = "surging" if btc_delta > 1 else ("dropping" if btc_delta < -1 else "sideways")
        
        script = f"""
        <div class="script-box">
            <span class="visual-cue">[SCENE 1: HOOK - 0:00-0:05]</span><br>
            "Bitcoin in AUD is currently {sentiment}, trading at ${btc_price:,.0f}. But the numbers aren't the real story today."
            <br><br>
            <span class="visual-cue">[SCENE 2: THE EVIDENCE - 0:05-0:20 - POINT TO SCANNER TAB]</span><br>
            "My AI scanner just flagged a movement of {btc_delta:.2f}% in the last 24 hours. While the crowd is guessing, my 'Lavender' engine is looking at the raw evidence."
            <br><br>
            <span class="visual-cue">[SCENE 3: THE INTELLIGENCE - 0:20-0:40 - SHOW INTELLIGENCE TAB]</span><br>
            "Here's the real alpha: BTC is currently moving in lockstep with <b>{btc_link}</b>. We are seeing a 30-day correlation shift that most retail traders are completely missing."
            <br><br>
            <span class="visual-cue">[SCENE 4: THE SCORECARD - 0:40-0:55 - SHOW SCORECARD GRAPH]</span><br>
            "This isn't a gut feeling. Our prediction error is currently trending on the scorecard, proving the AI is learning the Australian market rhythm. We're building evidence, not opinions."
            <br><br>
            <span class="visual-cue">[SCENE 5: CALL TO ACTION - 0:55-1:00]</span><br>
            "Want to see the full intelligence ledger? Drop a comment or follow for the daily heartbeat."
        </div>
        """
        st.markdown(script, unsafe_allow_html=True)
        
        st.divider()
        st.subheader("💡 Creator Pro-Tips")
        st.write("1. **The Hook:** Make sure the first 3 seconds are fast and loud.")
        st.write("2. **Visuals:** Use the 'Green Screen' effect on TikTok to show your Lavender Lambda dashboard behind you.")
        st.write("3. **Consistency:** Post at the same time every day after the robot finishes its shift (10:30 AM AEST).")

else:
    st.warning("Connecting to global markets...")

st.caption(f"Sync: {datetime.now().strftime('%H:%M')} AEST | Master Dashboard v2.1.0")
