import unittest

from security_policy import authorize_model_execution


class SecurityPolicyTests(unittest.TestCase):
    def test_low_risk_and_minimal_scope_allowed(self):
        d = authorize_model_execution(
            request_text="summarize public text",
            requested_scopes=["read"],
            granted_scopes=["read"],
            risk_assessment="low",
        )
        self.assertTrue(d.allowed)

    def test_scope_escalation_denied(self):
        d = authorize_model_execution(
            request_text="request",
            requested_scopes=["read", "write"],
            granted_scopes=["read"],
            risk_assessment="low",
        )
        self.assertFalse(d.allowed)

    def test_no_requested_scope_denied(self):
        d = authorize_model_execution(
            request_text="request",
            requested_scopes=[],
            granted_scopes=["read"],
            risk_assessment="low",
        )
        self.assertFalse(d.allowed)

    def test_unknown_and_high_risk_fail_closed(self):
        for risk in ("unknown", "high"):
            with self.subTest(risk=risk):
                self.assertFalse(
                    authorize_model_execution(
                        request_text="request",
                        requested_scopes=["read"],
                        granted_scopes=["read"],
                        risk_assessment=risk,
                    ).allowed
                )

    def test_elevated_risk_does_not_proceed_on_approval_alone(self):
        d = authorize_model_execution(
            request_text="request",
            requested_scopes=["read"],
            granted_scopes=["read"],
            risk_assessment="elevated",
            human_approval=True,
        )
        self.assertFalse(d.allowed)

    def test_audit_record_does_not_keep_request_text(self):
        text = "private request content"
        d = authorize_model_execution(
            request_text=text,
            requested_scopes=[],
            granted_scopes=[],
            risk_assessment="high",
        )
        record = d.audit_record(text)
        self.assertNotIn(text, str(record))
        self.assertFalse(record["request_content_retained"])
        self.assertEqual(len(record["request_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
