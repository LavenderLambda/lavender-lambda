import pandas as pd
import yfinance as yf
from datetime import datetime
import os
from supabase import create_client

# This script is the 'Robot' version of your app
def run_sync():
    # 1. Setup Connection (GitHub will provide these)
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase = create_client(url, key)

    # 2. Watchlist
    tickers = ["BTC-AUD", "ETH-AUD", "NVDA", "SPY", "VAS.AX", "GC=F", "SI=F", "AUDUSD=X", "^TNX"]

    # 3. Fetch Data
    print(f"Robot waking up at {datetime.now()}...")
    df = yf.download(tickers, period="5d", interval="1d", progress=False)['Close'].ffill()
    
    # 4. Save Performance Log (The Graph)
    today = datetime.now().strftime('%Y-%m-%d')
    daily_vol = df.pct_change().iloc[-1].abs().mean() * 100
    
    supabase.table("performance_logs").upsert({
        "date": today, 
        "error_rate": round(daily_vol, 2)
    }).execute()

    # 5. Save Anomalies (Knowledge Ledger)
    last_move = df.pct_change().iloc[-1] * 100
    for ticker, move in last_move.items():
        if abs(move) > 5.0:
            supabase.table("knowledge_ledger").insert({
                "asset": ticker,
                "event": "Volatility Spike",
                "context": f"Robot detected move of {move:.2f}%"
            }).execute()
            print(f"Anomaly logged for {ticker}")

    print("Sync complete. Robot going back to sleep.")

if __name__ == "__main__":
    run_sync()
