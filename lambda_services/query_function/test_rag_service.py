#!/usr/bin/env python
"""
Test script for the RAG service.
This script simulates API requests to the RAG service Lambda function.
"""

import os
import json
import argparse
from rag_service import rag_query

def test_rag(query, top_k=5, model_id=None, hybrid=True, max_tokens=None, 
            temperature=None, include_sources=True):
    """Test the RAG functionality"""
    print(f"Testing RAG service with query: '{query}'")
    print(f"Parameters: top_k={top_k}, hybrid_search={hybrid}")
    
    # Get default model from environment or use Claude
    default_model = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
    model = model_id or default_model
    print(f"Using model: {model}")
    
    # Get max tokens
    tokens = max_tokens or int(os.environ.get('MAX_TOKENS', 4096))
    temp = temperature or float(os.environ.get('TEMPERATURE', 0.7))
    
    # Ensure environment variables are set
    if not os.environ.get('OPENSEARCH_ENDPOINT'):
        print("Warning: OPENSEARCH_ENDPOINT environment variable not set")
        opensearch_endpoint = input("Enter your OpenSearch endpoint URL: ")
        os.environ['OPENSEARCH_ENDPOINT'] = opensearch_endpoint
    
    # Call the RAG function
    result, status_code = rag_query(
        query, top_k, model, hybrid, 
        tokens, temp, 0.9, include_sources
    )
    
    # Print the status code
    print(f"\nStatus Code: {status_code}")
    
    # Format and print the results
    if status_code == 200:
        print("\n===== RAG RESPONSE =====")
        print(f"Query: '{result['query']}'")
        print("\nAnswer:")
        print(result['response'])
        
        if include_sources and 'sources' in result:
            print("\n===== SOURCES =====")
            for i, source in enumerate(result['sources'], 1):
                print(f"\n--- Source {i} ---")
                print(f"Filename: {source['filename']}")
                print(f"Score: {source['score']}")
                
                # Print metadata if available
                if 'metadata' in source and source['metadata']:
                    print("Metadata:")
                    for key, value in source['metadata'].items():
                        print(f"  {key}: {value}")
    else:
        print("\n===== ERROR =====")
        print(result.get('error', 'Unknown error'))
    
    return result, status_code

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test RAG service functionality')
    parser.add_argument('--query', '-q', type=str, required=True, help='Query text')
    parser.add_argument('--top-k', '-k', type=int, default=5, help='Number of documents to retrieve (default: 5)')
    parser.add_argument('--model', '-m', type=str, help='Bedrock model ID')
    parser.add_argument('--hybrid', action='store_true', help='Use hybrid search (vector + keyword)')
    parser.add_argument('--vector-only', dest='hybrid', action='store_false', help='Use vector search only')
    parser.add_argument('--max-tokens', '-t', type=int, help='Maximum tokens in response')
    parser.add_argument('--temperature', type=float, help='LLM temperature')
    parser.add_argument('--no-sources', dest='include_sources', action='store_false', help='Do not include source documents')
    parser.add_argument('--endpoint', '-e', type=str, help='OpenSearch endpoint URL')
    parser.add_argument('--region', '-r', type=str, help='AWS region for Bedrock')
    
    parser.set_defaults(hybrid=True, include_sources=True)
    args = parser.parse_args()
    
    # Set environment variables if provided
    if args.endpoint:
        os.environ['OPENSEARCH_ENDPOINT'] = args.endpoint
    
    if args.region:
        os.environ['AWS_REGION'] = args.region
    
    # Run the RAG test
    test_rag(
        args.query, 
        args.top_k, 
        args.model, 
        args.hybrid, 
        args.max_tokens, 
        args.temperature, 
        args.include_sources
    )

if __name__ == "__main__":
    main() 