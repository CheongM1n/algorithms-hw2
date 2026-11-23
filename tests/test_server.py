import http.client
import os
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.parse import urlencode

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from hash_table import TABLES  # noqa: E402
from server import make_handler  # noqa: E402
from shortener import Shortener  # noqa: E402


class ServerContract:
    table_class = None

    def setUp(self):
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(Shortener(self.table_class)))
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()

    def req(self, method, path, body=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        headers = {"Content-Type": "application/x-www-form-urlencoded"} if body else {}
        c.request(method, path, body=body, headers=headers)
        r = c.getresponse()
        data = r.read().decode("utf-8")
        c.close()
        return r, data

    def test_form(self):
        r, data = self.req("GET", "/")
        self.assertEqual(r.status, 200)
        self.assertIn("<form", data)

    def test_shorten_and_redirect(self):
        r, data = self.req("POST", "/shorten", urlencode({"url": "https://example.com/a?b=1"}))
        self.assertEqual(r.status, 200)
        self.assertIn(f"127.0.0.1:{self.port}/1", data)
        r, _ = self.req("GET", "/1")
        self.assertEqual(r.status, 302)
        self.assertEqual(r.getheader("Location"), "https://example.com/a?b=1")

    def test_bad_url(self):
        r, _ = self.req("POST", "/shorten", urlencode({"url": "not a url"}))
        self.assertEqual(r.status, 400)

    def test_unknown_code(self):
        self.assertEqual(self.req("GET", "/zzz")[0].status, 404)
        self.assertEqual(self.req("GET", "/!!")[0].status, 404)

    def test_table_view(self):
        self.req("POST", "/shorten", urlencode({"url": "https://example.com"}))
        r, data = self.req("GET", "/table")
        self.assertEqual(r.status, 200)
        self.assertIn(self.table_class.kind, data)
        self.assertIn("Horner", data)
        self.assertIn("https://example.com", data)

    def test_escapes_html(self):
        self.req("POST", "/shorten", urlencode({"url": "https://a.com/<script>"}))
        _, data = self.req("GET", "/table")
        self.assertNotIn("<script>", data)


for _name, _cls in TABLES:
    globals()[f"TestServer_{_name}"] = type(f"TestServer_{_name}", (ServerContract, unittest.TestCase),
                                           {"table_class": _cls})


if __name__ == "__main__":
    unittest.main()
