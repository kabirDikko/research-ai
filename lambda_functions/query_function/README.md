# Query Function
This function handles user queries and invokes Bedrock for story generation.

## Overview

The query function processes user queries and generates a story using Bedrock. It performs the following steps:

1. Extracts the user query from the event
2. Searches OpenSearch for relevant documents
3. Aggregates context from search results
4. Calls Bedrock to generate a story
5. Returns the generated story in the response

## How it Works

### Step 1: Extract User Query
The function extracts the user query from the event payload.

### Step 2: Search OpenSearch
It constructs a search query against the OpenSearch index and sends it to the endpoint.
### Step 3: Aggregate Context
The function combines relevant document excerpts from the search results into a single context string.

### Step 4: Generate Story with Bedrock
The function constructs a prompt combining the user query and aggregated context, then sends it to Bedrock for story generation.

### Step 5: Return Response
Returns a JSON response containing the generated story.

## Required Environment Variables
- `OPENSEARCH_ENDPOINT`: The endpoint URL for your OpenSearch domain
- `BEDROCK_ENDPOINT`: The endpoint URL for AWS Bedrock

## Dependencies
The function requires the following Python packages (see requirements.txt):
- requests==2.28.2
- boto3==1.33.1

## IAM Permissions
The function requires IAM permissions for:
- OpenSearch operations (ESHttpPost, ESHttpGet)
- Bedrock operations

## Input Format
The function expects a JSON event with:
{
  "query": "user's query"
}

## Output Format
The function returns a JSON response with:  
{
  "statusCode": 200,
  "body": "{\"story\": \"generated story\"}"
}               





