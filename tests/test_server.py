import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import override
from unittest.mock import patch

import requests

import server


class ServerTests(unittest.TestCase):
    @override
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.html = b"<!doctype html><title>Freeside</title>"
        (self.root / "freeside-sign.html").write_bytes(self.html)
        (self.root / "eventsdata.json").write_bytes(b"[]")
        (self.root / "unrelated.html").write_bytes(b"Other page")
        root_patch = patch("server.CONTENT_ROOT", self.root)
        root_patch.start()
        self.addCleanup(root_patch.stop)
        log_patch = patch.object(server.SignRequestHandler, "log_message")
        log_patch.start()
        self.addCleanup(log_patch.stop)
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.SignRequestHandler)
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)
        thread = threading.Thread(
            target=lambda: self.httpd.serve_forever(poll_interval=0.01), daemon=True
        )
        thread.start()
        self.base_url = f"http://127.0.0.1:{self.httpd.server_port}"

    def test_root_serves_sign_without_redirect_or_directory_listing(self) -> None:
        for path in ("/", "/?_=123"):
            response = requests.get(
                self.base_url + path, timeout=2, allow_redirects=False
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, self.html)
            self.assertEqual(
                response.headers["Content-Type"], "text/html; charset=utf-8"
            )

    def test_event_data_and_head_requests(self) -> None:
        response = requests.get(self.base_url + "/eventsdata.json?_=123", timeout=2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertIn("Last-Modified", response.headers)
        response = requests.head(self.base_url + "/", timeout=2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")
        self.assertEqual(int(response.headers["Content-Length"]), len(self.html))

    def test_event_timestamp_tracks_last_successful_publication(self) -> None:
        output = self.root / "eventsdata.json"
        os.utime(output, (1_700_000_000, 1_700_000_000))
        response = requests.get(self.base_url + "/eventsdata.json", timeout=2)
        self.assertEqual(
            response.headers["Last-Modified"], "Tue, 14 Nov 2023 22:13:20 GMT"
        )
        replacement = self.root / "replacement.json"
        replacement.write_bytes(b"[]")
        os.utime(replacement, (1_700_003_600, 1_700_003_600))
        replacement.replace(output)
        response = requests.get(self.base_url + "/eventsdata.json", timeout=2)
        self.assertEqual(
            response.headers["Last-Modified"], "Tue, 14 Nov 2023 23:13:20 GMT"
        )

    def test_other_paths_are_not_served(self) -> None:
        for path in (
            "/freeside-sign.html",
            "/unrelated.html",
            "/server.py",
            "/public/",
            "/.env",
        ):
            response = requests.get(self.base_url + path, timeout=2)
            self.assertEqual(response.status_code, 404)
        (self.root / "eventsdata.json").unlink()
        response = requests.get(self.base_url + "/eventsdata.json", timeout=2)
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
