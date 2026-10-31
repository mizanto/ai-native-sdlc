"""In-memory data store. Real deployments back this with Postgres."""

CLAIMS = {
    "C-100": {"id": "C-100", "policy_id": "P-1", "owner": "alice", "status": "under_review",
              "amount": 1250.00, "updated_at": "2026-10-20T09:12:00Z"},
    "C-101": {"id": "C-101", "policy_id": "P-1", "owner": "alice", "status": "paid",
              "amount": 300.00, "updated_at": "2026-09-02T14:40:00Z"},
    "C-200": {"id": "C-200", "policy_id": "P-2", "owner": "bob", "status": "submitted",
              "amount": 980.50, "updated_at": "2026-10-28T17:05:00Z"},
}

POLICIES = {
    "P-1": {"id": "P-1", "owner": "alice"},
    "P-2": {"id": "P-2", "owner": "bob"},
}


def get_claim(claim_id):
    return CLAIMS.get(claim_id)


def claims_for_policy(policy_id):
    return [c for c in CLAIMS.values() if c["policy_id"] == policy_id]
