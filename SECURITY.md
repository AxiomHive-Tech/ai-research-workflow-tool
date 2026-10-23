# Security Policy

## Reporting a vulnerability

Please do not publish credentials, private task data, or an exploitable vulnerability in a public issue. Contact the repository owner through a private GitHub security advisory if that feature is enabled, or another private channel already supplied by the owner. Include the affected version, impact, reproduction steps, and any safe mitigation.

## Scope and data handling

The CLI runs locally and does not make network requests. Intake and work-order generation use Python's standard library; workflow validation depends on `jsonschema`. The CLI has no identity provider and rejects release-status claims unless a trusted embedding application calls the library API with an approval verifier. Schema validation alone is not authenticated authorization. Intake files, conversation records, and generated work orders may contain sensitive information; store and share them according to your organization's policies. Do not commit confidential inputs, saved conversations, or generated work orders to the repository.

## Supported versions

Security fixes are applied to the current repository version. Users should upgrade to the latest reviewed release or commit.
