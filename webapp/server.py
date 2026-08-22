"""
Static file server + /api/chat proxy for Anthropic API.
Fixes CORS issue — Mini App calls same origin, server proxies to Anthropic.
"""
import os
import json
import logging
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from anthropic import Anthropic

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", 8080))
WEB_DIR = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

if not API_KEY:
    logger.error("❌ ANTHROPIC_API_KEY not set!")
else:
    logger.info(f"✅ Anthropic key loaded: {API_KEY[:8]}...")

client = Anthropic(api_key=API_KEY)

DEFAULT_SYSTEM = (
    "Ты — персональный учитель английского языка. Ученик учит с нуля.\n"
    "ПРАВИЛА:\n"
    "1. Отвечай на РУССКОМ (объяснения, советы, оценки)\n"
    "2. Английские примеры — по-английски\n"
    "3. Будь конкретным, добрым и честным\n"
    "4. Исправляй ошибки — объясняй каждую по-русски\n"
    "5. Всегда давай практический совет в конце\n"
    "6. Поощряй прогресс"
)


class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        logger.info(f"HTTP {self.command} {self.path} — {fmt % args}")

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/chat":
            try:
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length)
                logger.info(f"POST /api/chat body: {raw[:200]}")
                data = json.loads(raw)

                messages = data.get("messages", [])
                system = data.get("system") or DEFAULT_SYSTEM

                if not messages:
                    raise ValueError("No messages provided")

                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1200,
                    system=system,
                    messages=messages
                )
                text = response.content[0].text
                logger.info(f"Claude response length: {len(text)}")

                body = json.dumps({"text": text}, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", len(body))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(body)

            except Exception as e:
                logger.error(f"Error in /api/chat: {e}\n{traceback.format_exc()}")
                body = json.dumps({"error": str(e)}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", len(body))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", ""):
            path = "/index.html"

        filepath = os.path.join(WEB_DIR, path.lstrip("/"))

        if os.path.isfile(filepath):
            ext = filepath.rsplit(".", 1)[-1].lower()
            ct = {
                "html": "text/html; charset=utf-8",
                "js": "application/javascript; charset=utf-8",
                "css": "text/css",
                "png": "image/png",
                "jpg": "image/jpeg",
                "svg": "image/svg+xml",
                "ico": "image/x-icon",
            }.get(ext, "application/octet-stream")

            with open(filepath, "rb") as f:
                data = f.read()

            self.send_response(200)
            self.send_header("Content-Type", ct)
            self.send_header("Content-Length", len(data))
            self.send_header("Cache-Control", "no-cache")
            self.send_cors_headers()
            self.end_headers()
            self.wfile.write(data)
        else:
            logger.warning(f"404: {filepath}")
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    logger.info(f"✅ Starting server on port {PORT}")
    logger.info(f"✅ Serving files from: {WEB_DIR}")
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()
