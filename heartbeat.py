import os
import sys
import pandas as pd
import yfinance as yf
from supabase import create_client

def run():
    print("--- 1. ROBOT WAKING UP ---")
    
    # Check Secrets
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or url == "" or "supabase.co" not in str(url):
        print("!!! ERROR: SUPABASE_URL is missing or invalid in GitHub Secrets.")
        sys.exit(1)
    print("--- 2. SECRETS VERIFIED ---")

    try:
        # Connect to Database
        supabase = create_client(url, key)
        print("--- 3. DATABASE CONNECTED ---")
        
        # Get Market Data
        print("--- 4. FETCHING MARKET DATA ---")
        # Just BTC-AUD for this test to keep it simple
        data = yf.download("BTC-AUD", period="5d", interval="1d", progress=False)
        
        if data.empty:
            print("!!! ERROR: Yahoo Finance returned NO data. Is the internet down?")
            sys.exit(1)
        
        price = data['Close'].iloc[-1]
        print(f"--- 5. DATA RECEIVED: BTC is ${price:,.2f} AUD ---")
            
        # Try a test write
        print("--- 6. ATTEMPTING DATABASE WRITE ---")
        # (We are not actually writing yet, just testing the connection flow)
        
        print("--- 7. ROBOT SHIFT SUCCESSFUL ---")
        
    except Exception as e:
        print(f"!!! CRITICAL CRASH: {str(e)}")
        # This gives us the 'Secret Message' we need
        sys.exit(1)

if __name__ == "__main__":
    run()
