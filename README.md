# AI Research & Analysis Workflow Tool

A repeatable, code-backed Python CLI for turning a research or analysis request into a structured work order **and an assistant-ready prompt**. It enforces an explicit clarification gate, a research → design → implementation sequence, mandatory citations, and a no-placeholders quality bar.

The tool runs on Python 3.10+ and uses only the standard library. No account, API key, network connection, or third-party dependency is required.

The CLI prepares instructions only: it does not conduct research, produce the downstream requested deliverable, or independently verify citations.

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

## Project structure

```text
ai-research-workflow-tool/
├── ai_workflow_tool.py
├── tests/
│   └── test_ai_workflow_tool.py
├── docs/
│   ├── architecture.md
│   └── acceptance.md
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
