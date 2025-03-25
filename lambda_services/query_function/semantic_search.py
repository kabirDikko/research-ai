import os
import json
import boto3
import requests
from urllib.parse import parse_qs

# Initialize Bedrock client for embeddings
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.environ.get('AWS_REGION', 'us-east-1')
)

# Constants for embedding model
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v1"
EMBEDDING_DIMENSION = 1536  # Titan model dimension

# Get OpenSearch endpoint from environment variable
opensearch_endpoint = os.environ.get('OPENSEARCH_ENDPOINT')
index_name = os.environ.get('OPENSEARCH_INDEX', 'documents')

def get_embeddings(text, max_chunk_size=8000):
    """
    Generate embeddings using Amazon Bedrock Titan Embeddings model.
    """
    if not text or not text.strip():
        print("Empty text provided for embeddings")
        return None
        
    try:
        # Ensure we don't exceed the model's maximum input size
        if len(text) > max_chunk_size:
            print(f"Text exceeds maximum size, truncating to {max_chunk_size} characters")
            text = text[:max_chunk_size]
            
        # Prepare request body
        request_body = json.dumps({
            "inputText": text
        })
        
        # Call Bedrock to get embeddings
        response = bedrock_runtime.invoke_model(
            modelId=EMBEDDING_MODEL_ID,
            body=request_body
        )
        
        # Parse the response
        response_body = json.loads(response.get("body").read())
        embedding = response_body.get("embedding")
        
        return embedding
    except Exception as e:
        print(f"Error generating embeddings: {str(e)}")
        return None

def search_documents(query_text, top_k=5, hybrid_search=True):
    """
    Search documents in OpenSearch using semantic search with vector embeddings
    If hybrid_search is True, combines vector search with keyword search for better results
    """
    if not query_text:
        return {"error": "Query text is required"}, 400
        
    if not opensearch_endpoint:
        return {"error": "OpenSearch endpoint is not configured"}, 500
    
    try:
        # Generate embeddings for the query
        query_embedding = get_embeddings(query_text)
        
        if not query_embedding:
            return {"error": "Failed to generate embeddings for the query"}, 500
        
        # Ensure OpenSearch endpoint has the correct scheme
        endpoint = opensearch_endpoint
        if not endpoint.startswith(('http://', 'https://')):
            endpoint = f"https://{endpoint}"
            
        # Construct search URL
        search_url = f"{endpoint}/{index_name}/_search"
        headers = {"Content-Type": "application/json"}
        
        # Build the search query
        if hybrid_search:
            # Combined vector and text search for better results
            search_query = {
                "size": top_k,
                "query": {
                    "script_score": {
                        "query": {
                            "bool": {
                                "should": [
                                    {"match": {"text": query_text}}
                                ]
                            }
                        },
                        "script": {
                            "source": "knn_score",
                            "params": {
                                "field": "vector",
                                "query_value": query_embedding,
                                "space_type": "cosinesimil"
                            }
                        }
                    }
                }
            }
        else:
            # Pure vector search
            search_query = {
                "size": top_k,
                "query": {
                    "knn": {
                        "vector": {
                            "vector": query_embedding,
                            "k": top_k
                        }
                    }
                }
            }
            
        # Execute the search
        response = requests.post(search_url, headers=headers, data=json.dumps(search_query))
        
        if response.status_code != 200:
            return {"error": f"OpenSearch query failed: {response.text}"}, response.status_code
            
        # Parse search results
        results = json.loads(response.text)
        hits = results.get("hits", {}).get("hits", [])
        
        # Format the results
        formatted_results = []
        for hit in hits:
            doc = hit.get("_source", {})
            formatted_results.append({
                "score": hit.get("_score"),
                "filename": doc.get("filename"),
                "text": doc.get("text"),
                "metadata": json.loads(doc.get("text-metadata", "{}"))
            })
        
        return {"query": query_text, "results": formatted_results}, 200
        
    except Exception as e:
        print(f"Error searching documents: {str(e)}")
        return {"error": f"Failed to search documents: {str(e)}"}, 500

def lambda_handler(event, context):
    """
    Lambda handler for the semantic search API
    Accepts query parameters:
    - q: Query text (required)
    - k: Top K results (optional, default 5)
    - hybrid: Whether to use hybrid search (optional, default true)
    """
    try:
        # Parse different types of events (API Gateway, direct invocation)
        if event.get('httpMethod') == 'GET' and event.get('queryStringParameters'):
            # API Gateway GET request
            params = event.get('queryStringParameters', {})
            query_text = params.get('q', '')
            top_k = int(params.get('k', '5'))
            hybrid = params.get('hybrid', 'true').lower() == 'true'
            
        elif event.get('body') and event.get('httpMethod') == 'POST':
            # API Gateway POST request
            body = json.loads(event.get('body', '{}'))
            query_text = body.get('query', '')
            top_k = int(body.get('top_k', 5))
            hybrid = body.get('hybrid', True)
            
        elif event.get('querytext'):
            # Direct invocation with parameters
            query_text = event.get('querytext', '')
            top_k = int(event.get('top_k', 5))
            hybrid = event.get('hybrid', True)
            
        else:
            # Unknown event format
            return {
                'statusCode': 400,
                'body': json.dumps({"error": "Invalid request format"})
            }
        
        # Validate query text
        if not query_text:
            return {
                'statusCode': 400,
                'body': json.dumps({"error": "Query text is required"})
            }
            
        # Execute the search
        result, status_code = search_documents(query_text, top_k, hybrid)
        
        # Return the response
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({"error": f"Internal server error: {str(e)}"})
        } 