"""Local JSON API for the explainable classifier."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from classifier import classify


def reject_constant(value):
    raise ValueError(f"constante JSON inválida: {value}")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def respond(self, status, body):
        payload = json.dumps(body, ensure_ascii=False, allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        self.respond(200, {"ok": True}) if self.path == "/health" else self.respond(404, {"error": "rota não encontrada"})

    def do_POST(self):
        if self.path != "/classify":
            self.respond(404, {"error": "rota não encontrada"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 131072:
                raise ValueError("corpo deve ter entre 1 e 131072 bytes")
            body = json.loads(self.rfile.read(length), parse_constant=reject_constant)
            if not isinstance(body, dict) or "views" not in body:
                raise ValueError("informe objeto com views, uma lista de contagens por hora")
            result = classify(body["views"])
        except (ValueError, UnicodeDecodeError) as error:
            self.respond(400, {"error": str(error)})
            return
        self.respond(200, result)


def serve(port=3009):
    server = HTTPServer(("127.0.0.1", port), Handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=3009)
    serve(parser.parse_args().port)
