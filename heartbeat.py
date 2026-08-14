import os
import sys
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from supabase import create_client

def run_sync():
    print("--- 🧠 HYPER-ROBUST HEARTBEAT STARTING ---")
    try:
        url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
        key = os.environ.get("SUPABASE_KEY", "").strip()
        supabase = create_client(url, key)

        # 1. FETCH DATA (Extended buffer)
        print("Fetching market data...")
        raw_data = yf.download("BTC-AUD", period="14d", interval="1d", progress=False)
        
        if raw_data.empty:
            print("!!! ERROR: No data found.")
            return

        # 2. DATA CRUSHER: Force data into a predictable format
        # This handles the 'Series' error by flattening everything to a list of numbers
        if 'Close' in raw_data.columns:
            close_data = raw_data['Close']
        else:
            # Handles 'MultiIndex' if yfinance returns (Close, BTC-AUD)
            close_data = raw_data.xs('Close', axis=1, level=0)
            
        # Convert to a flat list of prices, ignoring labels
        prices = close_data.values.flatten()
        # Filter out any 'NaN' values
        prices = [p for p in prices if pd.notmd(p) and p > 0]

        if len(prices) < 2:
            print("!!! ERROR: Not enough price points found.")
            return

        today_price = float(prices[-1])
        yesterday_price = float(prices[-2])
        actual_move = (today_price - yesterday_price) / yesterday_price
        
        today_str = datetime.now().strftime('%Y-%m-%d')
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        print(f"Price Analysis: Today ${today_price:,.2f} | Move: {actual_move:.2%}")

        # 3. GRADE YESTERDAY'S WORK
        try:
            print(f"Looking for prediction from {yesterday_str}...")
            last_pred = supabase.table("daily_predictions").select("*").eq("date", yesterday_str).execute()
            
            # Default values
            was_hit = False
            
            if last_pred.data:
                p = last_pred.data[0]
                was_hit = (actual_move > 0 and p['predicted_direction'] == 1) or \
                          (actual_move < 0 and p['predicted_direction'] == -1) or \
                          (abs(actual_move) < 0.01 and p['predicted_direction'] == 0)
                print(f"Prediction found! Hit: {was_hit}")

            # Record performance
            supabase.table("performance_logs").upsert({
                "date": today_str,
                "error_rate": round(abs(actual_move * 100), 2),
                "was_hit": was_hit
            }).execute()
            print("Performance Log updated.")
        except Exception as e:
            print(f"Grading bypassed: {e}")

        # 4. MAKE TODAY'S PREDICTION
        # Simple Contrarian: If down > 2%, predict bounce (1). Else if up > 2% predict drop (-1).
        prediction = 1 if actual_move < -0.02 else (-1 if actual_move > 0.02 else 0)
        confidence = 0.5 # Baseline confidence

        supabase.table("daily_predictions").upsert({
            "date": today_str,
            "asset": "BTC-AUD",
            "predicted_direction": int(prediction),
            "confidence": float(confidence),
            "actual_price_at_prediction": today_price
        }).execute()
        
        print(f"Today's prediction ({prediction}) saved to Cloud Brain.")
        print("--- ✅ SUCCESS: ROBOT SHIFT COMPLETE ---")

    except Exception as e:
        print(f"!!! CRITICAL CRASH: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Helper to fix pandas issues
    import numpy as np
    pd.notmd = np.isreal 
    run_sync()
