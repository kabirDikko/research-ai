# RAG Query Service

This service provides Retrieval-Augmented Generation (RAG) capabilities for querying documents stored in OpenSearch.

## Overview

The RAG Query Service consists of two main components:

1. **Semantic Search**: Finds relevant documents based on vector embeddings and text similarity.
2. **LLM Response Generation**: Uses Amazon Bedrock to generate responses based on retrieved documents.

## Features

- **Semantic Search**: Vector-based document retrieval using embeddings.
- **Hybrid Search**: Combines vector and keyword search for better results.
- **Multiple Models**: Support for Claude, Titan, and other Bedrock models.
- **Source Attribution**: Includes source documents in the response.
- **Configurable Parameters**: Customize top-k results, temperature, etc.

## Requirements

- AWS Lambda
- Amazon API Gateway
- Amazon Bedrock
- Amazon OpenSearch
- Python 3.9+

## Environment Variables

The service requires the following environment variables:

- `OPENSEARCH_ENDPOINT`: The endpoint URL for your OpenSearch cluster.
- `AWS_REGION`: AWS region where your services are deployed (defaults to us-east-1).
- `OPENSEARCH_INDEX`: Name of the OpenSearch index (defaults to "documents").
- `BEDROCK_MODEL_ID`: Default Bedrock model to use (defaults to Claude 3 Sonnet).
- `MAX_TOKENS`: Maximum tokens in the LLM response (defaults to 4096).
- `TEMPERATURE`: LLM temperature (defaults to 0.7).
- `TOP_P`: LLM top-p value (defaults to 0.9).

## Testing Locally

To test the RAG service locally, use the provided test scripts:

### Test Semantic Search Only

```bash
python test_semantic_search.py --query "Your search query" --top-k 5 --hybrid
```

Options:
- `--query`, `-q`: Search query text (required)
- `--top-k`, `-k`: Number of results to return (default: 5)
- `--hybrid`: Use hybrid search (default)
- `--vector-only`: Use vector search only
- `--endpoint`, `-e`: OpenSearch endpoint URL
- `--region`, `-r`: AWS region for Bedrock

### Test Full RAG Service

```bash
python test_rag_service.py --query "Your question about documents" --model "anthropic.claude-3-sonnet-20240229-v1:0"
```

Options:
- `--query`, `-q`: Query text (required)
- `--top-k`, `-k`: Number of documents to retrieve (default: 5)
- `--model`, `-m`: Bedrock model ID
- `--hybrid`: Use hybrid search (default)
- `--vector-only`: Use vector search only
- `--max-tokens`, `-t`: Maximum tokens in response
- `--temperature`: LLM temperature
- `--no-sources`: Do not include source documents
- `--endpoint`, `-e`: OpenSearch endpoint URL
- `--region`, `-r`: AWS region for Bedrock

## API Usage

### REST API

When deployed to AWS Lambda with API Gateway, the service can be accessed via HTTP:

#### GET Request

```
GET /rag?q=your+query&k=5&model=anthropic.claude-3-sonnet-20240229-v1:0&hybrid=true&max_tokens=4096&temperature=0.7&include_sources=true
```

#### POST Request

```
POST /rag
Content-Type: application/json

{
  "query": "Your query about documents",
  "top_k": 5,
  "model": "anthropic.claude-3-sonnet-20240229-v1:0",
  "hybrid": true,
  "max_tokens": 4096,
  "temperature": 0.7,
  "include_sources": true
}
```

### Lambda Direct Invocation

```python
import boto3

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='rag-query-function',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        "querytext": "Your query about documents",
        "top_k": 5,
        "model": "anthropic.claude-3-sonnet-20240229-v1:0",
        "hybrid": True,
        "max_tokens": 4096,
        "temperature": 0.7,
        "include_sources": True
    })
)
```

## Response Format

```json
{
  "query": "Your original query",
  "response": "Generated answer from the LLM...",
  "sources": [
    {
      "filename": "document1.pdf",
      "score": 0.95,
      "metadata": {
        "source_bucket": "your-bucket",
        "source_key": "document1.pdf",
        "extraction_time": "2023-03-24T12:00:00",
        "file_type": "pdf"
      }
    },
    ...
  ]
}
```

## Deployment

1. Ensure your AWS credentials are configured correctly.

2. Update the `serverless.yml` file to include the required environment variables and permissions.

3. Deploy the service using Serverless Framework:
   ```bash
   cd lambda_services
   serverless deploy
   ``` 