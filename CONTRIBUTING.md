# Contributing

Contributions that improve correctness, clarity, accessibility, or maintainability are welcome.

## Before opening a change

1. Open an issue for substantial behavior changes so the expected behavior can be discussed.
2. Keep the project standard-library-only at runtime unless maintainers agree to a dependency change.
3. Preserve the requirement-first gate: missing correctness-critical information must remain visible and must not be silently guessed.
4. Keep mandatory citation requirements and the assistant-ready prompt aligned across text, Markdown, and JSON output.
5. Do not add incomplete functionality, TODOs, stubs, or placeholder content.

## Local validation

```bash
python3 -m unittest discover -s tests -v
python3 ai_workflow_tool.py --help
python3 ai_workflow_tool.py --version
```

Add or update tests for behavior changes. Tests should use temporary directories for file operations and should not require network access or credentials.

## Pull requests

Describe the behavior change, rationale, tests run, and any compatibility impact. Do not include personal or confidential task data in fixtures. CI runs the standard-library test suite on supported Python versions.

## License

The repository currently has no open-source license. Do not assume that public availability grants permission to reuse, modify, or redistribute the project. Ask the repository owner to add a license before making licensing claims.
