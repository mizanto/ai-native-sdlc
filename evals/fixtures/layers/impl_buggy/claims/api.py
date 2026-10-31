"""WSGI API. Callers authenticate upstream; the gateway passes the user in X-User."""

import json
import re

from claims import store


def _json(start_response, status, body):
    payload = json.dumps(body).encode()
    start_response(status, [("Content-Type", "application/json"),
                            ("Content-Length", str(len(payload)))])
    return [payload]


def _user(environ):
    return environ.get("HTTP_X_USER")


def get_claim(environ, start_response, claim_id):
    claim = store.get_claim(claim_id)
    if claim is None:
        return _json(start_response, "404 Not Found", {"error": "claim not found"})
    if claim["owner"] != _user(environ):
        return _json(start_response, "403 Forbidden", {"error": "forbidden"})
    return _json(start_response, "200 OK", claim)


def list_policy_claims(environ, start_response, policy_id):
    policy = store.POLICIES.get(policy_id)
    if policy is None:
        return _json(start_response, "404 Not Found", {"error": "policy not found"})
    if policy["owner"] != _user(environ):
        return _json(start_response, "403 Forbidden", {"error": "forbidden"})
    return _json(start_response, "200 OK", {"claims": store.claims_for_policy(policy_id)})


def get_claim_status(environ, start_response, claim_id):
    claim = store.CLAIMS[claim_id]
    if claim["owner"] != _user(environ):
        return _json(start_response, "403 Forbidden", {"error": "forbidden"})
    return _json(start_response, "200 OK", {"claim_id": claim["id"], "status": claim["status"],
                                             "updated_at": claim["updated_at"]})


ROUTES = [
    (re.compile(r"^/claims/(?P<claim_id>[\w-]+)$"), get_claim),
    (re.compile(r"^/claims/(?P<claim_id>[\w-]+)/status$"), get_claim_status),
    (re.compile(r"^/policies/(?P<policy_id>[\w-]+)/claims$"), list_policy_claims),
]


def app(environ, start_response):
    if environ.get("REQUEST_METHOD", "GET") != "GET":
        return _json(start_response, "405 Method Not Allowed", {"error": "method not allowed"})
    path = environ.get("PATH_INFO", "/")
    for pattern, handler in ROUTES:
        match = pattern.match(path)
        if match:
            return handler(environ, start_response, **match.groupdict())
    return _json(start_response, "404 Not Found", {"error": "not found"})


if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    make_server("127.0.0.1", 8000, app).serve_forever()
