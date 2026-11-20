import base64
import binascii
import os

import boto3

s3 = boto3.client("s3")


def handler(event, context):
    source_bucket = event["source_bucket"]
    source_key = event["source_key"]
    encoded_audio = event["audio_base64"]

    try:
        audio = base64.b64decode(encoded_audio, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError("audio_base64 must contain valid base64-encoded audio.") from error
    if not audio:
        raise ValueError("Synthesized audio is empty.")

    audio_key = f"{source_key.rsplit('.', 1)[0]}.mp3"
    s3.put_object(
        Bucket=os.environ["AUDIO_BUCKET"],
        Key=audio_key,
        Body=audio,
        ContentType="audio/mpeg",
    )
    return {
        "bucket": os.environ["AUDIO_BUCKET"],
        "key": audio_key,
        "bytes": len(audio),
    }
