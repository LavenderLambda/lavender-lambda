import os
import sys
import pandas as pd
import yfinance as yf
from supabase import create_client

def run():
    print("--- 1. ROBOT WAKING UP ---")
    
    # 1. Fetch Secrets from GitHub
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    # 2. Strict Check for the URL
    if not url or "supabase.co" not in str(url):
        print("!!! ERROR: SUPABASE_URL is missing or wrong in GitHub.")
        sys.exit(1)
    
    # 3. Strict Check for the KEY
    if not key or len(str(key)) < 10:
        print("!!! ERROR: SUPABASE_KEY is missing or too short in GitHub.")
        print(f"DEBUG: Key found was: {type(key)}")
        sys.exit(1)

    print("--- 2. ADDRESS AND KEY VERIFIED ---")

    try:
        # 4. Connect to Database
        print("--- 3. ATTEMPTING CLOUD CONNECTION ---")
        supabase = create_client(url, key)
        print("--- 4. DATABASE CONNECTED ---")
        
        # 5. Get Market Data (Testing with BTC)
        print("--- 5. FETCHING MARKET DATA ---")
        data = yf.download("BTC-AUD", period="5d", interval="1d", progress=False)
        
        if data.empty:
            print("!!! ERROR: No market data received.")
            sys.exit(1)
        
        price = data['Close'].iloc[-1]
        print(f"--- 6. DATA RECEIVED: BTC is ${price:,.2f} AUD ---")
        print("--- 7. ROBOT SHIFT SUCCESSFUL ---")
        
    except Exception as e:
        print(f"!!! CRITICAL CRASH: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run()
