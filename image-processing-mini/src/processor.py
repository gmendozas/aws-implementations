import io
import json
import logging
import os
from datetime import datetime, timezone

import boto3
from PIL import Image, ImageOps

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

THUMBNAIL_SIZE = (256, 256)
MAX_IMAGE_BYTES = int(os.environ.get("MAX_IMAGE_BYTES", "10485760"))
thumbnail_bucket = os.environ.get("THUMBNAIL_BUCKET")
table_name = os.environ.get("IMAGE_PROCESSING_TABLE")
table = dynamodb.Table(table_name) if table_name else None


def _process_image(eventbridge_event):
    detail = eventbridge_event["detail"]
    source_bucket = detail["bucket"]["name"]
    source_key = detail["object"]["key"]
    event_id = eventbridge_event["id"]

    image_object = s3.get_object(Bucket=source_bucket, Key=source_key)
    if image_object["ContentLength"] > MAX_IMAGE_BYTES:
        raise ValueError(
            f"Image is {image_object['ContentLength']} bytes; the limit is "
            f"{MAX_IMAGE_BYTES} bytes."
        )

    image_data = image_object["Body"].read()
    if len(image_data) > MAX_IMAGE_BYTES:
        raise ValueError(f"Image exceeds the {MAX_IMAGE_BYTES}-byte limit.")

    with Image.open(io.BytesIO(image_data)) as image:
        image.load()
        image = ImageOps.exif_transpose(image)
        original_width, original_height = image.size
        image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

        if image.mode in ("RGBA", "LA") or "transparency" in image.info:
            image = image.convert("RGBA")
            background = Image.new("RGB", image.size, "white")
            background.paste(image, mask=image.getchannel("A"))
            image = background
        else:
            image = image.convert("RGB")

        thumbnail_data = io.BytesIO()
        image.save(thumbnail_data, format="JPEG", quality=85, optimize=True)
        thumbnail_width, thumbnail_height = image.size

    thumbnail_key = f"thumbnails/{source_key}.jpg"
    s3.put_object(
        Bucket=thumbnail_bucket,
        Key=thumbnail_key,
        Body=thumbnail_data.getvalue(),
        ContentType="image/jpeg",
    )

    processed_at = datetime.now(timezone.utc).isoformat()
    table.put_item(
        Item={
            "event_id": event_id,
            "source_bucket": source_bucket,
            "source_key": source_key,
            "thumbnail_bucket": thumbnail_bucket,
            "thumbnail_key": thumbnail_key,
            "original_width": original_width,
            "original_height": original_height,
            "thumbnail_width": thumbnail_width,
            "thumbnail_height": thumbnail_height,
            "processed_at": processed_at,
        }
    )
    logger.info(
        "Processed s3://%s/%s into s3://%s/%s (%dx%d -> %dx%d)",
        source_bucket,
        source_key,
        thumbnail_bucket,
        thumbnail_key,
        original_width,
        original_height,
        thumbnail_width,
        thumbnail_height,
    )


def handler(event, context):
    batch_item_failures = []
    for record in event["Records"]:
        message_id = record["messageId"]
        try:
            eventbridge_event = json.loads(record["body"])
            _process_image(eventbridge_event)
        except Exception:
            logger.exception("Failed to process SQS message %s", message_id)
            batch_item_failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": batch_item_failures}
