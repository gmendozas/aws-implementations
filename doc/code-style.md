# Code style

These conventions apply to the Python Lambda handlers and SAM template.

## Python

- Use Python 3.11-compatible syntax and four spaces for indentation.
- Use `snake_case` for variables and functions, and `UPPER_SNAKE_CASE` for
  module-level constants.
- Keep each Lambda entry point named `handler` and keep AWS event handling
  explicit.
- Prefer standard-library modules before third-party imports; keep imports
  grouped and separated by a blank line.
- Use f-strings for readable messages and `logging` for operational messages.
- Validate inputs and raise a specific exception for invalid data or failed
  downstream operations. Do not silently hide errors.
- Keep AWS clients at module scope for reuse across Lambda invocations.
- Read deployment-specific values, such as bucket names and voice IDs, from
  environment variables rather than hard-coding resource names.
- Keep helpers and changes focused; avoid adding abstractions for one-off
  operations.

## AWS SAM and configuration

- Define AWS resources, IAM permissions, environment variables, and
  deployment-time parameters in `template.yaml`.
- Grant each function only the permissions it needs.
- Use CloudFormation references for resource names and ARNs instead of
  hard-coding them.
- Do not commit credentials, private keys, local environment files, SAM build
  output, or personal deployment configuration.

## Documentation and samples

- Keep operational setup and usage instructions in `README.md`.
- Put architecture and implementation conventions in `doc/`.
- Keep sample text files short, UTF-8 encoded, and free of private or
  customer-provided content.
