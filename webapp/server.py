"""
Static file server + /api/chat proxy using Google Gemini (free).
"""
import os
import json
import logging
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
import google.generativeai as genai

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

PORT = int(os.getenv("PORT", 8080))
WEB_DIR = os.path.dirname(os.path.abspath(__file__))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    logger.error("❌ GEMINI_API_KEY not set!")
else:
    logger.info(f"✅ Gemini key loaded: {GEMINI_API_KEY[:8]}...")

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

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


def build_prompt(messages, system):
    """Convert OpenAI-style messages to a single Gemini prompt."""
    sys_text = system or DEFAULT_SYSTEM
    parts = [f"СИСТЕМНАЯ ИНСТРУКЦИЯ:\n{sys_text}\n\n"]
    for m in messages:
        role = "Ученик" if m.get("role") == "user" else "Учитель"
        parts.append(f"{role}: {m.get('content', '')}")
    return "\n".join(parts)


class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        logger.info(f"HTTP {self.command} {self.path}")

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
                prompt = build_prompt(messages, system)

                logger.info(f"Calling Gemini, prompt length: {len(prompt)}")
                response = gemini_model.generate_content(prompt)
                text = response.text
                logger.info(f"Gemini response length: {len(text)}")

                body = json.dumps({"text": text}, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", len(body))
                self.send_cors()
                self.end_headers()
                self.wfile.write(body)

            except Exception as e:
                logger.error(f"Error: {e}\n{traceback.format_exc()}")
                body = json.dumps({"error": str(e)}).encode("utf-8")
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
                "js": "application/javascript; charset=utf-8",
                "css": "text/css",
                "png": "image/png",
                "jpg": "image/jpeg",
                "svg": "image/svg+xml",
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
            logger.warning(f"404: {filepath}")
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    logger.info(f"✅ Server starting on port {PORT}")
    logger.info(f"✅ Serving from: {WEB_DIR}")
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()
