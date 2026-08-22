#!/usr/bin/env python3
"""Simple static server for Telegram Mini App — runs alongside the bot."""
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = int(os.getenv("PORT", 8080))
WEB_DIR = os.path.join(os.path.dirname(__file__))

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, format, *args):
        pass  # suppress logs

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Webapp server running on port {PORT}")
    server.serve_forever()
