import json
import logging
import os
from datetime import datetime, timezone
from uuid import uuid4

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TASK_TABLE"])

MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000


class BadRequestError(Exception):
    pass


class NotFoundError(Exception):
    pass


def _response(status_code, payload=None):
    return {
        "statusCode": status_code,
        "headers": {"content-type": "application/json"},
        "body": "" if payload is None else json.dumps(payload),
    }


def _parse_body(event):
    body = event.get("body")
    if not isinstance(body, str):
        raise BadRequestError("Request body must be a JSON object.")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as error:
        raise BadRequestError("Request body must be valid JSON.") from error
    if not isinstance(payload, dict):
        raise BadRequestError("Request body must be a JSON object.")
    return payload


def _validated_text_fields(payload, *, creating):
    allowed_fields = {"title", "description"}
    unknown_fields = set(payload) - allowed_fields
    if unknown_fields:
        raise BadRequestError(
            f"Unsupported field(s): {', '.join(sorted(unknown_fields))}."
        )
    if creating and "title" not in payload:
        raise BadRequestError("The title field is required.")
    if not creating and not payload:
        raise BadRequestError("Provide at least one field to update.")

    fields = {}
    if "title" in payload:
        title = payload["title"]
        if not isinstance(title, str) or not title.strip():
            raise BadRequestError("Title must be a non-empty string.")
        if len(title.strip()) > MAX_TITLE_LENGTH:
            raise BadRequestError(
                f"Title must be at most {MAX_TITLE_LENGTH} characters."
            )
        fields["title"] = title.strip()
    if "description" in payload:
        description = payload["description"]
        if not isinstance(description, str):
            raise BadRequestError("Description must be a string.")
        if len(description) > MAX_DESCRIPTION_LENGTH:
            raise BadRequestError(
                "Description must be at most "
                f"{MAX_DESCRIPTION_LENGTH} characters."
            )
        fields["description"] = description
    return fields


def _now():
    return datetime.now(timezone.utc).isoformat()


def _list_tasks():
    response = table.scan()
    tasks = response.get("Items", [])
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        tasks.extend(response.get("Items", []))
    tasks.sort(key=lambda task: task["created_at"], reverse=True)
    return tasks


def _create_task(event):
    fields = _validated_text_fields(_parse_body(event), creating=True)
    timestamp = _now()
    task = {
        "task_id": str(uuid4()),
        "title": fields["title"],
        "description": fields.get("description", ""),
        "completed": False,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    table.put_item(Item=task)
    return _response(201, task)


def _get_task(task_id):
    result = table.get_item(Key={"task_id": task_id})
    task = result.get("Item")
    if task is None:
        raise NotFoundError("Task not found.")
    return task


def _update_task(event, task_id):
    fields = _validated_text_fields(_parse_body(event), creating=False)
    assignments = []
    names = {}
    values = {":updated_at": _now()}
    for index, (field, value) in enumerate(fields.items()):
        name_key = f"#field{index}"
        value_key = f":value{index}"
        names[name_key] = field
        values[value_key] = value
        assignments.append(f"{name_key} = {value_key}")
    assignments.append("updated_at = :updated_at")

    try:
        result = table.update_item(
            Key={"task_id": task_id},
            UpdateExpression="SET " + ", ".join(assignments),
            ConditionExpression="attribute_exists(task_id)",
            ExpressionAttributeNames=names,
            ExpressionAttributeValues=values,
            ReturnValues="ALL_NEW",
        )
    except ClientError as error:
        if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise NotFoundError("Task not found.") from error
        raise
    return result["Attributes"]


def _complete_task(task_id):
    try:
        result = table.update_item(
            Key={"task_id": task_id},
            UpdateExpression="SET completed = :completed, updated_at = :updated_at",
            ConditionExpression="attribute_exists(task_id)",
            ExpressionAttributeValues={
                ":completed": True,
                ":updated_at": _now(),
            },
            ReturnValues="ALL_NEW",
        )
    except ClientError as error:
        if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise NotFoundError("Task not found.") from error
        raise
    return result["Attributes"]


def _delete_task(task_id):
    try:
        table.delete_item(
            Key={"task_id": task_id},
            ConditionExpression="attribute_exists(task_id)",
        )
    except ClientError as error:
        if error.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise NotFoundError("Task not found.") from error
        raise


def handler(event, context):
    request_id = getattr(context, "aws_request_id", "unknown")
    route_key = event.get("routeKey", "")
    task_id = (event.get("pathParameters") or {}).get("taskId")
    logger.info("Handling task API request request_id=%s route=%s", request_id, route_key)

    try:
        if route_key == "POST /tasks":
            return _create_task(event)
        if route_key == "GET /tasks":
            return _response(200, {"tasks": _list_tasks()})
        if route_key == "GET /tasks/{taskId}" and task_id:
            return _response(200, _get_task(task_id))
        if route_key == "PUT /tasks/{taskId}" and task_id:
            return _response(200, _update_task(event, task_id))
        if route_key == "PATCH /tasks/{taskId}/complete" and task_id:
            return _response(200, _complete_task(task_id))
        if route_key == "DELETE /tasks/{taskId}" and task_id:
            _delete_task(task_id)
            return _response(204)
        return _response(404, {"error": "Route not found."})
    except BadRequestError as error:
        return _response(400, {"error": str(error)})
    except NotFoundError as error:
        return _response(404, {"error": str(error)})
    except BotoCoreError:
        logger.exception("Task API request failed request_id=%s", request_id)
        return _response(500, {"error": "Internal server error."})
