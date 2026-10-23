# Changelog

## Unreleased

- Reject workflow and system-manifest release claims by default unless a trusted embedding application provides an approval verifier; the CLI provides none and cannot authenticate approvers.
- Pass a defensive copy of the complete document to the verifier and fail closed when it rejects approval or raises an exception.
- Add regression tests for forged/self-asserted CLI approvals, verifier rejection, verifier errors, and accepted test-verifier callbacks.

## 1.1.0 — 2026-10-23

- Add the unified eight-stage research workflow runtime, strict workflow schema, evidence/source validation, safety review gates, and explicit human approval for release.
- Add a least-privilege security preflight and a chronological, provenance-aware conversation store with non-destructive restructuring controls.
- Add the comprehensive system manifest schema for components, governance layers, planning blocks, research stages, verification gates, audit pillars, and qualification.
- Harden release and qualification gates: require explicit approval, a present empty unresolved-issues register, nonempty planning, evidence references that resolve through the registry, and reviewed evidence for release.
- Require independently verified components and evidence-backed met metrics before a manifest may claim qualified status.
- Add command-line end-to-end integration coverage from intake and work-order generation through workflow release and system-manifest validation.
- Apply Ruff lint fixes and format all Python source and test files.
- Update the GitHub Actions test matrix to install declared runtime dependencies before importing and testing the workflow validators.
- Verification: 54 tests passed; Ruff lint and formatting checks passed; both JSON schemas passed Draft 2020-12 validation; package source and wheel builds succeeded. Bandit found two low-severity warnings for controlled subprocess use in the integration-test harness and no medium/high findings.

## 1.0.0

- Add interactive and JSON-file intake for research and analysis tasks.
- Add a clarification gate for missing goal, deliverable type, success criteria, constraints, and output format.
- Generate structured work orders and assistant-ready prompts in plain text, Markdown, and JSON.
- Make citations mandatory in research instructions; keep proposed assumptions explicitly unapproved.
- Add safe output-file handling, standard-library tests, documentation, and GitHub Actions CI.
