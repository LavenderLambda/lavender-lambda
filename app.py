import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import sqlite3

# --- 1. MOBILE PAGE CONFIG ---
st.set_page_config(page_title="Lavender Lambda", page_icon="💜", layout="centered")

# Custom CSS for a Mobile Dashboard look
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; font-weight: bold; }
    .stMetric { background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
    div[data-testid="stMetricValue"] { color: #4B0082; }
    button[kind="primary"] { background-color: #ff4b4b !important; color: white !important; border: None; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('lavender.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS system_state (id INTEGER PRIMARY KEY, override BOOLEAN)''')
    c.execute('INSERT OR IGNORE INTO system_state (id, override) VALUES (1, 0)')
    conn.commit()
    return conn

conn = init_db()

# --- 3. LOGIC ---
def get_status():
    res = conn.execute('SELECT override FROM system_state WHERE id=1').fetchone()
    return "INACTIVE" if res[0] else "ACTIVE"

def toggle_override():
    current = conn.execute('SELECT override FROM system_state WHERE id=1').fetchone()[0]
    conn.execute('UPDATE system_state SET override = ? WHERE id=1', (0 if current else 1,))
    conn.commit()

# --- 4. UI ---
st.title("💜 Lavender Lambda v1.0")
status = get_status()

if status == "ACTIVE":
    if st.button("🚨 GLOBAL OVERRIDE (SHUT DOWN)", type="primary"):
        toggle_override()
        st.rerun()
else:
    if st.button("✅ RE-ACTIVATE SYSTEM"):
        toggle_override()
        st.rerun()

st.subheader("Intelligence Dashboard (AUD)")
col1, col2 = st.columns(2)

# Fetch Real-time Data
try:
    data = yf.download("BTC-AUD", period="2d", interval="1d")
    price = data['Close'].iloc[-1]
    prev_price = data['Close'].iloc[-2]
    delta = ((price - prev_price) / prev_price) * 100
except:
    price, delta = 0, 0

with col1:
    st.metric("BTC Price", f"${price:,.0f} AUD", f"{delta:.2f}%")
with col2:
    st.metric("System Status", status)

st.divider()
if abs(delta) < 2:
    st.info("**AI Recommendation:** HOLD / NO ACTION")
else:
    st.success("**AI Recommendation:** Market movement detected. Analyzing...")

tab1, tab2 = st.tabs(["Knowledge", "Portfolio"])
with tab1:
    st.write("Historical Patterns Detected:")
    st.write("- 2024-07-15: Bullish Surge (+5.4%)")
with tab2:
    st.write("Balance: **$100,000.00 AUD**")
