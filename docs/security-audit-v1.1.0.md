# Security Audit Report — v1.1.0

**Audit date:** 2026-10-23
**Tag:** `v1.1.0`
**Audited commit:** `2ec45784f309c63ac81256014066762b9f0e5b09` (`release: prepare v1.1.0`)
**Repository:** `AxiomHive-Tech/ai-research-workflow-tool`

## Executive summary

Automated checks found **no known vulnerabilities in the declared runtime or build dependency set**. Bandit reported two low-severity findings, both in the end-to-end test harness; it reported no medium- or high-severity findings. GitHub Actions passed on Python 3.10, 3.11, 3.12, and 3.13, including distribution build/install checks.

This is not a zero-risk or security-certification result. Review of the complete tagged tree identified significant trust-boundary and privacy limitations. In particular, the workflow validator checks approval fields in caller-supplied data but does not authenticate the approver. The repository documentation states that validation does not establish external enforcement or authenticate reviewers/evidence; downstream systems must not interpret a structural `VALID` result as proof of authorized approval.

The v1.1.0 release-preparation commit itself changes version/changelog metadata and CI dependency installation; no new application runtime code was added in that commit. The findings below describe the full v1.1.0 tree, including features introduced earlier in the release cycle.

## Automated scan results

| Check | Result |
|---|---|
| Bandit 1.9.4, repository Python scan | 2 low findings; 0 medium; 0 high. The findings are `B404` and `B603` for `subprocess` use in `tests/test_end_to_end_integration.py` (lines 4 and 16). The test invokes local commands with an argument list and does not use a shell. Bandit returns exit code 1 because it reports low findings. |
| `pip-audit` | No known vulnerabilities found in the declared `jsonschema>=4.23,<5`, `setuptools>=77`, and optional `build>=1.2` dependency ranges at scan time. This is a point-in-time advisory-database result, not a guarantee against future disclosures. |
| GitHub Actions | Passed for Python 3.10–3.13 and the distribution build/install job on the release candidate commit. |
| GitHub Dependabot alerts | Could not be queried: Dependabot alerts are disabled for this repository (GitHub API returned HTTP 403 with that reason). |

## Findings and residual risks

### 1. Approval fields are not authenticated — conditional high impact

`unified_workflow.py` (around lines 188–202) accepts `review.status == "approved"` and `review.record.approved is True` as the human-review condition. The validator does not authenticate the approver, verify their authority, or verify a signature. A caller able to edit the workflow JSON can self-assert those fields; the end-to-end test demonstrates fixture data using a literal approver and timestamp.

**Impact:** If a downstream deployment or release process treats this validator’s success as proof of human authorization, a caller who can submit or modify the JSON may bypass that authorization. This is a high-impact integration risk, not evidence of an authentication bypass in a service—the repository contains no authenticated release service. `docs/unified-system.md` and `docs/security-matrix.md` describe the implementation as declarative and state that external enforcement and reviewer identity are not established.

**Recommendation:** Keep the output explicitly structural, or place it behind an authenticated authorization service that verifies approver identity/authority and signed or otherwise trusted approval evidence before taking release actions.

### 2. `sensitive` does not redact conversation content — medium privacy risk

`conversation_store.py` records a sensitivity boolean, but `render()` includes `normalized_text` and `save()` serializes all item fields, including raw `text`, without redaction (`conversation_store.py`, around lines 324–375). Marking an item sensitive therefore does not prevent its content from appearing in rendered or saved output.

**Impact:** Callers may mistake the flag for a protection boundary and disclose sensitive content when exporting or rendering a store. The repository’s earlier security summary already records that the flag is not coupled to a privacy-review rule.

**Recommendation:** Clarify the flag’s meaning and provide explicit redacted rendering/export behavior, with tests that verify sensitive values do not appear in protected output paths.

### 3. Qualification and evidence statuses are declarative — medium assurance risk

The system manifest can declare qualification, verified components/evidence, and met metrics. Schema/runtime validation checks structure and reference resolution but does not authenticate evidence files, reviewer identity, signatures, test execution, or whether evidence substantiates a claim (`docs/security-matrix.md`; `docs/security-summary-schema-hardening.md`).

**Impact:** A manifest author can self-assert qualification fields. Downstream consumers must not treat a passing structural validation as independent certification or proof of security.

**Recommendation:** Bind qualification to trusted evidence ingestion, authenticated reviewers, and independently verified test results before using it as an assurance decision.

### 4. Manifest release-stage consistency gap — medium integrity risk

The existing security summary documents that the comprehensive system manifest may accept a mismatch between `workflow.release_status` and the individual release-stage status (`docs/security-summary-schema-hardening.md`, “Remaining limits and known issues”). This weakens the manifest as a release-status signal. The issue predates the v1.1.0 release-preparation commit.

**Recommendation:** Enforce the invariant for released and non-released states in both schema and runtime validation, with regression tests for mismatched values.

### 5. Generic workflow stage records remain permissive — low validation-integrity risk

Except for the safety-review record, generic stage `record` objects allow arbitrary properties (`workflow.schema.json`). Misspelled or unexpected fields may be accepted without being checked. This limitation is also disclosed in the earlier security summary.

**Recommendation:** Define closed, stage-specific record schemas where the record vocabulary is sufficiently specified.

### 6. Dependency ranges are not reproducibly locked — low supply-chain risk

Runtime and build dependencies are version-ranged rather than locked to a reviewed resolution. This is not a known vulnerable dependency finding, but it makes future builds sensitive to upstream releases and does not guarantee identical dependency resolution over time.

**Recommendation:** Consider a reviewed lock/constraints file for CI and release builds, with an explicit update process.

### 7. Security documentation has a dependency-scope mismatch — low documentation risk

`SECURITY.md` describes the CLI as standard-library-only, while v1.1.0 declares `jsonschema` as a runtime dependency in `pyproject.toml`. This does not itself create an exploit path, but it makes the dependency/security description inaccurate.

**Recommendation:** Update the security documentation to reflect the runtime dependency and its audit process.

## Conclusion

The dependency scan found no known advisories in the declared dependencies, and automated Python static analysis found no medium/high-severity findings. However, the full v1.1.0 source contains documented trust-boundary and privacy risks, especially if declarative approval or qualification fields are consumed as authenticated authorization or certification. No code or tag was modified during this audit; the report is an uncommitted local artifact.

## Post-audit authorization patch status (2026-10-23)

A follow-up local patch adds a trusted `approval_verifier` callback to `validate_workflow()` and `validate_system_config()`. Both APIs now reject released records by default; the CLI configures no verifier and rejects self-asserted release approval fields. When supplied by an embedding application, the verifier receives a defensive copy of the complete document; false results and exceptions fail closed. Regression tests cover both workflow and system-manifest release paths.

This patch does **not** implement an identity provider, key management, or a production signature verifier. The embedding application remains responsible for authenticating approver identity/authority and binding approval to the exact document. Direct JSON Schema validation remains structural and cannot establish approval authenticity. The existing v1.1.0 tag and release are unchanged; the patch and this report update are local and uncommitted. The post-patch suite has 57 passing tests, with Ruff lint/format checks, schema validation, and package builds passing.
