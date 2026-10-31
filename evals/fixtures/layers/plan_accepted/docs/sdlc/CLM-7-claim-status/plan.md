---
id: CLM-7-claim-status
artifact: plan
lane: full
status: accepted
upstream: docs/sdlc/CLM-7-claim-status/spec.md
created: 2026-10-27
accepted_by: Sergey Bendak
accepted_at: 2026-10-28T10:00:00
---

# Plan: Claim status endpoint

## Files that change
- `claims/api.py` — add `get_claim_status` handler and route.
- `tests/test_status.py` — new tests for R1–R4.

## Order of work
- [ ] 1. Add `get_claim_status` to `claims/api.py` with 404 and ownership checks (test: `tests.test_status`)
- [ ] 2. Register route `^/claims/(?P<claim_id>[\w-]+)/status$` in `ROUTES`
- [ ] 3. Add `tests/test_status.py` covering R1–R4
- [ ] 4. Run full suite

## Risks
- Route regex overlap with `/claims/{id}` — patterns are anchored, low risk. Rollback: revert the commit.

## Proof
- R1 — `python3 -m unittest tests.test_status.StatusTests.test_owner_gets_status -v`
- R2 — `python3 -m unittest tests.test_status.StatusTests.test_unknown_claim_404 -v`
- R3 — `python3 -m unittest tests.test_status.StatusTests.test_other_user_403 tests.test_status.StatusTests.test_missing_user_403 -v`
- R4 — `python3 -m unittest tests.test_status.StatusTests.test_no_amount_or_policy -v`
- All — `python3 -m unittest discover -s tests -v`
