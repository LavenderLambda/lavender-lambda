import os
import sys
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from supabase import create_client

def run_sync():
    print("--- 🧠 INVINCIBLE HEARTBEAT STARTING ---")
    try:
        url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
        key = os.environ.get("SUPABASE_KEY", "").strip()
        supabase = create_client(url, key)

        # 1. FETCH DATA
        print("Fetching market data...")
        # Period 14d handles weekend gaps
        raw_data = yf.download("BTC-AUD", period="14d", interval="1d", progress=False)
        
        if raw_data.empty:
            print("!!! ERROR: No data found.")
            return

        # Ensure we have a single column of Close prices
        if isinstance(raw_data.columns, pd.MultiIndex):
            df = raw_data['Close']['BTC-AUD'].ffill().dropna()
        else:
            df = raw_data['Close'].ffill().dropna()

        # FIX: Explicitly convert to single float values
        today_price = float(df.values[-1])
        yesterday_price = float(df.values[-2])
        actual_move = (today_price - yesterday_price) / yesterday_price
        
        today_str = datetime.now().strftime('%Y-%m-%d')
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        # 2. GRADE YESTERDAY'S WORK
        print(f"Grading logic for {yesterday_str}...")
        try:
            last_pred = supabase.table("daily_predictions").select("*").eq("date", yesterday_str).execute()
            if last_pred.data:
                p = last_pred.data[0]
                was_hit = (actual_move > 0 and p['predicted_direction'] == 1) or \
                          (actual_move < 0 and p['predicted_direction'] == -1) or \
                          (abs(actual_move) < 0.01 and p['predicted_direction'] == 0)
                
                error = abs(actual_move * 100)
                supabase.table("performance_logs").upsert({
                    "date": today_str,
                    "error_rate": round(error, 2),
                    "was_hit": was_hit
                }).execute()
            else:
                error = abs(actual_move * 100)
                supabase.table("performance_logs").upsert({
                    "date": today_str,
                    "error_rate": round(error, 2),
                    "was_hit": False
                }).execute()
        except Exception as e:
            print(f"Grading bypassed: {e}")

        # 3. MAKE TODAY'S PREDICTION
        prediction = 1 if actual_move < -0.02 else (-1 if actual_move > 0.02 else 0)
        confidence = min(abs(actual_move) * 5, 0.90)

        supabase.table("daily_predictions").upsert({
            "date": today_str,
            "asset": "BTC-AUD",
            "predicted_direction": int(prediction),
            "confidence": float(confidence),
            "actual_price_at_prediction": today_price
        }).execute()
        
        print("--- ✅ SUCCESS: ROBOT SHIFT COMPLETE ---")

    except Exception as e:
        print(f"!!! CRITICAL SYSTEM CRASH: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_sync()
