#!/usr/bin/env python3
"""Unified human-support research and design workflow validator."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import sys
import sysconfig
from collections.abc import Callable
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent
_SCHEMA_CANDIDATES = (
    ROOT / "workflow.schema.json",
    Path(sysconfig.get_path("data"))
    / "share"
    / "ai-research-workflow-tool"
    / "workflow.schema.json",
)
SCHEMA_PATH = next(
    (candidate for candidate in _SCHEMA_CANDIDATES if candidate.is_file()),
    _SCHEMA_CANDIDATES[0],
)
_SYSTEM_SCHEMA_CANDIDATES = (
    ROOT / "unified_system.schema.json",
    Path(sysconfig.get_path("data"))
    / "share"
    / "ai-research-workflow-tool"
    / "unified_system.schema.json",
)
SYSTEM_SCHEMA_PATH = next(
    (candidate for candidate in _SYSTEM_SCHEMA_CANDIDATES if candidate.is_file()),
    _SYSTEM_SCHEMA_CANDIDATES[0],
)
STAGES = (
    "scope",
    "clarification",
    "research",
    "design",
    "safety_review",
    "draft",
    "human_review",
    "release",
)
ApprovalVerifier = Callable[[dict[str, Any]], bool]


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def new_workflow(workflow_id: str = "workflow-001") -> dict[str, Any]:
    """Create a valid, blocked-by-default workflow starter record."""
    now = _utc_now()
    stages = []
    for name in STAGES:
        stages.append(
            {
                "stage": name,
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "record": {},
            }
        )
    stages[0].update(
        status="completed",
        started_at=now,
        completed_at=now,
        record={"objective": "", "scope_in": [], "scope_out": []},
    )
    stages[7]["record"] = {"decision": "blocked"}
    return {
        "schema_version": "1.0",
        "workflow_id": workflow_id,
        "status": "in_progress",
        "created_at": now,
        "released_at": None,
        "sources": [],
        "claims": [],
        "stages": stages,
    }


def _parse_time(value: Any, label: str, errors: list[str]) -> dt.datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        errors.append(f"{label}: timestamp must be a string or null")
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{label}: invalid ISO 8601 timestamp")
        return None
    if parsed.utcoffset() is None:
        errors.append(f"{label}: timestamp must include explicit UTC offset")
        return None
    return parsed


def _approval_verification_error(
    document: dict[str, Any],
    approval_verifier: ApprovalVerifier | None,
    release_label: str,
) -> str | None:
    """Require a trusted caller to verify approval over a defensive document copy."""
    if approval_verifier is None:
        return (
            f"{release_label}: a trusted approval verifier is required; "
            "the CLI does not authenticate approvers"
        )
    try:
        verified = approval_verifier(copy.deepcopy(document))
    except Exception:  # noqa: BLE001 -- any verifier failure must fail closed
        return f"{release_label}: trusted approval verification failed closed"
    if verified is not True:
        return f"{release_label}: trusted approval verifier rejected the approval"
    return None


def validate_workflow(
    data: Any,
    schema_path: Path = SCHEMA_PATH,
    *,
    approval_verifier: ApprovalVerifier | None = None,
) -> list[str]:
    """Validate a workflow; released records require a caller-trusted verifier.

    The verifier must authenticate the approver and bind approval to the complete
    document. The CLI does not configure a verifier and therefore rejects release
    claims rather than treating caller-supplied approval fields as authorization.
    """
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Cannot load workflow schema: {exc}"]
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    structural = sorted(
        validator.iter_errors(data),
        key=lambda error: list(map(str, error.absolute_path)),
    )
    errors = [
        f"schema {('/' + '/'.join(map(str, e.absolute_path))) if e.absolute_path else '/'}: {e.message}"
        for e in structural
    ]
    if errors or not isinstance(data, dict):
        return errors

    sources = data["sources"]
    source_ids = [source["source_id"] for source in sources]
    if len(source_ids) != len(set(source_ids)):
        errors.append("sources: source_id values must be unique")
    known_sources = set(source_ids)
    claim_ids: list[str] = []
    for claim in data["claims"]:
        claim_ids.append(claim["claim_id"])
        for source_id in claim["source_ids"]:
            if source_id not in known_sources:
                errors.append(
                    f"claim {claim['claim_id']}: reference to unknown source_id {source_id!r}"
                )
        if claim["support_status"] == "unsupported":
            continue
        if (
            claim.get("analysis_type") == "corroborated"
            and len(claim["source_ids"]) < 2
        ):
            errors.append(
                f"claim {claim['claim_id']}: corroborated claims require at least two source references"
            )
    if len(claim_ids) != len(set(claim_ids)):
        errors.append("claims: claim_id values must be unique")

    previous_completion: dt.datetime | None = None
    previous_stage_closed = True
    for index, stage in enumerate(data["stages"]):
        label = f"stages[{index}]/{stage['stage']}"
        start = _parse_time(stage["started_at"], f"{label}/started_at", errors)
        end = _parse_time(stage["completed_at"], f"{label}/completed_at", errors)
        if start and end and end < start:
            errors.append(
                f"{label}: completed_at timestamp must not precede started_at"
            )
        if start and previous_completion and start < previous_completion:
            errors.append(
                f"{label}: started_at timestamp must not precede prior stage completion"
            )
        if index > 0 and start and not previous_stage_closed:
            errors.append(f"{label}: cannot start before the prior stage is completed")
        if index > 0 and start and previous_completion is None:
            errors.append(
                f"{label}: prior stage must have completed_at before this stage starts"
            )
        if end:
            previous_completion = end
        previous_stage_closed = stage["status"] not in {
            "pending",
            "needs_input",
            "blocked",
            "changes_required",
            "assumed",
        }
        if stage["stage"] == "safety_review":
            if stage["status"] == "pass" and not stage["record"].get("risk_items"):
                errors.append(
                    "safety_review: passing review requires recorded risk_items"
                )
            for risk in stage["record"].get("risk_items", []):
                if risk.get("residual_risk") == "high" and stage["status"] == "pass":
                    errors.append(
                        "safety_review: high residual risk prevents a pass decision"
                    )

    released = data["status"] == "released"
    release_stage = data["stages"][7]
    review = data["stages"][6]
    if released:
        if data.get("released_at") is None:
            errors.append(
                "release: released_at is required when workflow status is released"
            )
        if release_stage["status"] != "released":
            errors.append("release: workflow and release-stage status must align")
        if (
            review["status"] != "approved"
            or review["record"].get("approved") is not True
        ):
            errors.append("release: explicit human_review approval is required")
        for stage in data["stages"][:6]:
            if stage["status"] not in ("completed", "pass", "not_required"):
                errors.append(
                    f"release: required stage {stage['stage']} is not complete"
                )
        if data["stages"][4]["status"] != "pass":
            errors.append("release: safety_review must pass before release")
        unresolved = [
            c["claim_id"]
            for c in data["claims"]
            if c["support_status"] == "unsupported"
        ]
        if unresolved:
            errors.append(
                "release: unsupported claims must be resolved or removed: "
                + ", ".join(unresolved)
            )
    elif data.get("released_at") is not None:
        errors.append(
            "release: released_at must be null unless workflow status is released"
        )
    if release_stage["status"] == "released" and not released:
        errors.append(
            "release: release-stage status cannot be released unless root status is released"
        )
    if released and not errors:
        approval_error = _approval_verification_error(
            data, approval_verifier, "release"
        )
        if approval_error:
            errors.append(approval_error)
    return errors


def validate_system_config(
    data: Any,
    schema_path: Path = SYSTEM_SCHEMA_PATH,
    *,
    approval_verifier: ApprovalVerifier | None = None,
) -> list[str]:
    """Validate a system manifest; released workflows require a trusted verifier.

    The verifier must authenticate the approver and bind approval to the complete
    manifest. The CLI does not configure a verifier and rejects release claims.
    """
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Cannot load system schema: {exc}"]
    structural = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(data),
        key=lambda error: list(map(str, error.absolute_path)),
    )
    errors = [
        f"schema {('/' + '/'.join(map(str, e.absolute_path))) if e.absolute_path else '/'}: {e.message}"
        for e in structural
    ]
    if errors or not isinstance(data, dict):
        return errors
    evidence_records = data["evidence_registry"]
    evidence_ids = [record["evidence_id"] for record in evidence_records]
    if len(evidence_ids) != len(set(evidence_ids)):
        errors.append("evidence_registry: evidence_id values must be unique")
    known_evidence = set(evidence_ids)
    evidence_references: list[str] = []

    def collect_evidence_refs(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"evidence_refs", "record_refs"} and isinstance(child, list):
                    evidence_references.extend(
                        ref for ref in child if isinstance(ref, str)
                    )
                elif key == "decision_ref" and isinstance(child, str):
                    evidence_references.append(child)
                else:
                    collect_evidence_refs(child)
        elif isinstance(value, list):
            for child in value:
                collect_evidence_refs(child)

    collect_evidence_refs(data)
    for reference in evidence_references:
        if reference not in known_evidence:
            errors.append(
                f"evidence reference {reference!r} does not resolve to evidence_registry"
            )
    items = data["information_model"]["items"]
    item_ids = [item["item_id"] for item in items]
    if len(item_ids) != len(set(item_ids)):
        errors.append("information_model.items: item_id values must be unique")
    turns = [item["turn_index"] for item in items]
    if turns != sorted(turns):
        errors.append(
            "information_model.items: items must be in nondecreasing turn order"
        )
    known = set(item_ids)
    for item in items:
        for relation, targets in item.get("links", {}).items():
            for target in targets:
                if target not in known:
                    errors.append(
                        f"item {item['item_id']}: {relation} link references unknown item_id {target!r}"
                    )
    if data["workflow"]["release_status"] == "released" and not errors:
        approval_error = _approval_verification_error(
            data, approval_verifier, "system release"
        )
        if approval_error:
            errors.append(approval_error)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create and validate a unified, human-controlled research workflow."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser(
        "init", help="write a blocked-by-default workflow template"
    )
    init.add_argument("output", type=Path)
    init.add_argument("--id", default="workflow-001")
    init.add_argument("--force", action="store_true")
    check = commands.add_parser(
        "validate",
        help="validate structure, evidence links, chronology, risks, and release gates",
    )
    check.add_argument("workflow", type=Path)
    system_check = commands.add_parser(
        "validate-system",
        help="validate the comprehensive component and governance manifest",
    )
    system_check.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            if args.output.exists() and not args.force:
                raise ValueError(
                    f"Output already exists: {args.output} (use --force to replace it)"
                )
            args.output.write_text(
                json.dumps(new_workflow(args.id), indent=2) + "\n", encoding="utf-8"
            )
            print(f"Created blocked-by-default workflow: {args.output}")
            return 0
        data = json.loads(
            (
                args.manifest if args.command == "validate-system" else args.workflow
            ).read_text(encoding="utf-8")
        )
        errors = (
            validate_system_config(data)
            if args.command == "validate-system"
            else validate_workflow(data)
        )
        if errors:
            print("INVALID")
            for error in errors:
                print(f"- {error}")
            return 1
        if args.command == "validate-system":
            print("VALID: system manifest structure and cross-record checks passed")
        else:
            print("VALID: structure and workflow gates passed")
        return 0
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
