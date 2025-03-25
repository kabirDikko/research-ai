# Document Processing with RAG Integration

This service provides document processing capabilities with Retrieval-Augmented Generation (RAG) integration using Amazon Bedrock and OpenSearch.

## Overview

The document processing pipeline handles the following steps:

1. **Ingestion**: Files are uploaded to an S3 bucket, triggering the Lambda function.
2. **Conversion**: Images in HEIC/HEIF/TIFF formats are converted to JPG.
3. **Text Extraction**: Amazon Textract extracts text from images and PDFs.
4. **Embedding Generation**: Amazon Bedrock Titan Embeddings model generates vector embeddings of the extracted text.
5. **Indexing**: Both the text and vector embeddings are indexed in OpenSearch for retrieval.

## Key Features

- **Multi-format Support**: Handles various image formats, including HEIC, HEIF, TIFF, JPG, PNG, and PDF.
- **Semantic Search**: Vector embeddings enable semantic search capabilities.
- **Error Handling**: Robust error handling with retry logic and failed file tracking.
- **Scalable Architecture**: Serverless architecture that scales with your document processing needs.

## Requirements

- AWS Lambda
- Amazon S3
- Amazon Textract
- Amazon Bedrock
- Amazon OpenSearch
- Python 3.9+

## Environment Variables

The service requires the following environment variables:

- `OPENSEARCH_ENDPOINT`: The endpoint URL for your OpenSearch cluster.
- `INGESTION_BUCKET`: S3 bucket for initial file uploads.
- `PROCESSED_INGESTION_BUCKET`: S3 bucket for processed files.
- `FAILED_INGESTION_BUCKET`: S3 bucket for files that failed processing.
- `AWS_REGION`: AWS region where your services are deployed (defaults to us-east-1).

## Testing

To test the RAG integration, you can use the provided test scripts:

1. Make the test script executable:
   ```bash
   chmod +x test_rag_setup.sh
   ```

2. Run the test script:
   ```bash
   ./test_rag_setup.sh
   ```

The script will:
- Set up necessary environment variables
- Install required dependencies
- Test the Bedrock embeddings functionality
- Test the OpenSearch connection and indexing

## Deployment

1. Ensure your AWS credentials are configured correctly.

2. Update the `serverless.yml` file to include the required environment variables and permissions.

3. Deploy the service using Serverless Framework:
   ```bash
   cd lambda_services
   serverless deploy
   ```

## OpenSearch Index Mapping

For optimal vector search, create your OpenSearch index with the following mapping:

```json
{
  "mappings": {
    "properties": {
      "filename": {
        "type": "text"
      },
      "text": {
        "type": "text"
      },
      "vector": {
        "type": "knn_vector",
        "dimension": 1536
      },
      "text-metadata": {
        "type": "text"
      }
    }
  },
  "settings": {
    "index": {
      "knn": true,
      "knn.space_type": "cosinesimil"
    }
  }
}
```

## Query Examples

### Semantic Search Query

```python
import boto3
import json
import requests

# Generate query embeddings
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
query_text = "Find documents about artificial intelligence"

# Get embeddings for the query
response = bedrock_runtime.invoke_model(
    modelId="amazon.titan-embed-text-v1",
    body=json.dumps({"inputText": query_text})
)
query_embedding = json.loads(response["body"].read())["embedding"]

# Construct the OpenSearch query
opensearch_query = {
  "size": 5,
  "query": {
    "knn": {
      "vector": {
        "vector": query_embedding,
        "k": 5
      }
    }
  }
}

# Send the query to OpenSearch
endpoint = "https://your-opensearch-endpoint"
url = f"{endpoint}/documents/_search"
headers = {"Content-Type": "application/json"}
response = requests.get(url, headers=headers, data=json.dumps(opensearch_query))

# Process results
results = json.loads(response.text)["hits"]["hits"]
for result in results:
    print(f"Score: {result['_score']}")
    print(f"Filename: {result['_source']['filename']}")
    print(f"Text: {result['_source']['text'][:100]}...")
    print("---")
``` 