"""Fail-closed authorization checks to run before any model execution.

This module does not execute models or classify natural-language intent. Callers must
supply an explicit risk assessment from an approved review process. Denials retain
metadata and a one-way content digest, not the submitted content.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

VALID_RISK = {"low", "elevated", "high", "unknown"}


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    granted_scopes: tuple[str, ...]
    requested_scopes: tuple[str, ...]

    def audit_record(self, request_text: str) -> dict[str, object]:
        return {
            **asdict(self),
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "request_sha256": hashlib.sha256(request_text.encode("utf-8")).hexdigest(),
            "request_content_retained": False,
        }


def authorize_model_execution(
    *,
    request_text: str,
    requested_scopes: Iterable[str],
    granted_scopes: Iterable[str],
    risk_assessment: str,
    human_approval: bool = False,
) -> Decision:
    """Authorize only explicit, scoped, low-risk work; otherwise deny without executing."""
    requested = tuple(sorted(set(requested_scopes)))
    granted = tuple(sorted(set(granted_scopes)))
    if not isinstance(request_text, str) or not request_text.strip():
        return Decision(False, "empty or invalid request", granted, requested)
    if risk_assessment not in VALID_RISK:
        return Decision(False, "missing or invalid risk assessment", granted, requested)
    if not requested:
        return Decision(
            False, "no explicit capability was requested", granted, requested
        )
    if risk_assessment in {"high", "unknown"}:
        return Decision(
            False,
            "high or unknown risk fails closed before model execution",
            granted,
            requested,
        )
    if not set(requested).issubset(set(granted)):
        return Decision(
            False,
            "requested capability exceeds granted least-privilege scopes",
            granted,
            requested,
        )
    if risk_assessment == "elevated" and not human_approval:
        return Decision(
            False,
            "elevated-risk action requires explicit human approval",
            granted,
            requested,
        )
    if risk_assessment == "elevated" and human_approval:
        return Decision(
            False,
            "elevated-risk actions require a separate policy review; approval alone is insufficient",
            granted,
            requested,
        )
    return Decision(
        True, "explicit scopes granted and risk assessment is low", granted, requested
    )
