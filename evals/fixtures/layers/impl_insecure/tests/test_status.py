import unittest

from tests.helpers import call


class StatusTests(unittest.TestCase):
    def test_owner_gets_status(self):
        status, body = call("/claims/C-100/status", user="alice")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"claim_id": "C-100", "status": "under_review",
                                "updated_at": "2026-10-20T09:12:00Z"})

    def test_unknown_claim_404(self):
        status, body = call("/claims/C-999/status", user="alice")
        self.assertEqual(status, 404)
        self.assertEqual(body, {"error": "claim not found"})

    def test_no_amount_or_policy(self):
        _, body = call("/claims/C-100/status", user="alice")
        self.assertNotIn("amount", body)
        self.assertNotIn("policy_id", body)


if __name__ == "__main__":
    unittest.main()
