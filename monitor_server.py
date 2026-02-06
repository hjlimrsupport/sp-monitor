
import http.server
import socketserver
import json
import os
import webbrowser
import threading
from pathlib import Path

# Import logic
import smart_monitor
import cleanup

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MonitorAPIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == '/api/data':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            data = {
                "meta": self.load_json("site_report_meta.json"),
                "summary": self.load_json("site_summary.json"),
                "structure": self.load_json("site_structure.json"),
                "history": self.load_json("monitoring_history.json")
            }
            self.wfile.write(json.dumps(data).encode('utf-8'))
        else:
            # Serve index.html by default
            if self.path == '/' or self.path == '':
                self.path = '/index.html'
            return super().do_GET()

    def do_POST(self):
        content_length = int(self.headers['Content-Length']) if 'Content-Length' in self.headers else 0
        
        if self.path == '/api/scan':
            try:
                print("🚀 Starting Scan via API...")
                smart_monitor.run_targeted_monitor()
                self.send_success()
            except Exception as e:
                self.send_error_msg(str(e))
        
        elif self.path == '/api/cleanup':
            try:
                cleanup.run_cleanup()
                self.send_success()
            except Exception as e:
                self.send_error_msg(str(e))
                
        elif self.path == '/api/reset':
            try:
                files = ["site_state.json", "site_summary.json", "site_report_meta.json", "monitoring_history.json", "site_structure.json", "site_state_daily.json"]
                for f in files:
                    p = Path(DIRECTORY) / f
                    if p.exists(): p.unlink()
                self.send_success()
            except Exception as e:
                self.send_error_msg(str(e))

    def send_success(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "success"}).encode())

    def send_error_msg(self, msg):
        self.send_response(500)
        self.end_headers()
        self.wfile.write(msg.encode())

    def load_json(self, filename):
        p = Path(DIRECTORY) / filename
        if p.exists():
            with p.open('r', encoding='utf-8') as f:
                try: return json.load(f)
                except: return [] if "history" in filename or "summary" in filename else {}
        return [] if "history" in filename or "summary" in filename else {}

def start_browser():
    webbrowser.open(f"http://localhost:{PORT}")

if __name__ == "__main__":
    print(f"📡 Splashtop JP Monitor Server starting at http://localhost:{PORT}")
    
    # Auto-open browser
    threading.Timer(1.5, start_browser).start()
    
    with socketserver.TCPServer(("", PORT), MonitorAPIHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped.")
            httpd.shutdown()
