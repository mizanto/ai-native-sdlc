# claims-service

Tiny WSGI claims API (stdlib only). `claims/api.py` routes, `claims/store.py` data.

<!-- sdlc:begin -->
## AI-Native SDLC

Work items live in `docs/sdlc/<ID>/`. Each stage writes one artifact and the next
stage only starts once its upstream is accepted (`/sdlc-accept`).

### Commands
- Test all: `python3 -m unittest discover -s tests -v`
- Test one: `python3 -m unittest tests.test_api -v`
- Run locally: `python3 -m claims.api` (serves on :8000)

### Verifying your work
Run `python3 -m unittest discover -s tests -v`. Healthy output ends with `OK`.
"Done" means this passed and the output is pasted into verify.md.

### Things Claude gets wrong
- The user identity comes from the `X-User` header (`HTTP_X_USER` in environ); every endpoint must check ownership.
<!-- sdlc:end -->
