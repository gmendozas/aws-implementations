# Event-driven image processor

This AWS SAM project creates a thumbnail when a supported image is uploaded to
an S3 source bucket. Amazon EventBridge routes S3 object-created events to an
SQS queue, which buffers work for a Python Lambda. The Lambda writes a JPEG
thumbnail to a separate private S3 bucket and records image and output details
in DynamoDB.

Supported lowercase input extensions are `.jpg`, `.jpeg`, `.png`, and `.webp`.
The processor converts images to JPEG, applies EXIF orientation, preserves
transparency on a white background, and constrains thumbnails to 256 by 256
pixels. Inputs are limited to 10 MiB.

## Project documentation

- [Architecture](docs/architecture.md): event flow, resources, permissions, and
  retry behavior.
- [Code style](docs/code-style.md): Python and AWS SAM conventions.

## Deploy

Prerequisites: AWS CLI credentials with permission to deploy the resources in
`template.yaml`, AWS SAM CLI, and Docker for building Pillow's Linux-compatible
binary dependency.

Run these commands from this directory:

```sh
sam validate --lint
sam build --use-container
sam deploy --guided
```

After deployment, get the bucket names from the stack outputs and upload an
image:

```sh
aws s3 cp ./photo.jpg s3://SOURCE_IMAGE_BUCKET_NAME/
```

The resulting JPEG is stored in the thumbnail bucket with a key prefixed by
`thumbnails/`, for example `thumbnails/photo.jpg.jpg`. Check the
`ImageProcessingTableName` output for the DynamoDB table containing the
processing record. SQS retries failed messages up to five receives before
sending them to the dead-letter queue.

The source and thumbnail buckets are private. Use AWS credentials with the
appropriate S3 permissions to inspect or retrieve images.

## Notes and limits

- The source bucket only routes files with the supported image extensions to
  the queue. An unsupported extension does not start processing.
- The pipeline is asynchronous and at-least-once. S3 and SQS may deliver
  duplicate events; DynamoDB records each EventBridge event ID.
- A message is acknowledged only after both the thumbnail write and DynamoDB
  write succeed. A failure is reported to the SQS event source mapping for
  retry; messages that exhaust retries are retained in the dead-letter queue.
- The generated thumbnail key includes the original source key, so similarly
  named images with different extensions do not overwrite one another.
- This example targets image files no larger than 10 MiB and uses Pillow in a
  1 GiB Lambda. For larger or untrusted workloads, add stricter dimension limits
  and consider a separate quarantine workflow.
