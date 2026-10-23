from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class EndToEndWorkflowIntegrationTests(unittest.TestCase):
    def _run(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            args, cwd=ROOT, capture_output=True, text=True, check=False
        )

    def test_intake_to_evidence_gated_release_via_clis(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            intake_path = tmp / "intake.json"
            work_order_path = tmp / "work-order.json"
            workflow_path = tmp / "workflow.json"
            manifest_path = tmp / "system-manifest.json"
            intake_path.write_text(
                json.dumps(
                    {
                        "goal": "Validate the research workflow against a controlled fixture",
                        "deliverable_type": "integration result",
                        "domain": "software validation",
                        "audience": "maintainers",
                        "success_criteria": "both workflow and manifest validators accept a human-approved fixture",
                        "constraints": "offline test fixture only",
                        "deadline": "test run",
                        "inputs_available": "synthetic in-test evidence",
                        "output_format": "JSON",
                    }
                ),
                encoding="utf-8",
            )

            intake = self._run(
                sys.executable,
                "ai_workflow_tool.py",
                "--intake-file",
                str(intake_path),
                "--format",
                "json",
                "--output",
                str(work_order_path),
            )
            self.assertEqual(intake.returncode, 0, intake.stdout + intake.stderr)
            work_order = json.loads(work_order_path.read_text(encoding="utf-8"))
            self.assertEqual(work_order["gate_status"], "cleared")
            self.assertTrue(work_order["citation_policy"]["required"])

            created = self._run(
                sys.executable,
                "unified_workflow.py",
                "init",
                str(workflow_path),
                "--id",
                "integration-case",
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
            workflow["sources"] = [
                {
                    "source_id": "fixture-source-1",
                    "title": "Controlled integration fixture",
                    "publisher": "Local test fixture",
                    "url": "fixture://integration/source-1",
                }
            ]
            workflow["claims"] = [
                {
                    "claim_id": "fixture-claim-1",
                    "statement": "The fixture was supplied to the validator.",
                    "source_ids": ["fixture-source-1"],
                    "support_status": "supported",
                    "analysis_type": "source_statement",
                    "limitations": "Synthetic test data; not an external factual claim.",
                }
            ]
            base = datetime(2026, 1, 1, tzinfo=timezone.utc)
            statuses = [
                "completed",
                "completed",
                "completed",
                "completed",
                "pass",
                "completed",
                "approved",
                "released",
            ]
            for index, (stage, status) in enumerate(zip(workflow["stages"], statuses)):
                start = base + timedelta(seconds=2 * index)
                end = start + timedelta(seconds=1)
                stage.update(
                    status=status,
                    started_at=start.isoformat(),
                    completed_at=end.isoformat(),
                )
                stage["record"] = {"integration_fixture": True}
            workflow["stages"][4]["record"] = {
                "risk_items": [{"risk_id": "fixture-risk-1", "residual_risk": "low"}]
            }
            workflow["stages"][6]["record"] = {
                "approved": True,
                "approver": "integration-test-operator",
            }
            workflow["stages"][7]["record"] = {"decision": "released"}
            workflow["status"] = "released"
            workflow["released_at"] = workflow["stages"][7]["completed_at"]
            workflow_path.write_text(json.dumps(workflow, indent=2), encoding="utf-8")
            workflow_check = self._run(
                sys.executable, "unified_workflow.py", "validate", str(workflow_path)
            )
            self.assertEqual(
                workflow_check.returncode,
                0,
                workflow_check.stdout + workflow_check.stderr,
            )
            self.assertIn("VALID", workflow_check.stdout)

            manifest = json.loads(
                (ROOT / "unified_system.example.json").read_text(encoding="utf-8")
            )
            evidence_id = "tests/test_unified_workflow.py"
            manifest["workflow"]["release_status"] = "released"
            release_statuses = [
                "completed",
                "completed",
                "completed",
                "completed",
                "pass",
                "completed",
                "approved",
                "released",
            ]
            for stage, status in zip(manifest["workflow"]["stages"], release_statuses):
                stage["status"] = status
                stage["evidence_refs"] = [evidence_id]
            for stage in manifest["research_method"]["research_stages"]:
                stage["status"] = "completed"
                stage["record_refs"] = [evidence_id]
            for gate in manifest["research_method"]["verification_gates"]:
                gate["status"] = "passed"
                gate["evidence_refs"] = [evidence_id]
            for pillar in manifest["pre_output_audit"].values():
                if isinstance(pillar, dict):
                    pillar["status"] = "passed"
                    pillar["evidence_refs"] = [evidence_id]
            manifest["pre_output_audit"].update(
                disclosure_complete=True, scope_confirmed=True
            )
            manifest["human_authority"]["release_approval"] = {
                "approved": True,
                "approver": "integration-test-operator",
                "approved_at": "2026-01-01T00:00:20+00:00",
                "decision_ref": evidence_id,
            }
            for evidence in manifest["evidence_registry"]:
                evidence["verification_status"] = "reviewed"
            manifest["unresolved_issues"] = []
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            manifest_check = self._run(
                sys.executable,
                "unified_workflow.py",
                "validate-system",
                str(manifest_path),
            )
            self.assertEqual(
                manifest_check.returncode,
                0,
                manifest_check.stdout + manifest_check.stderr,
            )
            self.assertIn("VALID: system manifest", manifest_check.stdout)


if __name__ == "__main__":
    unittest.main()
