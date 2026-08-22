"""
Static file server + /api/chat proxy endpoint.
Fixes CORS: Mini App calls /api/chat on same origin, server calls Anthropic.
"""
import os
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from anthropic import Anthropic

PORT = int(os.getenv("PORT", 8080))
WEB_DIR = os.path.dirname(os.path.abspath(__file__))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

client = Anthropic(api_key=ANTHROPIC_API_KEY)
logger = logging.getLogger(__name__)

DEFAULT_SYSTEM = """Ты — персональный учитель английского языка. Ученик учит с нуля.
ПРАВИЛА:
1. Отвечай на РУССКОМ (объяснения, советы, оценки)
2. Английские примеры — по-английски
3. Будь конкретным, добрым и честным
4. Исправляй ошибки — объясняй каждую по-русски
5. Всегда давай практический совет в конце
6. Поощряй прогресс — мотивация критична"""


class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass  # silence access log

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/chat":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                messages = data.get("messages", [])
                system = data.get("system", DEFAULT_SYSTEM)

                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1200,
                    system=system,
                    messages=messages
                )
                text = response.content[0].text
                result = json.dumps({"text": text}, ensure_ascii=False)

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors()
                self.end_headers()
                self.wfile.write(result.encode("utf-8"))

            except Exception as e:
                logger.error(f"API error: {e}")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/" or path == "":
            path = "/index.html"

        filepath = os.path.join(WEB_DIR, path.lstrip("/"))
        if os.path.isfile(filepath):
            ext = filepath.rsplit(".", 1)[-1].lower()
            ct = {
                "html": "text/html; charset=utf-8",
                "js": "application/javascript",
                "css": "text/css",
                "png": "image/png",
                "jpg": "image/jpeg",
                "svg": "image/svg+xml",
            }.get(ext, "application/octet-stream")

            with open(filepath, "rb") as f:
                data = f.read()

            self.send_response(200)
            self.send_header("Content-Type", ct)
            self.send_header("Content-Length", len(data))
            self.send_cors()
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"✅ Server on port {PORT}", flush=True)
    server.serve_forever()
