#!/usr/bin/env python3
"""AI Research & Analysis Workflow Tool.

Collect task requirements and produce a complete, structured work order plus an
assistant-ready prompt in plain text, Markdown, or JSON. Uses only the Python
standard library.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sys
from typing import Any

__version__ = "1.0.0"

INTAKE_FIELDS: tuple[tuple[str, str, bool], ...] = (
    ("goal", "Goal / outcome", True),
    ("deliverable_type", "Deliverable type (report/code/plan/etc.)", True),
    ("domain", "Domain / topic area", False),
    ("audience", "Intended audience", False),
    ("success_criteria", "Success criteria (measurable)", True),
    ("constraints", "Constraints (stack, policy, length, deadline, etc.)", True),
    ("deadline", "Deadline / urgency", False),
    ("inputs_available", "Inputs available (documents, links, data, context)", False),
    ("output_format", "Required output format", True),
)

BLOCKING_QUESTIONS: dict[str, str] = {
    "goal": "What exact goal or outcome should the work achieve?",
    "deliverable_type": "What deliverable is required (for example, report, code, plan, or checklist)?",
    "success_criteria": "What measurable criteria define success?",
    "constraints": "What constraints must be respected (technology, policy, length, budget, or deadline)?",
    "output_format": "What output format is required?",
}


def _clean(value: Any) -> str:
    """Convert a supplied intake value to a safe, trimmed display string."""
    if value is None:
        return ""
    if not isinstance(value, (str, int, float, bool)):
        raise ValueError("Intake values must be strings or scalar values.")
    return str(value).strip()


def normalize_intake(raw: dict[str, Any]) -> dict[str, str]:
    """Return a complete normalized intake mapping; unknown keys are rejected."""
    known = {key for key, _, _ in INTAKE_FIELDS}
    unknown = sorted(set(raw) - known)
    if unknown:
        raise ValueError("Unknown intake field(s): " + ", ".join(unknown))
    return {key: _clean(raw.get(key, "")) for key, _, _ in INTAKE_FIELDS}


def find_blockers(intake: dict[str, str]) -> list[str]:
    """Return unanswered correctness-critical questions in stable order."""
    return [question for key, question in BLOCKING_QUESTIONS.items() if not intake.get(key, "").strip()]


def collect_intake(stream_in: Any = sys.stdin, stream_out: Any = sys.stdout) -> dict[str, str]:
    """Interactively collect the task details. EOF or Ctrl-C exits cleanly."""
    values: dict[str, str] = {}
    print("Provide the request details. Answer what you know; required gaps will be flagged.\n", file=stream_out)
    try:
        for key, label, required in INTAKE_FIELDS:
            suffix = " (required to proceed)" if required else " (optional)"
            values[key] = input(f"{label}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nIntake cancelled.", file=sys.stderr)
        raise SystemExit(1)
    return normalize_intake(values)


def build_workflow(intake_raw: dict[str, Any], generated_at: str | None = None) -> dict[str, Any]:
    """Build the machine-readable work order and assistant-ready prompt."""
    intake = normalize_intake(intake_raw)
    blockers = find_blockers(intake)
    def label(key: str) -> str:
        return intake[key] if intake[key] else "Not provided"

    understanding = (
        f"Prepare a {label('deliverable_type')} about {label('domain')} to achieve: {label('goal')}. "
        f"The intended audience is {label('audience')}. Success criteria: {label('success_criteria')}. "
        f"Constraints: {label('constraints')}. Required output format: {label('output_format')}."
    )

    research_plan = [
        "Restate the request and confirm its scope boundaries before research.",
        "Resolve every blocking question before beginning substantive research, design, or implementation.",
        "Convert remaining unknowns into answerable research questions and state approved assumptions explicitly.",
        "Gather evidence from reputable primary sources first; use secondary sources only where needed and label them clearly.",
        "Citations are mandatory: cite material factual claims with source title, publisher/author, publication date when available, and a direct URL or precise document locator; distinguish evidence from inference.",
        "Cross-check important claims against independent authoritative evidence when available; record source limitations and dates.",
        "Synthesize findings and validate them against the stated success criteria and constraints.",
    ]
    design = [
        "Choose the deliverable structure or software components that directly satisfy the success criteria.",
        "Specify inputs, outputs, interfaces, and acceptance criteria for every section or component.",
        "Identify edge cases, failure modes, validation, and error handling before implementation.",
        "Define a verification method (automated tests, source checks, or review checklist) for each acceptance criterion.",
    ]
    implementation = [
        "Do not start implementation while any blocking question remains unanswered or explicitly waived by the requester.",
        "Produce complete, working code or actionable content; do not include TODOs, stubs, mocks, or placeholder sections.",
        "Include setup, execution, and validation instructions whenever code or a repeatable process is delivered.",
        "Cite external factual claims and identify assumptions only after the requester approves them.",
    ]
    usage = [
        "Review the understanding, blocking questions, constraints, and requested output format.",
        "Answer each blocking question, or explicitly waive it, before the assistant proceeds.",
        "Approve, reject, or revise proposed assumptions; unapproved assumptions are not requirements.",
        "Use the assistant-ready prompt below as the task instruction once the clarification gate is cleared.",
    ]
    verification = [
        "Every blocking question is answered or explicitly waived before substantive execution.",
        "The completed deliverable matches the requested type, audience, format, and measurable success criteria.",
        "Mandatory citations support material factual claims and are traceable to their sources.",
        "No TODOs, stubs, mocks, or placeholders remain in the final deliverable.",
        "Constraints, edge cases, and error handling are addressed; tests or evidence demonstrate completion.",
        "Setup and run instructions are complete when applicable.",
    ]
    work_order: dict[str, Any] = {
        "schema_version": "1.0",
        "generated_at": generated_at or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "gate_status": "blocked" if blockers else "cleared",
        "understanding": understanding,
        "intake": intake,
        "blocking_questions": blockers,
        "assumptions": {
            "status": "none approved",
            "proposed": [
                "Prefer reputable primary sources and cite them whenever research is required.",
                "If trade-offs exist, compare at least two feasible options and recommend one with reasons.",
                "If implementation is requested, deliver fully working code without placeholders.",
            ],
            "instruction": "Proposed assumptions require requester approval; do not treat them as accepted requirements.",
        },
        "citation_policy": {
            "required": True,
            "requirements": "Cite material factual claims with source title, publisher/author, date when available, and URL or precise locator.",
        },
        "research_plan": research_plan,
        "design": design,
        "implementation_expectations": implementation,
        "usage": usage,
        "verification_checklist": verification,
    }
    work_order["assistant_ready_prompt"] = build_assistant_prompt(work_order)
    return work_order


def build_assistant_prompt(work_order: dict[str, Any]) -> str:
    """Render an instruction prompt that preserves the clarification gate."""
    intake = work_order["intake"]
    lines = [
        "You are completing the task described below. Follow the sequence and acceptance rules exactly.",
        "",
        "CLARIFICATION GATE — MUST FOLLOW",
        "Do not begin substantive research, design, or implementation until every blocking question is answered or explicitly waived by the requester. If any blocking questions remain, ask only those questions and stop; do not continue with research, design, implementation, or claims of completion. Do not silently fill gaps with assumptions.",
        "",
        "TASK REQUIREMENTS",
    ]
    lines.extend(f"- {key.replace('_', ' ').title()}: {value or 'Not provided'}" for key, value in intake.items())
    lines.extend([
        "",
        "CITATIONS — MANDATORY",
        "Support material factual claims with citations identifying source title, publisher/author, date when available, and direct URL or precise document locator. Prefer authoritative primary sources, distinguish evidence from inference, and disclose limitations. Never fabricate sources or citations.",
        "",
        "EXECUTION SEQUENCE",
        "1. Confirm the scope and resolve the clarification gate.",
        "2. Research using traceable evidence and cite material claims.",
        "3. Present a design or deliverable outline with inputs, outputs, edge cases, and acceptance criteria.",
        "4. Implement or write the complete requested deliverable only after requirements are clear.",
        "5. Verify every acceptance criterion and provide usage/run instructions where applicable.",
        "",
        "QUALITY RULES",
        "- Do not include TODOs, stubs, mocks, or placeholders in the final output.",
        "- Do not claim a test or verification was performed unless it actually was.",
        "- Respect the requester's audience, output format, constraints, and approved assumptions.",
        "- Report limitations honestly and ask for missing information when it affects correctness.",
    ])
    return "\n".join(lines)


def render_text(work_order: dict[str, Any]) -> str:
    """Render a readable plain-text work order and assistant prompt."""
    sections: list[tuple[str, Any]] = [
        ("1) Understanding", work_order["understanding"]),
        ("2) Blocking Questions", work_order["blocking_questions"]),
        ("3) Assumptions (not approved)", [*work_order["assumptions"]["proposed"], work_order["assumptions"]["instruction"]]),
        ("4) Research Plan", work_order["research_plan"]),
        ("5) Design", work_order["design"]),
        ("6) Implementation Expectations (No Mocks/Stubs/Placeholders)", work_order["implementation_expectations"]),
        ("7) Usage / Run Instructions", work_order["usage"]),
        ("8) Verification Checklist", work_order["verification_checklist"]),
        ("9) Assistant-Ready Prompt", work_order["assistant_ready_prompt"]),
    ]
    out = ["AI Research & Analysis Workflow Document", f"Generated: {work_order['generated_at']}"]
    for title, body in sections:
        out.extend(["", title])
        if isinstance(body, list):
            out.extend([f"- {item}" for item in body] if body else ["(none)"])
        else:
            out.append(str(body))
    if work_order["blocking_questions"]:
        out.extend(["", "STATUS: BLOCKED — answer or explicitly waive the questions above before substantive execution."])
    else:
        out.extend(["", "STATUS: UNBLOCKED — requirements are complete enough to proceed."])
    return "\n".join(out) + "\n"


def render_markdown(work_order: dict[str, Any]) -> str:
    """Render a GitHub-flavored Markdown work order and assistant prompt."""
    out = [
        "# AI Research & Analysis Workflow Document",
        "",
        f"**Generated:** {work_order['generated_at']}",
        f"**Status:** {'BLOCKED — resolve or explicitly waive the questions below before substantive execution.' if work_order['blocking_questions'] else 'UNBLOCKED — requirements are complete enough to proceed.'}",
        "",
        "## 1. Understanding",
        "",
        work_order["understanding"],
        "",
        "## 2. Blocking Questions",
        "",
    ]
    out.extend([f"- {q}" for q in work_order["blocking_questions"]] if work_order["blocking_questions"] else ["None."])
    out.extend(["", "## 3. Assumptions (not approved)", ""])
    out.extend([f"- {x}" for x in work_order["assumptions"]["proposed"]])
    out.extend(["", f"> {work_order['assumptions']['instruction']}", "", "## 4. Research Plan", ""])
    out.extend(f"{i}. {item}" for i, item in enumerate(work_order["research_plan"], 1))
    out.extend(["", "## 5. Design", ""])
    out.extend(f"- {item}" for item in work_order["design"])
    out.extend(["", "## 6. Implementation Expectations (No Mocks/Stubs/Placeholders)", ""])
    out.extend(f"- {item}" for item in work_order["implementation_expectations"])
    out.extend(["", "## 7. Usage / Run Instructions", ""])
    out.extend(f"{i}. {item}" for i, item in enumerate(work_order["usage"], 1))
    out.extend(["", "## 8. Verification Checklist", ""])
    out.extend(f"- [ ] {item}" for item in work_order["verification_checklist"])
    out.extend(["", "## 9. Assistant-Ready Prompt", "", "```text", work_order["assistant_ready_prompt"], "```", ""])
    return "\n".join(out)


def render(work_order: dict[str, Any], output_format: str) -> str:
    """Serialize a work order using one of the supported formats."""
    if output_format == "text":
        return render_text(work_order)
    if output_format == "markdown":
        return render_markdown(work_order)
    if output_format == "json":
        return json.dumps(work_order, indent=2, ensure_ascii=False) + "\n"
    raise ValueError(f"Unsupported output format: {output_format}")


def _load_intake(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"Cannot read intake file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("The intake JSON root must be an object mapping field names to values.")
    return value


def _write_output(path: Path, content: str, force: bool) -> None:
    """Write output atomically; avoid accidental overwrite unless requested."""
    path = path.expanduser()
    parent = path.parent
    if not parent.exists() or not parent.is_dir():
        raise ValueError(f"Output directory does not exist: {parent}")
    if path.exists() and not force:
        raise ValueError(f"Output already exists: {path} (use --force to replace it)")
    temp_path: Path | None = None
    try:
        import tempfile
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            temp_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists() and not force:
            raise ValueError(f"Output already exists: {path} (use --force to replace it)")
        os.replace(temp_path, path)
    except OSError as exc:
        raise ValueError(f"Cannot write output file {path}: {exc}") from exc
    finally:
        if temp_path is not None and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect research-task requirements and produce a work order plus assistant-ready prompt.",
        epilog="Without --intake-file, the tool starts interactive intake. Required fields are validated as blockers, not silently assumed.",
    )
    parser.add_argument("--format", choices=("text", "markdown", "json"), default="markdown", help="Output encoding (default: markdown).")
    parser.add_argument("--intake-file", type=Path, help="Read intake fields from a UTF-8 JSON object instead of prompting.")
    parser.add_argument("--output", type=Path, help="Write to a file instead of stdout; existing files require --force.")
    parser.add_argument("--force", action="store_true", help="Allow replacing an existing --output file.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    if args.force and args.output is None:
        parser.error("--force requires --output")
    try:
        raw = _load_intake(args.intake_file) if args.intake_file else collect_intake()
        work_order = build_workflow(raw)
        content = render(work_order, args.format)
        if args.output:
            _write_output(args.output, content, args.force)
        else:
            sys.stdout.write(content)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
