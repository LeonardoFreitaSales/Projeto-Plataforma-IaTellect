import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", 3001))
ROOT = os.path.dirname(os.path.abspath(__file__))

NAO_ENCONTRADO = (
    "<meta charset=utf-8><p style=\"font:16px sans-serif;padding:2rem\">"
    "Esta pagina nao esta incluida neste pacote. "
    "<a href=\"acesso.html\">Voltar ao acesso</a></p>"
).encode("utf-8")


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".css": "text/css; charset=utf-8",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        if self.path in ("/", ""):
            self.path = "/acesso.html"
        super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def send_error(self, code, message=None, explain=None):
        if code == 404:
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(NAO_ENCONTRADO)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(NAO_ENCONTRADO)
        else:
            super().send_error(code, message, explain)

    def list_directory(self, path):
        self.send_error(404)
        return None


if __name__ == "__main__":
    try:
        servidor = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        print(f"A porta {PORT} ja esta em uso. Feche o outro servidor e tente de novo.")
        sys.exit(1)
    print(f"Tela de acesso em http://localhost:{PORT}")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
