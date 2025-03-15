import os
import json
import boto3
import requests

def lambda_handler(event, context):
    # Step 1: Extract user query from the event
    user_query = event.get("query", "default query")
    
    # Step 2: Search OpenSearch for relevant context
    opensearch_endpoint = os.environ.get("OPENSEARCH_ENDPOINT")
    search_results = search_opensearch(opensearch_endpoint, user_query)
    
    # Step 3: Aggregate results into context
    context_text = aggregate_context(search_results)
    
    # Step 4: Combine the user query and context
    prompt = f"Using the following context, generate a creative story:\n\nContext:\n{context_text}\n\nQuery: {user_query}"
    
    # Step 5: Call AWS Bedrock (or your chosen LLM service) with the prompt
    bedrock_endpoint = os.environ.get("BEDROCK_ENDPOINT")
    generated_story = call_bedrock(bedrock_endpoint, prompt)
    
    # Step 6: Return the generated story to the user
    return {
        "statusCode": 200,
        "body": json.dumps({"story": generated_story})
    }

def search_opensearch(endpoint, query):
    # Construct a search query against your OpenSearch index
    url = f"{endpoint}/documents/_search"
    headers = {"Content-Type": "application/json"}
    payload = {
        "query": {
            "match": {
                "extracted_text": query
            }
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.json()

def aggregate_context(search_results):
    # Combine relevant document excerpts from search results
    hits = search_results.get("hits", {}).get("hits", [])
    context_parts = [hit["_source"]["extracted_text"] for hit in hits]
    return "\n".join(context_parts)

def call_bedrock(endpoint, prompt):
    # Send the prompt to Bedrock and get the generated text
    headers = {"Content-Type": "application/json"}
    payload = {"prompt": prompt}
    response = requests.post(endpoint, headers=headers, data=json.dumps(payload))
    return response.json().get("generated_text", "No text generated")