from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
from unified_workflow import validate_system_config

ROOT = Path(__file__).resolve().parents[1]


class UnifiedSystemSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / "unified_system.schema.json").read_text(encoding="utf-8"))
        cls.example = json.loads((ROOT / "unified_system.example.json").read_text(encoding="utf-8"))

    def test_schema_is_valid_draft_2020_12(self):
        Draft202012Validator.check_schema(self.schema)

    def test_example_manifest_passes(self):
        self.assertEqual(validate_system_config(self.example), [])

    def test_released_workflow_requires_gates_audit_and_human_approval(self):
        candidate = copy.deepcopy(self.example)
        candidate["workflow"]["release_status"] = "released"
        self.assertTrue(validate_system_config(candidate))

    def _release_ready_manifest(self):
        candidate = copy.deepcopy(self.example)
        candidate["workflow"]["release_status"] = "released"
        expected = ["completed", "completed", "completed", "completed", "pass", "completed", "approved", "released"]
        for stage, status in zip(candidate["workflow"]["stages"], expected):
            stage["status"] = status
        for stage in candidate["research_method"]["research_stages"]:
            stage["status"] = "completed"
        for gate in candidate["research_method"]["verification_gates"]:
            gate["status"] = "passed"
        for pillar in candidate["pre_output_audit"].values():
            if isinstance(pillar, dict):
                pillar["status"] = "passed"
        candidate["pre_output_audit"]["disclosure_complete"] = True
        candidate["human_authority"]["release_approval"] = {
            "approved": True, "approver": "reviewer-1", "approved_at": "2026-10-23T00:00:00+00:00"
        }
        candidate["unresolved_issues"] = []
        return candidate

    def test_release_passes_when_all_declared_conditions_are_met(self):
        candidate = self._release_ready_manifest()
        self.assertEqual(validate_system_config(candidate), [])

    def test_any_pending_verification_gate_blocks_release(self):
        candidate = self._release_ready_manifest()
        candidate["research_method"]["verification_gates"][3]["status"] = "pending"
        self.assertTrue(validate_system_config(candidate))

    def test_any_incomplete_research_stage_blocks_release(self):
        candidate = self._release_ready_manifest()
        candidate["research_method"]["research_stages"][2]["status"] = "pending"
        self.assertTrue(validate_system_config(candidate))

    def test_governance_layers_are_a_closed_ordered_tuple(self):
        candidate = copy.deepcopy(self.example)
        candidate["governance_layers"][0]["id"] = "L1"
        self.assertTrue(validate_system_config(candidate))

    def test_unknown_conversation_link_rejected(self):
        candidate = copy.deepcopy(self.example)
        candidate["information_model"]["items"] = [{
            "item_id": "i1", "turn_index": 1, "raw_text": "source", "normalized_terms": [],
            "tag": "a", "topic_id": "t1", "source": "user", "location": "turn 1",
            "verification_status": "unverified", "sensitive": False,
            "links": {"references": ["missing"]}
        }]
        self.assertTrue(any("unknown item_id" in e for e in validate_system_config(candidate)))

    def test_nonchronological_items_rejected(self):
        candidate = copy.deepcopy(self.example)
        base = {"raw_text":"x", "normalized_terms":[], "tag":"a", "topic_id":"t1", "source":"user", "location":"turn", "verification_status":"unverified", "sensitive":False}
        candidate["information_model"]["items"] = [
            {"item_id":"i1", "turn_index":2, **base},
            {"item_id":"i2", "turn_index":1, **base}
        ]
        self.assertTrue(any("nondecreasing" in e for e in validate_system_config(candidate)))


if __name__ == "__main__":
    unittest.main()
