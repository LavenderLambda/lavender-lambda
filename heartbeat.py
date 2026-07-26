import os
import sys
import pandas as pd
import yfinance as yf
from datetime import datetime
from supabase import create_client

def run():
    print("--- 1. ROBOT WAKING UP ---")
    
    url = os.environ.get("SUPABASE_URL", "").strip().rstrip("/")
    key = os.environ.get("SUPABASE_KEY", "").strip()
    
    # AUTO-FIX: If user pasted the dashboard URL instead of the API URL
    if "supabase.com/dashboard" in url:
        print("!!! WARNING: You pasted the Dashboard URL. Attempting to extract Project ID...")
        project_id = url.split("/")[-1]
        url = f"https://{project_id}.supabase.co"
    
    if not url.startswith("https://"):
        print(f"!!! ERROR: URL must start with https:// - Found: {url}")
        sys.exit(1)

    print(f"--- 2. ADDRESS SET: {url[:15]}...supabase.co ---")

    try:
        # 1. Connect
        supabase = create_client(url, key)
        print("--- 3. CLOUD CONNECTION INITIALIZED ---")
        
        # 2. Assets
        tickers = ["BTC-AUD", "ETH-AUD", "NVDA", "SPY", "VAS.AX", "GC=F", "SI=F", "AUDUSD=X", "^TNX"]
        
        # 3. Fetch Market Data
        print("--- 4. FETCHING MARKET DATA ---")
        data = yf.download(tickers, period="7d", interval="1d", progress=False)['Close'].ffill()
        
        if data.empty:
            print("!!! ERROR: No data from Yahoo Finance.")
            sys.exit(1)
        
        # 4. Calculate
        today = datetime.now().strftime('%Y-%m-%d')
        daily_vol = float(data.pct_change().iloc[-1].abs().mean() * 100)
        print(f"--- 5. ANALYSIS COMPLETE: Volatility {daily_vol:.2f}% ---")
            
        # 5. SAVE TO SUPABASE
        print("--- 6. PINGING DATABASE ---")
        # The 'execute()' is where the 'Name not known' error happens
        supabase.table("system_state").select("id").limit(1).execute()
        
        print("--- 7. SAVING PERFORMANCE LOG ---")
        supabase.table("performance_logs").upsert({
            "date": today, 
            "error_rate": round(daily_vol, 2)
        }).execute()
        
        print("--- 8. ROBOT SHIFT SUCCESSFUL ---")
        
    except Exception as e:
        error_msg = str(e)
        print(f"!!! CRITICAL CRASH: {error_msg}")
        if "Name or service not known" in error_msg:
            print("\n🆘 FOUNDER ACTION REQUIRED:")
            print("1. Go to Supabase -> Settings -> API.")
            print("2. Copy the 'Project URL' (It ends in .supabase.co).")
            print("3. Update your GitHub Secret 'SUPABASE_URL'.")
        sys.exit(1)

if __name__ == "__main__":
    run()
