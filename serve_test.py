#!/usr/bin/env python3
"""
Simple HTTP server to serve the connectivity test page.
This fixes CORS issues when opening HTML files directly.
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

# Change to the project directory
project_dir = Path(__file__).parent
os.chdir(project_dir)

PORT = 3001

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"🌐 Serving test page at http://localhost:{PORT}")
        print(f"📄 Test page URL: http://localhost:{PORT}/test_frontend_connectivity.html")
        print("🚫 Press Ctrl+C to stop the server")
        
        # Open the test page in the default browser
        test_url = f"http://localhost:{PORT}/test_frontend_connectivity.html"
        print(f"🔗 Opening {test_url} in browser...")
        webbrowser.open(test_url)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")