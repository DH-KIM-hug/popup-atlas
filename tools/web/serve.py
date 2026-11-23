#!/usr/bin/env python3
"""Static server for build/web (Godot web export, no-threads build: no COOP/COEP needed).
Correct wasm/pck types, sends a precompressed <file>.gz when the browser accepts gzip.
   python3 tools/web/serve.py [port] [dir]"""
import http.server, os, sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
ROOT = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "../../build/web"))
TYPES = {".wasm": "application/wasm", ".pck": "application/octet-stream", ".js": "text/javascript",
         ".html": "text/html; charset=utf-8", ".png": "image/png", ".svg": "image/svg+xml"}


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def guess_type(self, path):
        return TYPES.get(os.path.splitext(path)[1], super().guess_type(path))

    def send_head(self):
        path = self.translate_path(self.path)
        gz = path + ".gz"
        if os.path.isfile(path) and os.path.isfile(gz) and "gzip" in self.headers.get("Accept-Encoding", ""):
            f = open(gz, "rb")
            st = os.fstat(f.fileno())
            self.send_response(200)
            self.send_header("Content-Type", self.guess_type(path))
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(st.st_size))
            self.send_header("Last-Modified", self.date_time_string(st.st_mtime))
            self.end_headers()
            return f
        return super().send_head()

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")  # revalidate, so a new export shows up
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.log_date_time_string(), fmt % args))


if __name__ == "__main__":
    print(f"serving {ROOT} on http://localhost:{PORT}", flush=True)
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
