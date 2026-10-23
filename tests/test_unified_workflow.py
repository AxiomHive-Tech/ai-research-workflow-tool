from __future__ import annotations

import copy
import unittest

from unified_workflow import STAGES, new_workflow, validate_workflow


def completed_workflow():
    data = new_workflow("test-1")
    data["status"] = "released"
    now = "2026-10-22T10:00:00+00:00"
    for i, stage in enumerate(data["stages"]):
        stamp = f"2026-10-22T{10+i:02d}:00:00+00:00"
        stage["started_at"] = stamp
        stage["completed_at"] = stamp
        if stage["stage"] in {"scope", "clarification", "research", "design", "draft"}:
            stage["status"] = "completed"
    data["stages"][4]["status"] = "pass"
    data["stages"][4]["record"] = {"risk_items": [{"risk_id": "r1", "residual_risk": "low"}]}
    data["stages"][6]["status"] = "approved"
    data["stages"][6]["record"] = {"approved": True, "reviewer": "human"}
    data["stages"][7]["status"] = "released"
    data["stages"][7]["record"] = {"decision": "released"}
    data["released_at"] = "2026-10-22T18:00:00+00:00"
    return data


class UnifiedWorkflowTests(unittest.TestCase):
    def test_template_has_fixed_eight_stages_and_is_not_released(self):
        data = new_workflow()
        self.assertEqual(tuple(s["stage"] for s in data["stages"]), STAGES)
        self.assertEqual(data["status"], "in_progress")
        self.assertEqual(validate_workflow(data), [])

    def test_valid_explicitly_approved_release_passes(self):
        self.assertEqual(validate_workflow(completed_workflow()), [])

    def test_reordered_stages_rejected(self):
        data = new_workflow()
        data["stages"][0], data["stages"][1] = data["stages"][1], data["stages"][0]
        self.assertTrue(any("schema" in e for e in validate_workflow(data)))

    def test_undeclared_properties_rejected(self):
        data = new_workflow()
        data["surprise"] = True
        self.assertTrue(validate_workflow(data))

    def test_unknown_source_rejected(self):
        data = new_workflow()
        data["claims"] = [{"claim_id": "c1", "statement": "claim", "source_ids": ["missing"], "support_status": "supported"}]
        self.assertTrue(any("unknown source_id" in e for e in validate_workflow(data)))

    def test_high_residual_risk_cannot_pass(self):
        data = new_workflow()
        data["stages"][4]["status"] = "pass"
        data["stages"][4]["record"] = {"risk_items": [{"risk_id": "r1", "residual_risk": "high"}]}
        self.assertTrue(any("high residual risk" in e for e in validate_workflow(data)))

    def test_malformed_risk_record_is_rejected_without_crashing(self):
        data = new_workflow()
        data["stages"][4]["record"] = {"risk_items": ["not-an-object"]}
        errors = validate_workflow(data)
        self.assertTrue(errors)
        self.assertTrue(any("schema" in error for error in errors))

    def test_release_without_human_approval_rejected(self):
        data = completed_workflow()
        data["stages"][6]["record"]["approved"] = False
        self.assertTrue(any("human_review approval" in e for e in validate_workflow(data)))

    def test_unsupported_claim_blocks_release(self):
        data = completed_workflow()
        data["claims"] = [{"claim_id": "c1", "statement": "unsupported", "source_ids": [], "support_status": "unsupported"}]
        self.assertTrue(any("unsupported claims" in e for e in validate_workflow(data)))

    def test_naive_timestamps_rejected(self):
        data = new_workflow()
        data["stages"][0]["started_at"] = "2026-01-01T10:00:00"
        self.assertTrue(validate_workflow(data))

    def test_corrobation_requires_independent_source_records(self):
        data = new_workflow()
        data["sources"] = [{"source_id":"s1","title":"S1","url":"https://example.test"}]
        data["claims"] = [{"claim_id":"c1","statement":"claim","source_ids":["s1"],"support_status":"supported","analysis_type":"corroborated"}]
        self.assertTrue(any("at least two" in e for e in validate_workflow(data)))


if __name__ == "__main__":
    unittest.main()
