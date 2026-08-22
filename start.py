#!/usr/bin/env python3
"""Starts both the Telegram bot and the Mini App static server concurrently."""
import subprocess
import sys
import os

def main():
    bot_proc = subprocess.Popen([sys.executable, "bot/main.py"])
    web_proc = subprocess.Popen([sys.executable, "webapp/server.py"])

    try:
        bot_proc.wait()
    except KeyboardInterrupt:
        bot_proc.terminate()
        web_proc.terminate()

if __name__ == "__main__":
    main()
