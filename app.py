import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Lavender Intelligence v2.0.1", page_icon="💜", layout="wide")

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
    
    # --- FIX: Handle Empty (NULL) values in old data ---
    # We fill empty boxes with False (0) so the computer doesn't crash
    df['was_hit'] = df['was_hit'].fillna(False)
    df['hit_int'] = df['was_hit'].astype(int)

    # --- CHART 1: PREDICTION ERROR (7-Day Average) ---
    st.subheader("↘️ Prediction Error (7-Day Avg)")
    df['error_sma'] = df['error_rate'].rolling(window=7, min_periods=1).mean()
    fig1 = px.line(df, x='date', y='error_sma', title="Aiming for lower uncertainty")
    fig1.update_traces(line_color='#702963')
    st.plotly_chart(fig1, use_container_width=True)

    col1, col2 = st.columns(2)
    
    with col1:
        # --- CHART 2: DIRECTIONAL ACCURACY ---
        st.subheader("↗️ Directional Accuracy")
        hits = df['hit_int'].sum()
        total = len(df)
        accuracy = (hits / total) * 100
        st.metric("Current Accuracy", f"{accuracy:.1f}%", delta=f"{hits} Correct")
        
        # Mini bar chart for hit consistency
        st.bar_chart(df.tail(14), x='date', y='hit_int')

    with col2:
        # --- CHART 3: AI PERFORMANCE vs BASELINE ---
        st.subheader("📈 Cumulative Strategy Growth")
        # Start everyone at $100k
        # Logic: If AI is correct, +2%. If wrong, -2%. 
        # (This is a simulation of the 'Learning Strategy')
        df['ai_returns'] = df['was_hit'].apply(lambda x: 1.02 if x else 0.98).cumprod() * 100000
        fig2 = px.area(df, x='date', y='ai_returns', title="Simulated $100k Portfolio")
        fig2.update_traces(line_color='#4B0082')
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.info("💡 **Founder Note:** The system is currently in 'Calibration Mode.' As the robot logs more predictions, these charts will begin to reveal the AI's true learning curve.")

else:
    st.warning("Scorecard is empty. The Robot needs a 24-hour cycle to log its first v2.0 entry.")

st.caption(f"v2.0.1 Build | Sydney, AU | Cloud Connected")
