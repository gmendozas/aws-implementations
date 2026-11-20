import base64
import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
aws_session = boto3.session.Session()
polly_region = aws_session.region_name
if polly_region not in aws_session.get_available_regions("polly"):
    polly_region = "us-west-1"
    logger.info(
        "Amazon Polly is unavailable in configured region %s; using %s.",
        aws_session.region_name,
        polly_region,
    )
polly = aws_session.client("polly", region_name=polly_region)
lambda_client = boto3.client("lambda")

MAX_TEXT_CHARACTERS = 3000
MAX_LAMBDA_INVOKE_PAYLOAD_BYTES = 6 * 1024 * 1024


def handler(event, context):
    detail = event["detail"]
    source_bucket = detail["bucket"]["name"]
    source_key = detail["object"]["key"]

    if not source_key.lower().endswith(".txt"):
        raise ValueError(f"Expected a .txt input object, got {source_key!r}")

    text_object = s3.get_object(Bucket=source_bucket, Key=source_key)
    text = text_object["Body"].read().decode("utf-8").strip()
    if not text:
        raise ValueError(f"Input text is empty: s3://{source_bucket}/{source_key}")
    if len(text) > MAX_TEXT_CHARACTERS:
        raise ValueError(
            f"Input text is {len(text)} characters; this demo supports at most "
            f"{MAX_TEXT_CHARACTERS} characters per file."
        )

    synthesis = polly.synthesize_speech(
        Text=text,
        OutputFormat="mp3",
        VoiceId=os.environ.get("POLLY_VOICE_ID", "Joanna"),
        Engine="standard",
    )
    audio = synthesis["AudioStream"].read()
    payload = json.dumps(
        {
            "source_bucket": source_bucket,
            "source_key": source_key,
            "audio_base64": base64.b64encode(audio).decode("ascii"),
        },
        separators=(",", ":"),
    ).encode("utf-8")
    if len(payload) > MAX_LAMBDA_INVOKE_PAYLOAD_BYTES:
        raise ValueError(
            "Synthesized audio is too large to pass to the storage Lambda "
            "within Lambda's synchronous invocation payload limit."
        )

    response = lambda_client.invoke(
        FunctionName=os.environ["AUDIO_STORAGE_FUNCTION"],
        InvocationType="RequestResponse",
        Payload=payload,
    )
    if response.get("FunctionError"):
        error = response["Payload"].read().decode("utf-8")
        raise RuntimeError(f"Audio storage Lambda failed: {error}")
    if response["StatusCode"] != 200:
        raise RuntimeError(
            f"Audio storage Lambda returned status {response['StatusCode']}."
        )

    storage_result = json.loads(response["Payload"].read().decode("utf-8"))
    logger.info(
        "Stored synthesized audio for s3://%s/%s",
        source_bucket,
        source_key,
    )
    return {"stored": storage_result}
