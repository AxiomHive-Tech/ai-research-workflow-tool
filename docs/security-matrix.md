# Defensive control matrix and qualification boundary

## Operational matrix implemented in this repository

| Step | Control | Software evidence | Boundary |
|---|---|---|---|
| 1. Intake | A caller supplies request text, requested scopes, granted scopes, and a risk assessment. | `authorize_model_execution(...)` input contract. | No semantic detector or automatic classifier is included. |
| 2. Assessment | Only `low`, `elevated`, `high`, or `unknown` are accepted; `high` and `unknown` fail closed. | `security_policy.py` decision tests. | The quality of an externally supplied assessment is not established by this module. |
| 3. Record | Return a decision, timestamp, capability sets, and SHA-256 request digest. | `Decision.audit_record(...)`. | Request contents are not retained by the audit record; external audit persistence is not implemented. |
| 4. Protective response | Deny empty or over-broad scopes; allow only explicit low-risk scoped work. Elevated-risk work is denied pending separate policy review. | Unit tests for least privilege and fail-closed outcomes. | This function does not call a model and cannot enforce controls in an unconnected service. |
| 5. Review | Caller may retain the metadata record and connect it to a human review process. | Returned audit mapping. | Storage, alerting, incident response, and review operations are not implemented here. |

The control is a procedural preflight interface, not a model-integrated safety system. A future execution adapter must call it before any model invocation and must not allow alternate execution paths to bypass it.

## Assertions that remain unverified

The supplied defensive design describes the following as architectural assertions, not demonstrated properties: absence of attackable targets, non-damageability, hostile actions backfiring, isolation of malicious actors, and immunity to malicious effort. This code does **not** claim any of those properties. Threat modeling, adversarial evaluation, independent review, deployment controls, and measurable acceptance criteria remain necessary.

The system records no raw denied request. A digest can support correlation but cannot explain the content or replace an incident record. No claim is made that a hash prevents misuse or proves safety.

System-manifest release and qualification states now require evidence references that resolve through `evidence_registry`; review/verification status, stage/gate/audit evidence, explicit human approval, and zero unresolved issues are checked by schema/runtime logic. These checks establish completeness of declarations, not authenticity of referenced files, reviewer identity, or whether a source substantiates a claim.
