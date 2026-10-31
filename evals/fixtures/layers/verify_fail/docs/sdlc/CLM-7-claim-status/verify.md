---
id: CLM-7-claim-status
artifact: verify
lane: full
status: draft
upstream: docs/sdlc/CLM-7-claim-status/plan.md
created: 2026-10-29
verdict: fail
---

# Verification: Claim status endpoint

## Proof results
`python3 -m unittest discover -s tests -v` — exit 1 — FAIL
```
test_other_user_403 (test_status.StatusTests.test_other_user_403) ... ok
test_owner_gets_status (test_status.StatusTests.test_owner_gets_status) ... ok
test_unknown_claim_404 (test_status.StatusTests.test_unknown_claim_404) ... ERROR

======================================================================
ERROR: test_unknown_claim_404 (test_status.StatusTests.test_unknown_claim_404)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/var/folders/gz/rb99vhsj5qv6mj0nbyzrkffh0000gn/T/tmp.CTk5NNswIN/tests/test_status.py", line 14, in test_unknown_claim_404
    status, body = call("/claims/C-999/status", user="alice")
                   ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/var/folders/gz/rb99vhsj5qv6mj0nbyzrkffh0000gn/T/tmp.CTk5NNswIN/tests/helpers.py", line 15, in call
    body = b"".join(app(environ, start_response))
                    ~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/var/folders/gz/rb99vhsj5qv6mj0nbyzrkffh0000gn/T/tmp.CTk5NNswIN/claims/api.py", line 60, in app
    return handler(environ, start_response, **match.groupdict())
  File "/private/var/folders/gz/rb99vhsj5qv6mj0nbyzrkffh0000gn/T/tmp.CTk5NNswIN/claims/api.py", line 39, in get_claim_status
    claim = store.CLAIMS[claim_id]
            ~~~~~~~~~~~~^^^^^^^^^^
KeyError: 'C-999'

----------------------------------------------------------------------
Ran 10 tests in 0.001s

FAILED (errors=1)
```

## Traceability
- R1 — PASS — test_owner_gets_status
- R2 — FAIL — test_unknown_claim_404 raises KeyError
- R3 — PASS — test_other_user_403, test_missing_user_403
- R4 — PASS — test_no_amount_or_policy

## Verdict
fail — R2: unknown claim raises KeyError instead of returning 404.
