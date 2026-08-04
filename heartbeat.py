import os
import sys
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from supabase import create_client

def run_sync():
    print("--- 🧠 INTELLIGENCE HEARTBEAT STARTING ---")
    url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    key = os.environ.get("SUPABASE_KEY", "").strip()
    supabase = create_client(url, key)

    # 1. FETCH DATA (BTC-AUD as the benchmark)
    data = yf.download("BTC-AUD", period="7d", interval="1d", progress=False)['Close'].ffill()
    today_price = float(data.iloc[-1])
    yesterday_price = float(data.iloc[-2])
    actual_move = (today_price - yesterday_price) / yesterday_price
    today_str = datetime.now().strftime('%Y-%m-%d')
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    # 2. GRADE YESTERDAY'S PREDICTION
    try:
        last_pred = supabase.table("daily_predictions").select("*").eq("date", yesterday_str).execute()
        if last_pred.data:
            p = last_pred.data[0]
            # Was the AI right about direction?
            was_hit = (actual_move > 0 and p['predicted_direction'] == 1) or \
                      (actual_move < 0 and p['predicted_direction'] == -1) or \
                      (abs(actual_move) < 0.01 and p['predicted_direction'] == 0)
            
            error = abs(actual_move * 100) # Simple error %
            
            # Save the result
            supabase.table("performance_logs").upsert({
                "date": today_str,
                "error_rate": round(error, 2),
                "was_hit": was_hit
            }).execute()
            print(f"Yesterday graded. Hit: {was_hit}, Error: {error:.2f}%")
    except Exception as e: print(f"Grading skipped: {e}")

    # 3. MAKE TODAY'S PREDICTION (The 'Reasoning')
    # Simple logic: If market moved >2%, predict a partial reversal (Contrarian)
    # This is what we will 'improve' over time.
    move_pct = (today_price - yesterday_price) / yesterday_price
    prediction = -1 if move_pct > 0.02 else (1 if move_pct < -0.02 else 0)
    confidence = min(abs(move_pct) * 10, 0.95) # Higher move = higher confidence

    supabase.table("daily_predictions").upsert({
        "date": today_str,
        "asset": "BTC-AUD",
        "predicted_direction": int(prediction),
        "confidence": float(confidence),
        "actual_price_at_prediction": today_price
    }).execute()
    
    print(f"--- ✅ SHIFT COMPLETE: Prediction for tomorrow logged. ---")

if __name__ == "__main__":
    run_sync()
