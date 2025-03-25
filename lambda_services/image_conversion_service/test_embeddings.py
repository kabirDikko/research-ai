import boto3
import json
import os
from ingest import get_embeddings

def test_bedrock_embeddings():
    """Test the Bedrock embeddings function with a sample text"""
    print("Testing Bedrock embeddings generation...")
    
    # Sample text for testing
    test_text = """
    This is a test document to verify that the Amazon Bedrock Titan Embeddings model
    is working correctly. We want to ensure that we can generate embeddings for our
    document processing system. These embeddings will be used for semantic search and
    retrieval-augmented generation (RAG) capabilities.
    """
    
    # Generate embeddings
    embeddings = get_embeddings(test_text)
    
    # Validate the embeddings
    if embeddings and isinstance(embeddings, list):
        print(f"✅ Successfully generated embeddings!")
        print(f"Embedding dimension: {len(embeddings)}")
        print(f"First few values: {embeddings[:5]}")
        return True
    else:
        print(f"❌ Failed to generate embeddings: {embeddings}")
        return False

def test_opensearch_indexing():
    """Test connection to OpenSearch and document indexing"""
    print("\nTesting OpenSearch connection and indexing...")
    
    # Import necessary functions from ingest.py
    from ingest import opensearch_endpoint, sanitize_id
    import requests
    
    if not opensearch_endpoint:
        print("❌ OpenSearch endpoint not configured. Set the OPENSEARCH_ENDPOINT environment variable.")
        return False
    
    # Sample document
    test_doc = {
        "filename": "test_document.txt",
        "text": "This is a test document for OpenSearch indexing.",
        "vector": [0.1, 0.2, 0.3, 0.4, 0.5] * 307,  # Create a vector of dimension 1535 (close to 1536)
        "text-metadata": json.dumps({
            "source_bucket": "test-bucket",
            "source_key": "test/test_document.txt",
            "extraction_time": "2023-03-24T12:00:00",
            "file_type": "txt"
        })
    }
    
    # Create a safe document ID
    doc_id = sanitize_id("test_document.txt")
    
    # Prepare the endpoint URL
    endpoint = opensearch_endpoint
    if not endpoint.startswith(('http://', 'https://')):
        endpoint = f"https://{endpoint}"
    
    url = f"{endpoint}/documents/_doc/{doc_id}"
    headers = {"Content-Type": "application/json"}
    
    try:
        # Test connection to OpenSearch
        response = requests.put(url, headers=headers, data=json.dumps(test_doc))
        
        if response.status_code >= 200 and response.status_code < 300:
            print(f"✅ Successfully indexed test document to OpenSearch!")
            print(f"Response: {response.text}")
            return True
        else:
            print(f"❌ Failed to index to OpenSearch: {response.status_code} - {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection to OpenSearch failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("======= TESTING BEDROCK EMBEDDINGS AND OPENSEARCH INTEGRATION =======")
    print(f"AWS Region: {os.environ.get('AWS_REGION', 'us-east-1')}")
    
    # Check if environment variables are set
    if not os.environ.get('OPENSEARCH_ENDPOINT'):
        print("Warning: OPENSEARCH_ENDPOINT environment variable not set")
    
    # Run tests
    embeddings_success = test_bedrock_embeddings()
    opensearch_success = test_opensearch_indexing()
    
    # Output summary
    print("\n======= TEST SUMMARY =======")
    print(f"Bedrock Embeddings Test: {'PASSED' if embeddings_success else 'FAILED'}")
    print(f"OpenSearch Indexing Test: {'PASSED' if opensearch_success else 'FAILED'}")
    
    # Return overall success
    return embeddings_success and opensearch_success

if __name__ == "__main__":
    main() 