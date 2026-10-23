# User guide

This guide walks a new user through the toolkit from install to a validated workflow. It does not call any AI model: the tools prepare, check and record work that a person or assistant carries out.

## Key terms

- **Work order:** A written brief for a research task, produced from your answers to intake questions.
- **Gate:** A check that must pass before work continues. The intake gate is `blocked` until the required answers are given, then `cleared`.
- **Workflow:** A record of eight fixed stages from scope to release, stored as a JSON file.
- **Schema:** A rules file that says which fields a JSON file may contain.
- **Validate:** Check a file against its schema plus extra rules, and list every problem found.

## 1. Install

Requires Python 3.10 or newer.

```bash
python3 -m pip install -e .
```

This also installs the `jsonschema` library the validator needs and creates two commands, `ai-workflow` and `unified-workflow`.

## 2. Create a work order

```bash
ai-workflow --format markdown --output work-order.md
```

Answer the questions. Five answers are required: goal, deliverable type, success criteria, constraints and output format. If one is missing, the work order says BLOCKED and tells the assistant to ask and stop. `cleared` only means the intake is complete enough to start, not that the research is done.

To run without prompts, put the answers in a JSON file and use `--intake-file intake.json`.

## 3. Start a workflow record

```bash
unified-workflow init workflow.json --id my-case-001
```

The new file is not released. Only the first stage (scope) is marked completed.

## 4. Fill it in and validate

Edit `workflow.json` as work progresses: add sources, add claims that cite those sources, and update each stage's status and timestamps in order. Then check it:

```bash
unified-workflow validate workflow.json
```

The output is `VALID` or a list of problems. Exit code 0 means valid, 1 means problems were found, and 2 means the file could not be read.

## 5. Release rules

A workflow can only be marked `released` when all of these hold:

1. Stages 1 to 6 are complete, and the safety review status is `pass`.
2. A person approved it in the human_review stage (`approved` is true).
3. No claim is marked `unsupported`.
4. `released_at` is set, and it is empty (null) for any workflow that is not released.

The validator checks that these records exist and are consistent. It cannot confirm that sources are real or that a claim is true.

## 6. Check the larger system manifest (optional)

```bash
unified-workflow validate-system unified_system.example.json
```

This checks the architecture manifest and confirms that every evidence reference points to an entry in its evidence registry.

## Limits to know

- No model is called by this toolkit.
- Passing validation does not mean the content is accurate or safe.
- The PostgreSQL schema (`timethread_schema.sql`) is a reference design and is not connected to the Python code.
- The repository has no open-source license, so reuse needs the owner's permission.
