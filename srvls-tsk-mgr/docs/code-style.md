# Code style

These conventions apply to the Python Lambda handler and SAM template.

## Python

- Use Python 3.11-compatible syntax and four spaces for indentation.
- Use `snake_case` for variables and functions, and `UPPER_SNAKE_CASE` for
  module-level constants.
- Keep the Lambda entry point named `handler` and make HTTP API event handling
  explicit.
- Prefer standard-library modules before third-party imports; keep imports
  grouped and separated by a blank line.
- Use f-strings for readable messages and `logging` for operational messages.
- Validate request bodies and surface unexpected storage failures as server
  errors; do not silently hide errors.
- Keep the DynamoDB resource at module scope for reuse across Lambda
  invocations.
- Read deployment-specific values from environment variables rather than
  hard-coding resource names.
- Keep helpers and changes focused; avoid abstractions for one-off operations.

## AWS SAM and configuration

- Define AWS resources, IAM permissions, environment variables, and API routes
  in `template.yaml`.
- Grant the Lambda only the DynamoDB actions it needs on the project table.
- Use CloudFormation references for resource names and ARNs instead of
  hard-coding them.
- Do not commit credentials, private keys, local environment files, SAM build
  output, or personal deployment configuration.

## Documentation

- Keep deployment and usage instructions in the project `README.md`.
- Put architecture and implementation conventions in `docs/`.
- Write architecture diagrams in Mermaid format.
