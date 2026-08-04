import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Lavender Intelligence v2.0.2", page_icon="💜", layout="wide")

@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
supabase = init_supabase()

st.title("💜 Lavender Lambda Scorecard")

# 1. FETCH AND MERGE DATA
# We need both tables to see the 'Confidence' vs the 'Result'
logs_res = supabase.table("performance_logs").select("*").order("date").execute()
preds_res = supabase.table("daily_predictions").select("date, confidence").execute()

df_logs = pd.DataFrame(logs_res.data) if logs_res.data else pd.DataFrame()
df_preds = pd.DataFrame(preds_res.data) if preds_res.data else pd.DataFrame()

if not df_logs.empty:
    # Merge the two tables so we can compare Confidence to Was_Hit
    df = pd.merge(df_logs, df_preds, on="date", how="left")
    df['date'] = pd.to_datetime(df['date'])
    df['was_hit'] = df['was_hit'].fillna(False)
    df['hit_int'] = df['was_hit'].astype(int)
    
    # --- CHART 1: PREDICTION ERROR (7-Day Average) ---
    st.subheader("↘️ Prediction Error (7-Day Avg)")
    st.caption("Measuring the gap between AI expectations and market reality.")
    df['error_sma'] = df['error_rate'].rolling(window=7, min_periods=1).mean()
    fig1 = px.line(df, x='date', y='error_sma', markers=True)
    fig1.update_traces(line_color='#702963')
    st.plotly_chart(fig1, use_container_width=True)

    col1, col2 = st.columns(2)
    
    with col1:
        # --- CHART 2: DIRECTIONAL ACCURACY ---
        st.subheader("↗️ Directional Accuracy")
        accuracy = (df['hit_int'].sum() / len(df)) * 100
        st.metric("Overall Hit Rate", f"{accuracy:.1f}%")
        st.bar_chart(df.tail(10), x='date', y='hit_int')

    with col2:
        # --- CHART 3: STRATEGY GROWTH ---
        st.subheader("📈 Cumulative Return vs Hold")
        # Theoretical alpha: +2% for correct, -2% for wrong
        df['returns'] = df['was_hit'].apply(lambda x: 1.02 if x else 0.98).cumprod() * 100000
        fig2 = px.area(df, x='date', y='returns')
        fig2.update_traces(line_color='#4B0082')
        st.plotly_chart(fig2, use_container_width=True)

    # --- CHART 4: CONFIDENCE CALIBRATION ---
    st.divider()
    st.subheader("🎯 Confidence Calibration")
    st.markdown('<p style="color: #555;">Are high-confidence predictions actually more accurate?</p>', unsafe_allow_html=True)
    
    if 'confidence' in df.columns and not df['confidence'].isna().all():
        # We group by confidence levels to see hit rate
        df['conf_group'] = (df['confidence'] * 10).round() / 10
        calib = df.groupby('conf_group')['hit_int'].mean().reset_index()
        
        fig3 = px.bar(calib, x='conf_group', y='hit_int', 
                     labels={'conf_group': 'AI Confidence Level', 'hit_int': 'Actual Win Rate'},
                     title="Calibration Curve (Target: Win Rate = Confidence)")
        fig3.update_traces(marker_color='#E6E6FA')
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Gathering confidence metrics from the robot... results appearing in 24h.")

else:
    st.warning("Scorecard is waiting for the robot's first v2.0 entry (Tomorrow morning).")

st.caption(f"v2.0.2 | Sydney, AU")
