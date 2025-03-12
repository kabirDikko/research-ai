# Ingest Function
This function processes documents uploaded to S3.
## Overview
This Lambda function processes documents uploaded to an S3 bucket by extracting text content and indexing it into OpenSearch. It supports multiple file types including:

- PDF documents
- Images (JPG, JPEG, PNG)
- Audio files (MP3, WAV, OGG) - *Note: Audio processing is currently a placeholder*

## How it Works

1. When a file is uploaded to the configured S3 bucket, it triggers this Lambda function
2. The function:
   - Downloads the file to temporary Lambda storage
   - Determines the file type by extension
   - Processes the content using appropriate AWS services:
     - PDFs & Images: Uses Amazon Textract to extract text
     - Audio files: Placeholder for future Amazon Transcribe integration
   - Indexes the extracted text and metadata into OpenSearch

## Required Environment Variables
- `OPENSEARCH_ENDPOINT`: The endpoint URL for your OpenSearch domain

## Dependencies
The function requires the following Python packages (see requirements.txt):
- requests==2.28.2
- boto3==1.33.1

## IAM Permissions
The function requires IAM permissions for:
- S3 access (GetObject)
- Textract operations
- Rekognition operations
- OpenSearch operations (ESHttpPost, ESHttpPut, ESHttpGet)

## Output Format
The function returns a JSON response with:
- HTTP status code
- Extracted text content
- OpenSearch indexing response

## Error Handling
- Unsupported file types are detected and logged
- Missing environment variables are caught and raise exceptions
- OpenSearch indexing responses are logged for monitoring
