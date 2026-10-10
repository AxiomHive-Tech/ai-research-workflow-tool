# Architecture

## Scope

`ai_workflow_tool.py` is a local, dependency-free command-line application that converts task requirements into a structured research/analysis work order and a companion assistant-ready prompt. It does not perform research, call an AI model, or transmit intake data. It provides a repeatable operating procedure for a later assistant session.

## Data flow

1. The CLI collects intake interactively or loads a UTF-8 JSON object.
2. `normalize_intake` validates known field names, normalizes scalar values to trimmed strings, and ensures every supported field exists.
3. `find_blockers` checks the five correctness-critical fields in stable order: goal, deliverable type, success criteria, constraints, and output format.
4. `build_workflow` constructs a versioned work-order mapping, mandatory citation policy, proposed-but-unapproved assumptions, research/design/implementation/verification instructions, and an assistant-ready prompt.
5. `render` serializes the same work order as plain text, Markdown, or JSON.
6. The CLI writes to standard output or atomically creates/replaces a requested file. Existing files are protected unless `--force` is supplied.

## Core structures

The intake record is a JSON-compatible mapping from the nine field names documented in the README to strings. The work order is a versioned mapping with `schema_version`, `generated_at`, `understanding`, `intake`, `blocking_questions`, `assumptions`, `citation_policy`, `research_plan`, `design`, `implementation_expectations`, `usage`, `verification_checklist`, and `assistant_ready_prompt`.

## Failure behavior

Malformed JSON, a non-object intake root, unknown intake keys, non-scalar intake values, unsupported formats, missing output directories, and accidental file replacement produce a clear error on standard error and a nonzero exit status. EOF or Ctrl-C during interactive intake exits with status 1. Missing required answers do not cause invented values: the tool generates a blocked work order with targeted questions and an explicit stop instruction.

## Security and privacy

The tool has no network access or runtime dependencies. It reads only the selected intake file and writes only to standard output or the requested destination. Generated work orders may contain sensitive information; users are responsible for handling those files appropriately.
