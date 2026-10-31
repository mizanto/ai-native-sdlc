import unittest

from tests.helpers import call


class ClaimTests(unittest.TestCase):
    def test_owner_gets_claim(self):
        status, body = call("/claims/C-100", user="alice")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "under_review")

    def test_other_user_forbidden(self):
        status, _ = call("/claims/C-100", user="bob")
        self.assertEqual(status, 403)

    def test_unknown_claim(self):
        status, _ = call("/claims/C-999", user="alice")
        self.assertEqual(status, 404)


class PolicyTests(unittest.TestCase):
    def test_owner_lists_policy_claims(self):
        status, body = call("/policies/P-1/claims", user="alice")
        self.assertEqual(status, 200)
        self.assertEqual({c["id"] for c in body["claims"]}, {"C-100", "C-101"})

    def test_other_user_forbidden(self):
        status, _ = call("/policies/P-1/claims", user="bob")
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
