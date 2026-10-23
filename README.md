# AI Research & Analysis Workflow Tool

A repeatable Python toolkit for preparing research work orders, validating an eight-stage human-controlled workflow, organizing conversation records, and checking least-privilege authorization before a future model call.

Requires Python 3.10+. The original `ai-workflow` intake CLI uses the standard library. The unified validator additionally uses `jsonschema>=4.23,<5`.

The toolkit does not execute a model, conduct external research, verify factual truth, or connect to PostgreSQL. Its workflow and storage schemas are reference implementations; the authorization gate must be called by any future execution adapter before model invocation.

## What it produces

- A concise understanding of the requested task and a normalized intake record.
- Targeted blocking questions for unanswered correctness-critical requirements. A blocked work order explicitly instructs the assistant to stop before substantive work.
- A machine-readable `gate_status` of `blocked` or `cleared`; `cleared` means intake is complete enough to start, not that the research or requested task is complete.
- Proposed assumptions labeled **not approved**; the assistant is instructed not to treat them as requirements without requester approval.
- A research plan with mandatory citation expectations, a design plan, implementation expectations, usage directions, and a verification checklist.
- An assistant-ready prompt that preserves the same clarification gate and citation rules.
- Output as plain text, GitHub-flavored Markdown, or JSON.

## Quick start

```bash
python3 ai_workflow_tool.py
```

Answer the intake questions. The tool writes a Markdown work order to standard output by default. Questions marked required correspond to the blocking gate; optional context is retained when supplied. If a required answer is missing, the generated work order says **BLOCKED** and the assistant-ready prompt tells the assistant to ask and stop.

## Install as a Python package

Install the built wheel with pip:

```bash
python3 -m pip install ./dist/ai_research_workflow_tool-1.0.0-py3-none-any.whl
ai-workflow --help
```

To build the wheel and source archive from a checkout, install the build extra and run:

```bash
python3 -m pip install '.[build]'
python3 -m build --sdist --wheel
```

This creates artifacts in `dist/`. The package uses the proprietary/no-license declaration; no open-source reuse rights are granted. These artifacts are locally built and are not uploaded to PyPI or another package index.

Save output to a new file:

```bash
python3 ai_workflow_tool.py --format markdown --output work-order.md
python3 ai_workflow_tool.py --format text --output work-order.txt
python3 ai_workflow_tool.py --format json --output work-order.json
```

An existing output file is never replaced by default. To intentionally replace it, add `--force`:

```bash
python3 ai_workflow_tool.py --format json --output work-order.json --force
```

## Non-interactive use

Provide a UTF-8 JSON object whose keys match the intake fields. Missing keys become empty values and are reported as blockers; unknown keys and non-scalar values are rejected.

```json
{
  "goal": "Assess the evidence for the proposed approach",
  "deliverable_type": "research report",
  "domain": "the specified topic area",
  "audience": "project team",
  "success_criteria": "claims are sourced and recommendations address stated constraints",
  "constraints": "use authoritative sources and stay within the requested scope",
  "deadline": "as specified by the requester",
  "inputs_available": "links or documents supplied for this task",
  "output_format": "Markdown"
}
```

Save that object to a file and run:

```bash
python3 ai_workflow_tool.py --intake-file intake.json --format json --output work-order.json
```

## Intake fields

| Field | Required to pass the clarification gate? | Purpose |
|---|---:|---|
| `goal` | Yes | Exact outcome sought |
| `deliverable_type` | Yes | Report, code, plan, checklist, or other deliverable |
| `domain` | No | Subject area context |
| `audience` | No | Intended readers or users |
| `success_criteria` | Yes | Measurable definition of done |
| `constraints` | Yes | Technical, policy, scope, length, budget, or other limits |
| `deadline` | No | Timing context |
| `inputs_available` | No | Supplied documents, links, data, or context |
| `output_format` | Yes | Required final format |

Only five fields are blocking by default. Optional context is clearly labeled when absent and is not silently invented. The question set is defined in `ai_workflow_tool.py` and can be adjusted for a team's process.

## Citation and assumption policy

Citations are mandatory for material factual claims in the research workflow. The generated instructions require source title, publisher or author, date when available, and a direct URL or precise document locator. They also tell the assistant not to fabricate citations, to distinguish evidence from inference, and to disclose source limitations. Proposed assumptions are not approved automatically.

## Commands

```text
python3 ai_workflow_tool.py --help
python3 ai_workflow_tool.py --version
python3 -m unittest discover -s tests -v
```

## Unified workflow runtime

The additional runtime validates the fixed `scope → clarification → research → design → safety_review → draft → human_review → release` lifecycle. It checks strict JSON Schema structure, source-ID resolution, timestamp offsets and order, risk gates, and human release approval.

```bash
python3 -m pip install -e .
unified-workflow init workflow.json --id case-001
unified-workflow validate workflow.json
unified-workflow validate-system unified_system.example.json
# Equivalent from a source checkout:
python3 unified_workflow.py init workflow.json
python3 unified_workflow.py validate workflow.json
python3 unified_workflow.py validate-system unified_system.example.json
```

The starter record is not released; populate and review it before changing any status. `conversation_store.py` provides explicit a–f tagged items, provenance links, chronological rendering, candidate duplicate suggestions, and logged non-destructive restructuring. Similarity is only a candidate-finding aid. `security_policy.py` fails closed for unknown/high risk and capability escalation; it records a digest rather than request content. No model call is connected by this repository.

`workflow.schema.json` is the Draft 2020-12 contract. `timethread_schema.sql` is PostgreSQL 16+ DDL requiring `pgcrypto` and `vector`; apply it only to a database you control. Its vector dimensions and HNSW index are design choices, not performance guarantees.

`unified_system.schema.json` is the broader architecture manifest: component inventory, L0–L6 layers, four research-planning blocks, six research stages, seven verification gates, the separate eight-stage workflow, information categories, four audit pillars, defensive matrix, and qualification evidence. `unified_system.example.json` is a pending reference manifest. Released status is conditionally rejected unless the required stages, gates, audits, disclosure, scope, and human approval pass. JSON Schema cannot by itself resolve cross-record identifiers or prove real-world verification; `validate-system` adds ordering and link checks.

See [`docs/unified-system.md`](docs/unified-system.md) for the component map and qualification limits, and [`docs/security-matrix.md`](docs/security-matrix.md) for the least-privilege preflight and unverified defense assertions.

## Project structure

```text
ai-research-workflow-tool/
├── ai_workflow_tool.py
├── unified_workflow.py
├── workflow.schema.json
├── unified_system.schema.json
├── unified_system.example.json
├── conversation_store.py
├── security_policy.py
├── timethread_schema.sql
├── tests/
│   ├── test_ai_workflow_tool.py
│   ├── test_unified_workflow.py
│   ├── test_conversation_store.py
│   ├── test_security_policy.py
│   └── test_unified_system_schema.py
├── docs/
│   ├── architecture.md
│   ├── acceptance.md
│   ├── unified-system.md
│   └── security-matrix.md
├── .github/workflows/ci.yml
├── .gitignore
├── CONTRIBUTING.md
├── SECURITY.md
├── CHANGELOG.md
├── pyproject.toml
└── README.md
```

## Compatibility and licensing

Requires Python 3.10 or newer. The repository intentionally has no open-source license file: public visibility alone does not grant reuse rights. The repository owner should choose and add a license before inviting reuse or redistribution.
