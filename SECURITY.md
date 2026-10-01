# Security

llm-wiki is a local command-line tool. A vulnerability report should describe the code defect, not the contents of a private library.

## Reporting

Use a private GitHub security advisory on this repository.

Do not open a public issue, pull request, or chat message that includes:

- source documents, notes, or attachments
- ingest manifests, OCR text, or file paths from a real library
- credentials, tokens, or `.env` contents

Describe the affected command, the version, and a synthetic way to reproduce the problem. If a fix needs a sample file, make that file synthetic.

## Scope

Report issues in the framework code: path handling, archive extraction, subprocess use, and anything that would send library content off the machine without an explicit user action.

User notes stored under `raw/` or `wiki/` are the operator's data. This project does not provide a hosted place to store them.
