import importlib
import json
import os
import sys
import types
import unittest
from unittest.mock import patch


class BotoCoreError(Exception):
    pass


class ClientError(BotoCoreError):
    def __init__(self, response, operation_name):
        super().__init__(operation_name)
        self.response = response


class FakeTable:
    def __init__(self):
        self.items = {}

    def put_item(self, *, Item):
        self.items[Item["task_id"]] = Item

    def scan(self, **kwargs):
        items = list(self.items.values())
        return {"Items": items}

    def get_item(self, *, Key):
        item = self.items.get(Key["task_id"])
        return {} if item is None else {"Item": item}

    def update_item(
        self,
        *,
        Key,
        UpdateExpression,
        ExpressionAttributeValues,
        ReturnValues,
        **kwargs,
    ):
        task = self.items.get(Key["task_id"])
        if task is None:
            raise ClientError(
                {"Error": {"Code": "ConditionalCheckFailedException"}},
                "UpdateItem",
            )
        names = kwargs.get("ExpressionAttributeNames", {})
        for assignment in UpdateExpression.removeprefix("SET ").split(", "):
            field, value_key = assignment.split(" = ")
            field = names.get(field, field)
            task[field] = ExpressionAttributeValues[value_key]
        return {"Attributes": task}

    def delete_item(self, *, Key, **kwargs):
        if self.items.pop(Key["task_id"], None) is None:
            raise ClientError(
                {"Error": {"Code": "ConditionalCheckFailedException"}},
                "DeleteItem",
            )


def load_task_api():
    fake_boto3 = types.ModuleType("boto3")
    fake_boto3.resource = lambda service: types.SimpleNamespace(
        Table=lambda name: FakeTable()
    )
    fake_botocore = types.ModuleType("botocore")
    fake_exceptions = types.ModuleType("botocore.exceptions")
    fake_exceptions.BotoCoreError = BotoCoreError
    fake_exceptions.ClientError = ClientError
    fake_botocore.exceptions = fake_exceptions

    with patch.dict(
        sys.modules,
        {
            "boto3": fake_boto3,
            "botocore": fake_botocore,
            "botocore.exceptions": fake_exceptions,
        },
    ), patch.dict(os.environ, {"TASK_TABLE": "test-table"}):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
        try:
            return importlib.import_module("task_api")
        finally:
            sys.path.pop(0)


task_api = load_task_api()


class TaskApiTests(unittest.TestCase):
    def setUp(self):
        task_api.table = FakeTable()
        self.context = types.SimpleNamespace(aws_request_id="test-request")

    def invoke(self, route_key, *, body=None, task_id=None):
        event = {
            "routeKey": route_key,
            "body": body,
            "pathParameters": {"taskId": task_id} if task_id else {},
        }
        return task_api.handler(event, self.context)

    def test_create_list_update_complete_and_delete_task(self):
        created = self.invoke(
            "POST /tasks",
            body=json.dumps({"title": "  Learn SAM  ", "description": "Basics"}),
        )
        self.assertEqual(created["statusCode"], 201)
        task = json.loads(created["body"])
        task_id = task["task_id"]
        self.assertEqual(task["title"], "Learn SAM")
        self.assertFalse(task["completed"])

        listed = self.invoke("GET /tasks")
        self.assertEqual(json.loads(listed["body"])["tasks"], [task])

        updated = self.invoke(
            "PUT /tasks/{taskId}",
            body=json.dumps({"description": "Deploy a stack"}),
            task_id=task_id,
        )
        self.assertEqual(
            json.loads(updated["body"])["description"], "Deploy a stack"
        )

        completed = self.invoke(
            "PATCH /tasks/{taskId}/complete", task_id=task_id
        )
        self.assertTrue(json.loads(completed["body"])["completed"])

        deleted = self.invoke("DELETE /tasks/{taskId}", task_id=task_id)
        self.assertEqual(deleted["statusCode"], 204)
        missing = self.invoke("GET /tasks/{taskId}", task_id=task_id)
        self.assertEqual(missing["statusCode"], 404)

    def test_invalid_create_body_returns_bad_request(self):
        response = self.invoke("POST /tasks", body='{"title": ""}')
        self.assertEqual(response["statusCode"], 400)
        self.assertIn("title", json.loads(response["body"])["error"].lower())


if __name__ == "__main__":
    unittest.main()
