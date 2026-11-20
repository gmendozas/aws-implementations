# Text to speech with Amazon Polly

This AWS SAM project turns a small UTF-8 text article into an MP3:

1. Upload a `.txt` file to the source S3 bucket.
2. S3 publishes an object-created event to EventBridge, which invokes
   `TextToSpeechFunction`.
3. That Lambda reads the text from S3 and calls Amazon Polly `SynthesizeSpeech`.
   It uses the deployment region when Polly is available there, or `us-west-1`
   otherwise. The Polly voice ID is configurable; the selected voice determines
   the spoken language.
4. It sends Polly's MP3 bytes, base64-encoded, to `AudioStorageFunction`.
5. The storage Lambda writes the MP3 to the private audio S3 bucket, using the
   same object key with an `.mp3` extension.

The sample article in `sample/quiet-hour-in-the-city.txt` is original and can be
used to try the workflow.

## Project documentation

- [Architecture](docs/architecture.md): AWS components, request flow, permissions,
  and system limits.
- [Code style](docs/code-style.md): conventions for Python, SAM configuration,
  and project documentation.

## Deploy

Prerequisites: AWS CLI credentials with permission to deploy CloudFormation,
create the resources in `template.yaml`, and use AWS SAM CLI.

```sh
sam build
sam deploy --guided
```

The stack parameter `PollyVoiceId` defaults to `Joanna`. To choose another
language, pass a voice ID supported by Polly's standard engine in the Polly
region:

```sh
sam deploy --parameter-overrides PollyVoiceId=Lucia
```

Replace `Lucia` with the voice ID you want. Available voices and languages are
listed in the [Amazon Polly voices documentation](https://docs.aws.amazon.com/polly/latest/dg/voicelist.html).

After deployment, note the `SourceTextBucketName` and `AudioBucketName` outputs.
Upload the sample article to the source bucket:

```sh
aws s3 cp sample/quiet-hour-in-the-city.txt s3://SOURCE_BUCKET_NAME/
```

After the S3 event is processed, the generated audio is available in the output
bucket at `quiet-hour-in-the-city.mp3`:

```sh
aws s3 ls s3://AUDIO_BUCKET_NAME/
aws s3 cp s3://AUDIO_BUCKET_NAME/quiet-hour-in-the-city.mp3 .
```

The output bucket is private; access the audio using AWS credentials with the
appropriate S3 permissions.

## Scope and limits

This example uses Polly's standard engine and Joanna voice by default. Each
input file is limited to 3,000 characters, and the resulting audio must fit in
a synchronous Lambda invocation payload (6 MB, including JSON/base64 overhead).
These limits make the two-Lambda handoff suitable for short articles or
newsletter sections, not full books. For long-form content, use Polly's asynchronous
`StartSpeechSynthesisTask` workflow with an S3 output destination instead of
passing audio between Lambda functions.

The source and audio buckets are created by the stack and are not configured
for public access. The source bucket accepts `.txt` uploads; other file types
are not part of this workflow.
