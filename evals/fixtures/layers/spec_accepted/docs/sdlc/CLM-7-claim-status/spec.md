---
id: CLM-7-claim-status
artifact: spec
lane: full
status: accepted
upstream: docs/sdlc/CLM-7-claim-status/intent.md
created: 2026-10-27
accepted_by: Sergey Bendak
accepted_at: 2026-10-28T10:00:00
---

# Spec: Claim status endpoint for the mobile app

## Requirements
- **R1** — `GET /claims/{id}/status` returns `200` with JSON `{"claim_id", "status", "updated_at"}` when the caller (`X-User`) owns the claim.
- **R2** — An unknown claim id returns `404` with `{"error": "claim not found"}`.
- **R3** — A caller who does not own the claim, or sends no `X-User`, gets `403` with `{"error": "forbidden"}`.
- **R4** — The response contains no monetary amount and no policy fields (data minimisation, SECURITY.md).

## Design
New handler `get_claim_status` in `claims/api.py`, registered in `ROUTES` with pattern `^/claims/(?P<claim_id>[\w-]+)/status$`. Reuses `store.get_claim` and the existing `_user`/`_json` helpers; mirrors the ownership check in `get_claim`.

## Non-goals
- Status explanations or history.
- Push notifications on status change.

## Flagged concerns
- R3 returns 403 for other owners, which reveals that the claim id exists. Accepted by product for consistency with `GET /claims/{id}` (2026-10-28).

## Acceptance criteria
- R1–R4 each covered by a unit test in `tests/test_status.py`; full suite stays green.
