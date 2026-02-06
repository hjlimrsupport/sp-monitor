from urllib.parse import urlparse, urlunparse

def normalize_url(url):
    parsed = urlparse(url)
    normalized = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
    return normalized.rstrip('/')

class MonitorHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/add_url':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            new_url = data.get('url')
            if new_url:
                new_url = normalize_url(new_url)
                try:
                    # Load existing structure
                    structure_path = 'site_structure.json'
                    if os.path.exists(structure_path):
                        with open(structure_path, 'r', encoding='utf-8') as f:
                            structure = json.load(f)
                    else:
                        structure = {}
                    
                    # Add new URL with depth 0
                    if new_url not in structure:
                        structure[new_url] = 0
                        with open(structure_path, 'w', encoding='utf-8') as f:
                            json.dump(structure, f, indent=4, ensure_ascii=False)
                        
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'status': 'success'}).encode())
                    else:
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'status': 'exists'}).encode())
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(str(e).encode())
            else:
                self.send_response(400)
                self.end_headers()

def run(server_class=HTTPServer, handler_class=MonitorHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"🚀 Monitor API Server running at http://localhost:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
