# Serverless task manager

This AWS SAM project provides a small task-management API using API Gateway,
AWS Lambda, and DynamoDB. It supports creating, listing, retrieving, updating,
deleting, and completing tasks.

## Project documentation

- [Architecture](docs/architecture.md): request flow, AWS resources, and
  security boundaries.
- [Code style](docs/code-style.md): Python and AWS SAM conventions.
- [To-do](docs/todo.md): planned authentication, user isolation, and other
  improvements.

## Deploy

Prerequisites: AWS CLI credentials with permission to deploy the resources in
`template.yaml`, and AWS SAM CLI.

Run these commands from this directory:

```sh
sam validate --lint
sam build
sam deploy --guided
```

After deployment, copy the `ApiUrl` output. The API currently has no
authentication, and all tasks are shared by every caller. Do not expose this
starter API to untrusted users or store private task data until authentication
and user-specific access controls are implemented.

## Use the API

Set the deployed URL before running the examples:

```sh
export API_URL="https://YOUR_API_ID.execute-api.YOUR_REGION.amazonaws.com"
```

Create a task:

```sh
curl -X POST "$API_URL/tasks" \
  -H 'content-type: application/json' \
  -d '{"title":"Read about serverless","description":"Review the architecture"}'
```

List tasks, or retrieve one using its `task_id` from the create response:

```sh
curl "$API_URL/tasks"
curl "$API_URL/tasks/TASK_ID"
```

Update task text, mark it complete, or delete it:

```sh
curl -X PUT "$API_URL/tasks/TASK_ID" \
  -H 'content-type: application/json' \
  -d '{"title":"Review serverless architecture"}'
curl -X PATCH "$API_URL/tasks/TASK_ID/complete"
curl -X DELETE "$API_URL/tasks/TASK_ID"
```

## Scope and limits

- A task title is required and limited to 200 characters. A description is
  optional and limited to 2,000 characters.
- Listing tasks scans the table and is intended for a small demonstration,
  not a high-volume production workload.
- API Gateway invokes a single Lambda function. The function validates
  requests and returns JSON errors; operational messages are written to
  CloudWatch Logs.
- Authentication, user-specific tasks, richer validation and error handling,
  notifications, and additional operational controls are tracked in
  [the to-do list](docs/todo.md).
