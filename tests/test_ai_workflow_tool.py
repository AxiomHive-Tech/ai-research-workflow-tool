from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import ai_workflow_tool as tool

COMPLETE_INTAKE = {
    "goal": "Compare two approaches",
    "deliverable_type": "analysis report",
    "domain": "data systems",
    "audience": "engineering team",
    "success_criteria": "recommendation supported by evidence",
    "constraints": "standard library only",
    "deadline": "next week",
    "inputs_available": "none",
    "output_format": "Markdown",
}


class IntakeTests(unittest.TestCase):
    def test_normalization_includes_optional_fields_and_trims(self) -> None:
        intake = tool.normalize_intake({"goal": "  Decide  "})
        self.assertEqual(intake["goal"], "Decide")
        self.assertEqual(intake["audience"], "")
        self.assertEqual(set(intake), {field[0] for field in tool.INTAKE_FIELDS})

    def test_unknown_fields_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown intake field"):
            tool.normalize_intake({"goal": "x", "unexpected": "y"})

    def test_non_scalar_values_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "scalar"):
            tool.normalize_intake({"goal": ["not", "scalar"]})

    def test_required_fields_create_targeted_blockers(self) -> None:
        blockers = tool.find_blockers(tool.normalize_intake({"goal": "A goal"}))
        self.assertEqual(len(blockers), 4)
        self.assertIn("What measurable criteria define success?", blockers)

    def test_complete_intake_has_no_blockers(self) -> None:
        self.assertEqual(tool.find_blockers(tool.normalize_intake(COMPLETE_INTAKE)), [])


class WorkOrderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.work_order = tool.build_workflow(
            COMPLETE_INTAKE, generated_at="2026-01-01T00:00:00+00:00"
        )

    def test_citation_policy_is_mandatory(self) -> None:
        self.assertTrue(self.work_order["citation_policy"]["required"])
        self.assertEqual(self.work_order["gate_status"], "cleared")
        self.assertIn(
            "Citations are mandatory", " ".join(self.work_order["research_plan"])
        )

    def test_assistant_prompt_preserves_gate_and_citations(self) -> None:
        prompt = self.work_order["assistant_ready_prompt"]
        self.assertIn("CLARIFICATION GATE", prompt)
        self.assertIn("CITATIONS — MANDATORY", prompt)
        self.assertIn("Do not begin substantive research", prompt)

    def test_all_formats_are_complete(self) -> None:
        text = tool.render(self.work_order, "text")
        markdown = tool.render(self.work_order, "markdown")
        parsed = json.loads(tool.render(self.work_order, "json"))
        for marker in (
            "1) Understanding",
            "8) Verification Checklist",
            "9) Assistant-Ready Prompt",
        ):
            self.assertIn(marker, text)
        self.assertIn("## 9. Assistant-Ready Prompt", markdown)
        self.assertEqual(
            parsed["assistant_ready_prompt"], self.work_order["assistant_ready_prompt"]
        )

    def test_blocked_work_order_clearly_stops_execution(self) -> None:
        work_order = tool.build_workflow({"goal": "A goal"}, generated_at="fixed")
        self.assertTrue(work_order["blocking_questions"])
        self.assertEqual(work_order["gate_status"], "blocked")
        self.assertIn("STATUS: BLOCKED", tool.render(work_order, "text"))
        self.assertIn(
            "ask only those questions and stop", work_order["assistant_ready_prompt"]
        )
        self.assertIn(
            "resolve the clarification gate",
            work_order["assistant_ready_prompt"].lower(),
        )

    def test_unknown_format_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported output format"):
            tool.render(self.work_order, "html")


class FileAndCliTests(unittest.TestCase):
    def test_intake_json_must_be_an_object(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "list.json"
            path.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "root must be an object"):
                tool._load_intake(path)

    def test_file_write_refuses_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.md"
            tool._write_output(path, "first", False)
            with self.assertRaisesRegex(ValueError, "already exists"):
                tool._write_output(path, "second", False)
            self.assertEqual(path.read_text(encoding="utf-8"), "first")
            tool._write_output(path, "second", True)
            self.assertEqual(path.read_text(encoding="utf-8"), "second")

    def test_main_writes_json_from_intake_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "intake.json"
            target = Path(directory) / "work-order.json"
            source.write_text(json.dumps(COMPLETE_INTAKE), encoding="utf-8")
            result = tool.main(
                [
                    "--intake-file",
                    str(source),
                    "--format",
                    "json",
                    "--output",
                    str(target),
                ]
            )
            self.assertEqual(result, 0)
            data = json.loads(target.read_text(encoding="utf-8"))
            self.assertFalse(data["blocking_questions"])
            self.assertTrue(data["citation_policy"]["required"])


if __name__ == "__main__":
    unittest.main()
