import os
import sys
import pandas as pd
import yfinance as yf
from datetime import datetime
from supabase import create_client

def run():
    print("--- 1. ROBOT WAKING UP ---")
    
    # Fetch and CLEAN the URL and Key
    raw_url = os.environ.get("SUPABASE_URL", "")
    raw_key = os.environ.get("SUPABASE_KEY", "")
    
    # .strip() removes spaces, .rstrip("/") removes the trailing slash
    url = raw_url.strip().rstrip("/")
    key = raw_key.strip()
    
    if not url or "https" not in url:
        print(f"!!! ERROR: URL looks wrong. Found: {url}")
        sys.exit(1)

    try:
        # 1. Connect
        supabase = create_client(url, key)
        print("--- 2. CLOUD CONNECTION INITIALIZED ---")
        
        # 2. Assets
        tickers = ["BTC-AUD", "ETH-AUD", "NVDA", "SPY", "VAS.AX", "GC=F", "SI=F", "AUDUSD=X", "^TNX"]
        
        # 3. Fetch Market Data
        print("--- 3. FETCHING MARKET DATA ---")
        data = yf.download(tickers, period="7d", interval="1d", progress=False)['Close'].ffill()
        
        if data.empty:
            print("!!! ERROR: No market data received.")
            sys.exit(1)
        
        # 4. Calculate
        today = datetime.now().strftime('%Y-%m-%d')
        daily_vol = float(data.pct_change().iloc[-1].abs().mean() * 100)
        print(f"--- 4. ANALYSIS COMPLETE: Uncertainty is {daily_vol:.2f}% ---")
            
        # 5. SAVE TO SUPABASE
        print(f"--- 5. ATTEMPTING SAVE TO: {url} ---")
        # We perform a small select first to test the 'Road' to the database
        supabase.table("system_state").select("*").limit(1).execute()
        
        # Now save the performance log
        supabase.table("performance_logs").upsert({
            "date": today, 
            "error_rate": round(daily_vol, 2)
        }).execute()
        
        print("--- 6. ROBOT SHIFT SUCCESSFUL: DATA SAVED ---")
        
    except Exception as e:
        print(f"!!! CRITICAL CRASH: {str(e)}")
        print("TIP: Ensure SUPABASE_URL in GitHub starts with https:// and has no extra slashes at the end.")
        sys.exit(1)

if __name__ == "__main__":
    run()
