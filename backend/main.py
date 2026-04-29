"""
Mock backend for sentiment analysis.

This version is intentionally lightweight for K3s on small AWS instances.
It uses Python's built-in http.server and returns a fixed JSON response.
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def _json(self, payload, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._json({"status": "ok"})
            return
        self._json({"sentiment": "POSITIVE", "label": "POSITIVE", "score": 0.99, "text": ""})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""
        text = ""
        if raw:
            try:
                payload = json.loads(raw.decode("utf-8"))
                text = str(payload.get("text", ""))
            except Exception:
                text = ""

        self._json({"sentiment": "POSITIVE", "label": "POSITIVE", "score": 0.99, "text": text})

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    server.serve_forever()
