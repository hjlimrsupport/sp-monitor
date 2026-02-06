import threading
import webbrowser
import time
import sys
from smart_monitor import run_targeted_monitor
from server import run as run_server

def start_browser():
    # Wait a bit for the server to start
    time.sleep(2)
    print("🌐 Opening dashboard at http://localhost:8080")
    webbrowser.open("http://localhost:8080")

if __name__ == "__main__":
    print("="*50)
    print("   Splashtop JP Monitor & Analyzer   ")
    print("="*50)
    
    # Run analysis first
    print("\n🔍 Step 1: Analyzing website changes...")
    try:
        run_targeted_monitor()
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        # Continue to server or exit? Let's show the dashboard anyway
    
    print("\n📡 Step 2: Starting Dashboard Server...")
    # Start browser in a background thread
    threading.Thread(target=start_browser, daemon=True).start()
    
    # Run server (this is a blocking call)
    try:
        run_server(port=8080)
    except Exception as e:
        print(f"❌ Server failed: {e}")
        sys.exit(1)
