# Security summary: schema hardening

**Draft date:** 2026-10-23  
**Reviewed commit:** `ee97c38b68ffa8492ed63cafddf811fe3d5512ba` (`fix: harden schema release and qualification gates`)  
**Scope:** `unified_system.schema.json`, the system-manifest validator, its example manifest, and regression tests.

## Summary

This update addresses high-severity release and qualification bypasses found during review. The schema now requires explicit human approval and a present, empty unresolved-issues register for release. Passed workflow stages, research stages, verification gates, audit pillars, and approval decisions must cite evidence. Planning blocks must be populated, and evidence references must resolve to unique records in `evidence_registry`. Evidence records used for release must be marked reviewed or verified.

A system may be labeled `qualified` only when all required components are marked independently verified and cite evidence, at least one qualification metric is marked met with evidence, unresolved issues are absent, and referenced evidence records are marked verified.

## Controls added

- **Release authority:** `human_authority` is required; release requires `approved: true`, a named approver, timestamp, and a decision reference that resolves to the evidence registry.
- **Issue closure:** `unresolved_issues` is required and must be empty for release and qualification.
- **Evidence completeness:** release requires nonempty evidence references for each applicable workflow stage, research stage, verification gate, audit pillar, and approval decision. Planning blocks must be nonempty.
- **Evidence-reference integrity:** runtime validation rejects duplicate evidence IDs and references that do not resolve. The schema requires reviewed or verified evidence for release and verified evidence for qualification.
- **Qualification threshold:** every component must be `independently_verified`; at least one metric must be marked `met` and include evidence.
- **Regression protection:** tests cover missing approval, omitted issue register, empty evidence/planning, unresolved references, unreviewed release evidence, and unverified qualification components.

## Verification results

At the time of this draft:

- All **53 automated tests passed**.
- `workflow.schema.json` and `unified_system.schema.json` passed JSON Schema Draft 2020-12 meta-schema checks.
- `unified-workflow validate-system unified_system.example.json` passed.
- Adversarial probes confirmed rejection of omitted approval/issue fields, unconfirmed scope, unverified components labeled qualified, and unregistered evidence references.
- A wheel build included the comprehensive schema and example manifest.

## Remaining limits and known issues

Evidence references and their `reviewed`/`verified` labels are declarations. Validation checks presence and identifier resolution; it does not authenticate referenced files, signatures, reviewer identity, source truth, or whether evidence substantiates a claim. The schema does not provide automatic personal-data detection, external security monitoring, or deployment enforcement. No result here establishes independent system qualification or security certification.

The follow-up audit also noted medium-severity issues outside this hardening scope: the comprehensive manifest can accept a mismatch between `workflow.release_status` and the release-stage status outside the release conditional; nested workflow `record` objects accept arbitrary properties; and a conversation item’s `sensitive` flag is not coupled to a privacy-review rule. These remain candidates for separate remediation.

## References

- [Commit `ee97c38`](https://github.com/AxiomHive-Tech/ai-research-workflow-tool/commit/ee97c38b68ffa8492ed63cafddf811fe3d5512ba)
- [`unified_system.schema.json`](../unified_system.schema.json)
- [`unified_workflow.py`](../unified_workflow.py)
- [`test_unified_system_schema.py`](../tests/test_unified_system_schema.py)
