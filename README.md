# AWS Portfolio

This repository is a portfolio of small, independent projects built with
Amazon Web Services. Each mini-project lives in its own directory and includes
the code and project-specific documentation needed to understand, validate, and
deploy it.

## Projects

| Project | Description | Documentation |
| --- | --- | --- |
| [txt2audio](./txt2audio/) | Converts short UTF-8 text files uploaded to Amazon S3 into MP3 audio using Amazon Polly, AWS Lambda, and AWS SAM. | [Project README](./txt2audio/README.md) |

More AWS portfolio projects can be added as sibling directories.

## Working with a project

Run commands from the mini-project directory so its SAM template and
configuration are used. For example:

```sh
cd txt2audio
sam validate --lint
sam build
sam deploy --guided
```

See each project's README for prerequisites, deployment details, usage, and
limitations.
