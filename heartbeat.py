import pandas as pd
import yfinance as yf
from datetime import datetime
import os
import sys
from supabase import create_client

def run_sync():
    print("--- STABLE ROBOT SHIFT STARTED ---")
    try:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        
        if not url or "supabase.co" not in url:
            print("CRITICAL ERROR: SUPABASE_URL looks invalid.")
            sys.exit(1)

        supabase = create_client(url, key)

        # Assets
        tickers = ["BTC-AUD", "ETH-AUD", "NVDA", "SPY", "VAS.AX", "GC=F", "SI=F", "AUDUSD=X", "^TNX"]

        # Fetch Data (Using the stable method)
        print("Downloading market data...")
        data = yf.download(tickers, period="1mo", interval="1d", progress=False)
        
        # Pull only the 'Close' prices
        df = data['Close'].ffill()
        
        if df.empty:
            print("ERROR: Download returned no data.")
            return

        # Calculate Performance
        today = datetime.now().strftime('%Y-%m-%d')
        daily_vol = df.pct_change().iloc[-1].abs().mean() * 100
        
        print(f"Success! Market Uncertainty for {today}: {daily_vol:.2f}%")
        
        # Save to Supabase
        supabase.table("performance_logs").upsert({
            "date": today, 
            "error_rate": round(daily_vol, 2)
        }).execute()

        print("--- SHIFT COMPLETE ---")

    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_sync()
