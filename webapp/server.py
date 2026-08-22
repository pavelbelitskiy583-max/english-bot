"""
Static file server + /api/chat proxy using Google Gemini REST API directly.
"""
import os
import json
import logging
import traceback
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", 8080))
WEB_DIR = os.path.dirname(os.path.abspath(__file__))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not set!")
else:
    logger.info(f"Gemini key loaded: {GEMINI_API_KEY[:12]}...")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

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


def call_gemini(messages, system):
    sys_text = system or DEFAULT_SYSTEM
    # Build prompt from messages history
    parts_text = f"ИНСТРУКЦИЯ УЧИТЕЛЯ:\n{sys_text}\n\n"
    for m in messages:
        role = "Ученик" if m.get("role") == "user" else "Учитель"
        parts_text += f"{role}: {m.get('content', '')}\n"
    parts_text += "Учитель:"

    payload = {
        "contents": [{"parts": [{"text": parts_text}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 1200,
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
        return data["candidates"][0]["content"]["parts"][0]["text"]


class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        logger.info(f"{self.command} {self.path}")

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors()
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/chat":
            try:
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length)
                data = json.loads(raw)
                messages = data.get("messages", [])
                system = data.get("system") or DEFAULT_SYSTEM

                text = call_gemini(messages, system)
                logger.info(f"Gemini OK, response len: {len(text)}")

                body = json.dumps({"text": text}, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", len(body))
                self.send_cors()
                self.end_headers()
                self.wfile.write(body)

            except urllib.error.HTTPError as e:
                err = e.read().decode()
                logger.error(f"Gemini HTTP error {e.code}: {err}")
                body = json.dumps({"error": f"Gemini {e.code}: {err[:200]}"}).encode()
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", len(body))
                self.send_cors()
                self.end_headers()
                self.wfile.write(body)

            except Exception as e:
                logger.error(f"Error: {e}\n{traceback.format_exc()}")
                body = json.dumps({"error": str(e)}).encode()
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", len(body))
                self.send_cors()
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
                "js": "application/javascript",
                "css": "text/css",
                "png": "image/png",
            }.get(ext, "application/octet-stream")
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", ct)
            self.send_header("Content-Length", len(content))
            self.send_header("Cache-Control", "no-cache")
            self.send_cors()
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    logger.info(f"Server starting on port {PORT}, serving from {WEB_DIR}")
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()
