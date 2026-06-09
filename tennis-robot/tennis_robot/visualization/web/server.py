import http.server
import socketserver
import os
import argparse


def launch_server(port=8000, directory=None):
    if directory is None:
        directory = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            "web_viz_data",
        )

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

        def do_GET(self):
            if self.path == "/":
                viz_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                    "tennis_robot", "visualization", "web", "visualization.html",
                )
                if os.path.exists(viz_path):
                    self.path = "/../tennis_robot/visualization/web/visualization.html"
            return super().do_GET()

        def log_message(self, format, *args):
            pass

    with socketserver.TCPServer(("", port), QuietHandler) as httpd:
        print(f"Web visualization server running at http://localhost:{port}")
        print(f"Serving from: {directory}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--directory", type=str, default=None)
    args = parser.parse_args()
    launch_server(args.port, args.directory)
