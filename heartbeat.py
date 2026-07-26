name: Daily Lavender Heartbeat

on:
  schedule:
    # Runs at 10:00 AM Sydney time
    - cron: '0 0 * * *'
  workflow_dispatch: 

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install pandas yfinance supabase websockets>=13.0

      - name: Run Heartbeat
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
        run: python heartbeat.py
