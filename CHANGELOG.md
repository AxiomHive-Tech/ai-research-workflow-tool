# Changelog

## Unreleased — Schema hardening (2026-10-23, `ee97c38`)

- Require explicit human approval and a present, empty unresolved-issues register before workflow release.
- Require nonempty planning blocks and evidence references for completed workflow/research stages, passed verification gates, audit pillars, and the approval decision.
- Add an evidence registry; reject duplicate evidence IDs and references that do not resolve. Release evidence must be marked reviewed or verified.
- Require every component to be independently verified, at least one evidence-backed metric to be met, and verified evidence records before marking the system qualified.
- Add regression coverage for the previously identified release and qualification bypasses.
- Validation: 53 automated tests passed; both schemas passed Draft 2020-12 validation; the sample system manifest and package-wheel contents were checked.

## 1.0.0

- Add interactive and JSON-file intake for research and analysis tasks.
- Add a clarification gate for missing goal, deliverable type, success criteria, constraints, and output format.
- Generate structured work orders and assistant-ready prompts in plain text, Markdown, and JSON.
- Make citations mandatory in research instructions; keep proposed assumptions explicitly unapproved.
- Add safe output-file handling, standard-library tests, documentation, and GitHub Actions CI.
