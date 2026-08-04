import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Lavender Intelligence v2.0.3", page_icon="💜", layout="wide")

@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
supabase = init_supabase()

st.title("💜 Lavender Lambda Scorecard")

# 1. FETCH DATA
logs_res = supabase.table("performance_logs").select("*").order("date").execute()
preds_res = supabase.table("daily_predictions").select("date, confidence").execute()

df_logs = pd.DataFrame(logs_res.data) if logs_res.data else pd.DataFrame()
df_preds = pd.DataFrame(preds_res.data) if preds_res.data else pd.DataFrame()

# 2. DATA PROCESSING & SAFETY CHECK
if not df_logs.empty:
    # If we have predictions, merge them. If not, just use logs.
    if not df_preds.empty and 'date' in df_preds.columns:
        df = pd.merge(df_logs, df_preds, on="date", how="left")
    else:
        df = df_logs
        df['confidence'] = None # Placeholder so Chart 4 doesn't break

    df['date'] = pd.to_datetime(df['date'])
    df['was_hit'] = df['was_hit'].fillna(False)
    df['hit_int'] = df['was_hit'].astype(int)
    
    # --- CHART 1: PREDICTION ERROR (7-Day Average) ---
    st.subheader("↘️ Prediction Error (7-Day Avg)")
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
        # Theoretical alpha calculation
        df['returns'] = df['was_hit'].apply(lambda x: 1.02 if x else 0.98).cumprod() * 100000
        fig2 = px.area(df, x='date', y='returns')
        fig2.update_traces(line_color='#4B0082')
        st.plotly_chart(fig2, use_container_width=True)

    # --- CHART 4: CONFIDENCE CALIBRATION ---
    st.divider()
    st.subheader("🎯 Confidence Calibration")
    
    if 'confidence' in df.columns and df['confidence'].notna().any():
        df['conf_group'] = (df['confidence'].astype(float) * 10).round() / 10
        calib = df.groupby('conf_group')['hit_int'].mean().reset_index()
        fig3 = px.bar(calib, x='conf_group', y='hit_int', 
                     labels={'conf_group': 'AI Confidence Level', 'hit_int': 'Actual Win Rate'})
        fig3.update_traces(marker_color='#E6E6FA')
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("🤖 **Robot Note:** I haven't logged any confidence data yet. Chart will appear after my first shift.")

else:
    st.warning("Scorecard is empty. The Robot needs to complete one shift to populate the data.")

st.caption(f"v2.0.3 Build | Sydney, AU")
