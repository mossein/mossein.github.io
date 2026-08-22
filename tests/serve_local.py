#!/usr/bin/env python3
"""Serve the repo the way GitHub Pages serves it, for local verification.

GitHub Pages does three things a plain `http.server` does not, and all three
matter to the agent-readiness checks:

  * `/about` resolves to `about.html`
  * a missing path returns `404.html` with a real 404 status
  * `.md` is served as `text/markdown; charset=utf-8`

    python3 tests/serve_local.py 8000 &
    tests/verify_live.sh http://127.0.0.1:8000
"""

import functools
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class PagesHandler(SimpleHTTPRequestHandler):
    extensions_map = dict(SimpleHTTPRequestHandler.extensions_map)
    extensions_map[".md"] = "text/markdown"
    extensions_map[".txt"] = "text/plain"

    def translate_path(self, path):
        local = SimpleHTTPRequestHandler.translate_path(self, path)
        if os.path.isdir(local):
            index = os.path.join(local, "index.html")
            return index if os.path.exists(index) else local
        if not os.path.exists(local) and not os.path.splitext(local)[1]:
            # pages answers /about as well as /about.html
            if os.path.exists(local + ".html"):
                return local + ".html"
        return local

    def send_error(self, code, message=None, explain=None):
        custom = os.path.join(ROOT, "404.html")
        if code == 404 and os.path.exists(custom):
            with open(custom, "rb") as fh:
                body = fh.read()
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Vary", "Accept-Encoding")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
            return
        SimpleHTTPRequestHandler.send_error(self, code, message, explain)

    def guess_type(self, path):
        base = SimpleHTTPRequestHandler.guess_type(self, path)
        if base.startswith("text/") and "charset" not in base:
            return base + "; charset=utf-8"
        return base

    def log_message(self, *args):
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    handler = functools.partial(PagesHandler, directory=ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print("serving %s on http://127.0.0.1:%d" % (ROOT, port))
    server.serve_forever()


if __name__ == "__main__":
    main()
