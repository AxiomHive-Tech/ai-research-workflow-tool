from __future__ import annotations

import unittest

from security_policy import authorize_model_execution
from unified_workflow import new_workflow, validate_workflow


def completed_workflow():
    data = new_workflow("edge-1")
    data["status"] = "released"
    for i, stage in enumerate(data["stages"]):
        stamp = f"2026-10-22T{10 + i:02d}:00:00+00:00"
        stage["started_at"] = stamp
        stage["completed_at"] = stamp
        if stage["stage"] in {"scope", "clarification", "research", "design", "draft"}:
            stage["status"] = "completed"
    data["stages"][4]["status"] = "pass"
    data["stages"][4]["record"] = {
        "risk_items": [{"risk_id": "r1", "residual_risk": "low"}]
    }
    data["stages"][6]["status"] = "approved"
    data["stages"][6]["record"] = {"approved": True, "reviewer": "human"}
    data["stages"][7]["status"] = "released"
    data["stages"][7]["record"] = {"decision": "released"}
    data["released_at"] = "2026-10-22T18:00:00+00:00"
    return data


class WorkflowEdgeCaseTests(unittest.TestCase):
    def test_baseline_fixture_is_valid(self):
        self.assertEqual(validate_workflow(completed_workflow()), [])

    def test_escalated_safety_review_blocks_release(self):
        data = completed_workflow()
        data["stages"][4]["status"] = "escalate"
        errors = validate_workflow(data)
        self.assertTrue(any("safety_review must pass" in e for e in errors))

    def test_redirected_safety_review_blocks_release(self):
        data = completed_workflow()
        data["stages"][4]["status"] = "redirect"
        errors = validate_workflow(data)
        self.assertTrue(any("safety_review must pass" in e for e in errors))

    def test_released_requires_released_at(self):
        data = completed_workflow()
        data["released_at"] = None
        errors = validate_workflow(data)
        self.assertTrue(any("released_at is required" in e for e in errors))

    def test_released_at_must_be_null_when_not_released(self):
        data = new_workflow()
        data["released_at"] = "2026-10-22T18:00:00+00:00"
        errors = validate_workflow(data)
        self.assertTrue(any("released_at must be null" in e for e in errors))

    def test_stage_cannot_start_before_prior_stage_completes(self):
        data = new_workflow()
        data["stages"][0]["started_at"] = "2026-10-22T09:00:00+00:00"
        data["stages"][0]["completed_at"] = "2026-10-22T10:00:00+00:00"
        data["stages"][1]["started_at"] = "2026-10-22T09:30:00+00:00"
        errors = validate_workflow(data)
        self.assertTrue(any("must not precede prior stage" in e for e in errors))

    def test_stage_cannot_start_while_prior_stage_is_open(self):
        data = new_workflow()
        data["stages"][0]["started_at"] = "2026-10-22T09:00:00+00:00"
        data["stages"][0]["completed_at"] = "2026-10-22T09:30:00+00:00"
        data["stages"][1]["status"] = "needs_input"
        data["stages"][1]["started_at"] = "2026-10-22T10:00:00+00:00"
        data["stages"][1]["completed_at"] = "2026-10-22T11:00:00+00:00"
        data["stages"][2]["started_at"] = "2026-10-22T12:00:00+00:00"
        errors = validate_workflow(data)
        self.assertTrue(any("prior stage is completed" in e for e in errors))

    def test_end_before_start_is_rejected(self):
        data = new_workflow()
        data["stages"][0]["started_at"] = "2026-10-22T10:00:00+00:00"
        data["stages"][0]["completed_at"] = "2026-10-22T09:00:00+00:00"
        errors = validate_workflow(data)
        self.assertTrue(any("must not precede started_at" in e for e in errors))


class SecurityPolicyEdgeCaseTests(unittest.TestCase):
    def _call(self, **overrides):
        args = {
            "request_text": "request",
            "requested_scopes": ["read"],
            "granted_scopes": ["read"],
            "risk_assessment": "low",
        }
        args.update(overrides)
        return authorize_model_execution(**args)

    def test_whitespace_request_denied(self):
        decision = self._call(request_text="   ")
        self.assertFalse(decision.allowed)
        self.assertIn("empty or invalid", decision.reason)

    def test_capitalized_risk_label_denied(self):
        decision = self._call(risk_assessment="Low")
        self.assertFalse(decision.allowed)
        self.assertIn("invalid risk", decision.reason)

    def test_elevated_risk_without_approval_denied(self):
        decision = self._call(risk_assessment="elevated", human_approval=False)
        self.assertFalse(decision.allowed)
        self.assertIn("requires explicit human approval", decision.reason)

    def test_high_risk_denied_before_scope_check(self):
        decision = self._call(risk_assessment="high", requested_scopes=["read", "write"])
        self.assertFalse(decision.allowed)
        self.assertIn("fails closed", decision.reason)

    def test_scopes_are_deduplicated_and_sorted(self):
        decision = self._call(
            requested_scopes=["write", "read", "read"],
            granted_scopes=["read", "write"],
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.requested_scopes, ("read", "write"))

    def test_audit_record_digest_matches_request(self):
        import hashlib

        decision = self._call(request_text="hello")
        record = decision.audit_record("hello")
        self.assertEqual(
            record["request_sha256"], hashlib.sha256(b"hello").hexdigest()
        )


if __name__ == "__main__":
    unittest.main()
