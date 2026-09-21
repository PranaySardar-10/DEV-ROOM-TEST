import unittest

from devroom.sandbox_policy import READ_ONLY, WORKSPACE_WRITE, RoleSandboxPolicy


class RoleSandboxPolicyTests(unittest.TestCase):
    def test_default_roles(self) -> None:
        policy = RoleSandboxPolicy()
        self.assertEqual(policy.sandbox_for("Lead"), READ_ONLY)
        self.assertEqual(policy.sandbox_for("Architect"), READ_ONLY)
        self.assertEqual(policy.sandbox_for("Implementer"), WORKSPACE_WRITE)
        self.assertEqual(policy.sandbox_for("Reviewer"), READ_ONLY)
        self.assertEqual(policy.sandbox_for("QA"), READ_ONLY)
        self.assertEqual(policy.sandbox_for("Unknown"), READ_ONLY)

    def test_non_implementer_cannot_be_writable(self) -> None:
        with self.assertRaises(PermissionError):
            RoleSandboxPolicy({"Reviewer": WORKSPACE_WRITE})


if __name__ == "__main__":
    unittest.main()
