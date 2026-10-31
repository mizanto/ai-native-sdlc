import json

from claims.api import app


def call(path, user=None, method="GET"):
    environ = {"REQUEST_METHOD": method, "PATH_INFO": path}
    if user:
        environ["HTTP_X_USER"] = user
    captured = {}

    def start_response(status, headers):
        captured["status"] = int(status.split()[0])

    body = b"".join(app(environ, start_response))
    return captured["status"], json.loads(body)
