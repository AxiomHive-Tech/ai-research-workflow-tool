# Unified system: implementation and boundaries

## Inputs reconciled

The implementation combines (1) the eight-stage workflow and acceptance criteria in the supplied workflow PDFs, (2) the assistant research/evidence/presentation standard, and (3) the conversation organization and safety requirements in the supplied pasted specifications. The original `ai-workflow` work-order generator remains available.

## Components

- `ai_workflow_tool.py`: interactive or JSON intake; blocking clarification gate; text, Markdown, and JSON work orders; generated prompt includes evidence, privacy, relevance, framework accuracy, respectful communication, and literal technical-language constraints.
- `workflow.schema.json` + `unified_workflow.py`: Draft 2020-12 closed eight-stage tuple, strict object shapes, runtime checks for source references, unique IDs, corroboration metadata, timestamp offsets/order, high-risk safety review, unsupported claims, and release/human approval reconciliation.
- `conversation_store.py`: explicit a–f tagging supplied by caller, atomic source records, provenance and relationship links, chronological topic ordering, normalization of Axiom Hive, candidate-only similarity, append-only restructure events, and on-demand four-heading rendering.
- `security_policy.py`: least-privilege scope check and fail-closed risk preflight intended to run before any future model execution. Denial audit records contain a request digest, not raw request contents.
- `timethread_schema.sql`: PostgreSQL 16 reference DDL for branches, messages, workflow payloads, source and claim records, claim-source links, 1536-dimensional vectors, HNSW, and an outbox table.

## Security and human authority

No model adapter, network client, automatic semantic risk classifier, or database connector is included. The security preflight requires an explicit risk assessment from an approved review process and does not infer harmful intent from text. It denies elevated, high, or unknown risk, and denies any capability not in the explicit grant set. A future model integration must call this gate before execution, use narrowly scoped grants, and retain a human review path. This local library alone cannot enforce controls on an external model or deployment.

The outbox and database schema provide storage structures, not access control, authentication, encryption policy, operational monitoring, or proof of secure deletion. PostgreSQL DDL has not been applied to a live database as part of this change.

## Conversation records

Each item retains verbatim text after configured name normalization, source/location provenance, a–f label, topic, chronological turn index, status and sensitivity flags, and explicit links. Similarity produces candidate duplicates only; a caller must explicitly create a duplicate link. No deletion API is provided. Topic merges that include contradiction links require explicit user approval. Restructure events retain before/after data and rationale.

## Acceptance evidence

Run `python -m pip install -e .` and `python -m unittest discover -s tests -v`. The test suite covers both earlier work-order behavior and the new workflow, authorization, and conversation-record modules. Performance metrics are not claimed. Standards references are design guidance, not certification or a claim of legal compliance.

## Additional consolidated governance requirements

The latest synthesis describes an L0–L6 governance architecture (practitioner basis; constitutional standard; conduct specifications; research workflow; defensive architecture; reference/information model; operational artifacts). These are governance layers, not equivalents of the eight workflow stages or executable modules. The source relationship between Axiom Hive and Collective Hive is reported as unresolved; this implementation makes no claim to resolve it.

Before research collection, the supplied method calls for four planning blocks: philosophy (knowledge/support/uncertainty), ideology (principles and affected people), methodology (search, inclusion/exclusion, analysis), and ethical language (clarity, accessibility, terminology, disclosure). It separately specifies six research stages (setup, rule establishment, planning, collection/analysis, review, communication) and seven verification gates (scope, planning, source records, claim labels, verification, adherence, disclosure). These process stages and gates are separate from the technical eight-stage state machine. They are documented here as requirements for further implementation, not represented as completed automated controls.

The source model proposes claim categories (fact, estimate, interpretation, hypothesis, recommendation), source tiers 1–4, statement relationships (explicit statement, corroborated claim, inference), and verification statuses (verified primary, verified secondary, corrected, unverified, requires confirmation). Corroboration and inference may coexist; generated text and source support are separate dimensions. Current runtime support is partial: the workflow schema records source metadata, claim support status, and optional source-statement/corroboration/inference labels, but does not implement the full tier taxonomy or substantive verification process.

A pre-output audit is described across accuracy, safety, privacy, and fairness, with disclosure, adherence, and scope controls. The current implementation supplies workflow gates and a separate least-privilege preflight only; it does not execute a complete four-pillar audit. See [`security-matrix.md`](security-matrix.md) for control-by-control standing.

## Qualification and release status

A requirement, an implementation, and its verification result remain separate records. The repository tests demonstrate only the tested behaviors in this checkout; they do not establish system-level qualification. No supplied performance target is claimed as achieved. Qualification metrics, adversarial tests, independent evaluation, deployment authorization, and the full Q1–Q7 and multi-agent role contracts are not implemented because the controlling criteria were not fully specified. Human-authorized release remains a workflow condition, not evidence that an external system enforces it.
