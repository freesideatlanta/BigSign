"""Serve only the sign at / and its generated event data."""

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

CONTENT_ROOT = Path(__file__).resolve().parent
ROUTES = {
    "/": ("freeside-sign.html", "text/html; charset=utf-8"),
    "/eventsdata.json": ("eventsdata.json", "application/json"),
}


class SignRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.serve_content(send_body=True)

    def do_HEAD(self) -> None:
        self.serve_content(send_body=False)

    def serve_content(self, *, send_body: bool) -> None:
        route = ROUTES.get(urlsplit(self.path).path)
        if route is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        filename, content_type = route
        try:
            content = (CONTENT_ROOT / filename).read_bytes()
        except FileNotFoundError:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if send_body:
            self.wfile.write(content)


def main() -> None:
    with ThreadingHTTPServer(("0.0.0.0", 8080), SignRequestHandler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
