# To-do

The following work is intentionally outside this starter implementation.
Complete these items before using the API for private or production workloads.

- [ ] **Authentication:** Add Amazon Cognito or another trusted identity
  provider, require authenticated requests, and validate the caller's identity
  in the API.
- [ ] **User-specific tasks:** Store an owner identifier with each task, key
  DynamoDB access by owner and task ID, and enforce ownership in every
  read/update/delete operation. Add tests proving one user cannot access
  another user's tasks.
- [ ] **Input validation:** Expand validation with explicit content-type,
  request-size, task-ID, and field-level constraints. Keep error responses
  consistent and document the API schema.
- [ ] **Error handling:** Define stable error codes and response formats for
  AWS service failures, throttling, malformed routes, and conditional-write
  conflicts; avoid exposing internal exception details.
- [ ] **Logging:** Add structured JSON logs, request correlation IDs, and
  retention/alerting guidance. Never log credentials, authorization headers,
  or sensitive task content.
- [ ] **Notifications:** Decide which task events should notify users, then
  add an appropriate delivery service such as Amazon SNS or Amazon SES,
  including user preferences and failure handling.
