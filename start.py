#!/usr/bin/env python3
"""Starts both the Telegram bot and the Mini App static server concurrently."""
import threading
import sys
import os
import http.server
import subprocess

PORT = int(os.getenv("PORT", 8080))
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webapp")

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, format, *args):
        pass

def run_webserver():
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"✅ Webapp running on port {PORT}", flush=True)
    server.serve_forever()

def run_bot():
    bot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot", "main.py")
    subprocess.run([sys.executable, bot_path])

if __name__ == "__main__":
    # Start web server in background thread
    web_thread = threading.Thread(target=run_webserver, daemon=True)
    web_thread.start()

    # Run bot in main thread
    print("✅ Starting Telegram bot...", flush=True)
    run_bot()
