# Acceptance Criteria

| Requirement | Observable evidence |
|---|---|
| Interactive requirements intake | Running with no arguments asks for the nine intake fields. |
| Upfront clarification gate | Missing any required field creates targeted blocking questions, `gate_status: blocked`, and an explicit BLOCKED state. |
| No silent assumption approval | Proposed assumptions are labeled unapproved in all generated formats. |
| Research → design → implementation sequence | Work order and assistant-ready prompt state the ordered stages and prohibit substantive work while blockers remain. |
| Mandatory citations | Research plan, work-order policy, and assistant-ready prompt require traceable citations and prohibit fabricated sources. |
| Complete work order and prompt | All sections are generated from the same validated intake. |
| Three output formats | `text`, `markdown`, and `json` are supported; JSON is parseable and preserves all work-order fields. |
| Cleared-state meaning | Complete intake produces `gate_status: cleared`; this is not represented as research completion or task delivery. |
| JSON file intake | Valid UTF-8 objects are accepted; malformed JSON, non-object roots, unknown keys, and non-scalar values are rejected. |
| Safe output files | Existing files are not replaced without `--force`; successful writes use a temporary file and atomic replacement. |
| No external runtime dependencies | The CLI imports only Python standard-library modules. |
| Automated regression coverage | `python -m unittest discover -s tests -v` passes. |
| Maintainer workflow | CI runs tests for Python 3.10, 3.11, 3.12, and 3.13. |

## Done criteria

A release is ready when all acceptance criteria are met, the README commands work from a clean checkout, CI passes, and the public repository description does not imply that the CLI performs research or that the project has an open-source license.
