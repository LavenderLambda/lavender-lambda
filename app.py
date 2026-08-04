import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Lavender Intelligence v2.0", page_icon="💜", layout="wide")

@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
supabase = init_supabase()

st.title("💜 Lavender Lambda Scorecard")
st.markdown("### Evidence-Based Performance Tracking")

# FETCH DATA FROM SUPABASE
logs_res = supabase.table("performance_logs").select("*").order("date").execute()
df = pd.DataFrame(logs_res.data) if logs_res.data else pd.DataFrame()

if not df.empty:
    df['date'] = pd.to_datetime(df['date'])
    
    # --- CHART 1: PREDICTION ERROR (7-Day Average) ---
    st.subheader("↘️ Prediction Error (7-Day Avg)")
    df['error_sma'] = df['error_rate'].rolling(window=7).mean()
    fig1 = px.line(df, x='date', y='error_sma', title="Aiming for the Bottom")
    fig1.update_traces(line_color='#702963')
    st.plotly_chart(fig1, use_container_width=True)

    col1, col2 = st.columns(2)
    
    with col1:
        # --- CHART 2: DIRECTIONAL ACCURACY ---
        st.subheader("↗️ Directional Accuracy")
        hits = df['was_hit'].sum()
        total = len(df)
        accuracy = (hits / total) * 100
        st.metric("Total Hit Rate", f"{accuracy:.1f}%", delta=f"{hits}/{total} Days")
        
        # Mini bar chart for hit consistency
        df['hit_int'] = df['was_hit'].astype(int)
        st.bar_chart(df.tail(14), x='date', y='hit_int')

    with col2:
        # --- CHART 3: BUY & HOLD COMPARISON ---
        st.subheader("📈 AI Alpha vs Buy & Hold")
        # Logic: We calculate a simulated 'Alpha' based on accuracy
        df['ai_returns'] = df['was_hit'].apply(lambda x: 1.02 if x else 0.98).cumprod() * 100000
        fig2 = px.area(df, x='date', y='ai_returns', title="Simulated Growth ($100k AUD Start)")
        st.plotly_chart(fig2, use_container_width=True)

    # --- CHART 4: CONFIDENCE CALIBRATION ---
    st.divider()
    st.subheader("🎯 Confidence Calibration")
    st.caption("Are high-confidence predictions actually more accurate?")
    # For MVP, we show the link between confidence and current results
    st.info("Gathering enough prediction samples to calibrate confidence curves...")

else:
    st.warning("Scorecard is empty. The Robot needs 48 hours of Shift Data to start the story.")

st.caption(f"v2.0 Build | Managed by {st.secrets.get('USER_NAME', 'Founder')} | Sydney, AU")
