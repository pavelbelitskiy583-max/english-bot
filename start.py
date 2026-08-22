#!/usr/bin/env python3
"""
Runs web server (PORT) in main thread + Telegram bot in background thread.
Railway needs the web server on $PORT to stay alive.
"""
import threading
import sys
import os
import subprocess

def run_bot():
    bot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot", "main.py")
    while True:
        try:
            subprocess.run([sys.executable, bot_path])
        except Exception as e:
            print(f"Bot crashed: {e}, restarting...", flush=True)

if __name__ == "__main__":
    # Start bot in background thread (daemon = dies with main)
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()
    print("✅ Bot thread started", flush=True)

    # Run web server in MAIN thread (Railway needs this on $PORT)
    server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webapp", "server.py")
    os.execv(sys.executable, [sys.executable, server_path])
