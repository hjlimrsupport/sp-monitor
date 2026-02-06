#!/bin/bash

# Move to the project directory
cd "$(dirname "$0")"

echo "------------------------------------------------"
echo "🚀 Splashtop JP Monitoring System Starting..."
echo "------------------------------------------------"

# 1. Install dependencies
echo "📦 Checking dependencies..."
pip3 install -r requirements.txt --quiet

# 2. Run the smart monitor to get the latest data
echo "🔍 Step 2: Analyzing website changes..."
python3 smart_monitor.py

# 2. Check if Python is installed to run a simple server
if command -v python3 >/dev/null 2>&1; then
    echo "🌐 Step 2: Starting Local Dashboard Server at http://localhost:8080"
    
    # Open the browser automatically
    # For Mac, use 'open'. For Windows, 'start'. For Linux, 'xdg-open'.
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "http://localhost:8080"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        start "http://localhost:8080"
    else
        xdg-open "http://localhost:8080"
    fi

    # Start our custom server
    python3 server.py
else
    echo "❌ Error: Python3 is not installed. Please install it to use the monitor."
fi
