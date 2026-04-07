"""Simple HTTP server with Range request support for audio seeking."""
import os
import http.server
import socketserver

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class RangeHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        range_header = self.headers.get('Range')
        if not range_header:
            return super().do_GET()

        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            self.send_error(404)
            return

        file_size = os.path.getsize(path)
        # Parse "bytes=START-END"
        range_spec = range_header.replace('bytes=', '')
        parts = range_spec.split('-')
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else file_size - 1
        end = min(end, file_size - 1)
        length = end - start + 1

        self.send_response(206)
        ctype = self.guess_type(path)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
        self.send_header('Content-Length', str(length))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        with open(path, 'rb') as f:
            f.seek(start)
            self.wfile.write(f.read(length))

    def end_headers(self):
        self.send_header('Accept-Ranges', 'bytes')
        super().end_headers()


class ReuseTCPServer(socketserver.TCPServer):
    allow_reuse_address = True
    allow_reuse_port = True


if __name__ == '__main__':
    with ReuseTCPServer(('', PORT), RangeHTTPRequestHandler) as httpd:
        print(f'Serving on http://localhost:{PORT}')
        httpd.serve_forever()
