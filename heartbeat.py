import os
import sys
import pandas as pd
import yfinance as yf
from datetime import datetime
from supabase import create_client

def run():
    print("--- 1. ROBOT WAKING UP ---")
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("!!! ERROR: Secrets missing.")
        sys.exit(1)

    try:
        # 1. Connect
        supabase = create_client(url, key)
        print("--- 2. CLOUD CONNECTION SUCCESSFUL ---")
        
        # 2. Assets to track
        tickers = ["BTC-AUD", "ETH-AUD", "NVDA", "SPY", "VAS.AX", "GC=F", "SI=F", "AUDUSD=X", "^TNX"]
        
        # 3. Fetch Market Data
        print("--- 3. FETCHING MARKET DATA ---")
        data = yf.download(tickers, period="7d", interval="1d", progress=False)['Close'].ffill()
        
        if data.empty:
            print("!!! ERROR: No data received.")
            sys.exit(1)
        
        # 4. Calculate Logic
        today = datetime.now().strftime('%Y-%m-%d')
        # We turn the 'List' into a single 'Average Uncertainty' number
        daily_vol = float(data.pct_change().iloc[-1].abs().mean() * 100)
        
        print(f"--- 4. ANALYSIS COMPLETE: Uncertainty is {daily_vol:.2f}% ---")
            
        # 5. SAVE TO SUPABASE (The real goal!)
        print("--- 5. SAVING TO CLOUD BRAIN ---")
        supabase.table("performance_logs").upsert({
            "date": today, 
            "error_rate": round(daily_vol, 2)
        }).execute()
        
        # 6. Check for Anomalies
        last_move = data.pct_change().iloc[-1] * 100
        for ticker, move in last_move.items():
            if abs(move) > 5.0:
                print(f"!!! Anomaly in {ticker}: {move:.2f}%")
                supabase.table("knowledge_ledger").insert({
                    "asset": ticker,
                    "event": "Robot Discovery",
                    "context": f"Detected move of {move:.2f}%"
                }).execute()
        
        print("--- 6. ROBOT SHIFT SUCCESSFUL: DATA SAVED ---")
        
    except Exception as e:
        print(f"!!! CRITICAL CRASH: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run()
