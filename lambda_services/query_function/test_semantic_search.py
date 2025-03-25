#!/usr/bin/env python
"""
Test script for semantic search functionality.
This script simulates API requests to the semantic search Lambda function.
"""

import os
import json
import argparse
from semantic_search import search_documents

def test_search(query, top_k=5, hybrid=True):
    """Test the semantic search functionality"""
    print(f"Testing semantic search with query: '{query}'")
    print(f"Parameters: top_k={top_k}, hybrid_search={hybrid}")
    
    # Ensure environment variables are set
    if not os.environ.get('OPENSEARCH_ENDPOINT'):
        print("Warning: OPENSEARCH_ENDPOINT environment variable not set")
        opensearch_endpoint = input("Enter your OpenSearch endpoint URL: ")
        os.environ['OPENSEARCH_ENDPOINT'] = opensearch_endpoint
    
    # Call the search function
    result, status_code = search_documents(query, top_k, hybrid)
    
    # Print the status code
    print(f"\nStatus Code: {status_code}")
    
    # Format and print the results
    if status_code == 200:
        print("\n===== SEARCH RESULTS =====")
        print(f"Query: '{result['query']}'")
        print(f"Number of results: {len(result['results'])}")
        
        for i, item in enumerate(result['results'], 1):
            print(f"\n--- Result {i} ---")
            print(f"Score: {item['score']}")
            print(f"Filename: {item['filename']}")
            
            # Trim text for display if it's too long
            text = item['text']
            if len(text) > 200:
                text = text[:200] + "..."
            print(f"Text: {text}")
            
            # Print metadata
            print("Metadata:")
            for key, value in item['metadata'].items():
                print(f"  {key}: {value}")
    else:
        print("\n===== ERROR =====")
        print(result.get('error', 'Unknown error'))
    
    return result, status_code

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test semantic search functionality')
    parser.add_argument('--query', '-q', type=str, required=True, help='Search query text')
    parser.add_argument('--top-k', '-k', type=int, default=5, help='Number of results to return (default: 5)')
    parser.add_argument('--hybrid', action='store_true', help='Use hybrid search (vector + keyword)')
    parser.add_argument('--vector-only', dest='hybrid', action='store_false', help='Use vector search only')
    parser.add_argument('--endpoint', '-e', type=str, help='OpenSearch endpoint URL')
    parser.add_argument('--region', '-r', type=str, help='AWS region for Bedrock')
    
    parser.set_defaults(hybrid=True)
    args = parser.parse_args()
    
    # Set environment variables if provided
    if args.endpoint:
        os.environ['OPENSEARCH_ENDPOINT'] = args.endpoint
    
    if args.region:
        os.environ['AWS_REGION'] = args.region
    
    # Run the search test
    test_search(args.query, args.top_k, args.hybrid)

if __name__ == "__main__":
    main() 