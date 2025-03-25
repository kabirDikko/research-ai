#!/bin/bash

# Setup and test script for RAG Query Service
echo "======= RAG Query Service Setup and Test ======="

# Set up environment variables for testing
echo "Setting up environment variables..."

# Check if AWS_REGION is set, otherwise default to us-east-1
if [ -z "$AWS_REGION" ]; then
  export AWS_REGION="us-east-1"
  echo "Setting AWS_REGION to default: us-east-1"
else
  echo "Using existing AWS_REGION: $AWS_REGION"
fi

# Ask for OpenSearch endpoint if not already set
if [ -z "$OPENSEARCH_ENDPOINT" ]; then
  echo -n "Enter your OpenSearch endpoint (without http/https): "
  read opensearch_endpoint
  export OPENSEARCH_ENDPOINT=$opensearch_endpoint
  echo "Set OPENSEARCH_ENDPOINT to: $OPENSEARCH_ENDPOINT"
else
  echo "Using existing OPENSEARCH_ENDPOINT: $OPENSEARCH_ENDPOINT"
fi

# Ask for Bedrock model if not already set
if [ -z "$BEDROCK_MODEL_ID" ]; then
  echo -n "Enter Bedrock model ID (or press enter for Claude 3 Sonnet): "
  read bedrock_model
  if [ -z "$bedrock_model" ]; then
    export BEDROCK_MODEL_ID="anthropic.claude-3-sonnet-20240229-v1:0"
  else
    export BEDROCK_MODEL_ID=$bedrock_model
  fi
  echo "Set BEDROCK_MODEL_ID to: $BEDROCK_MODEL_ID"
else
  echo "Using existing BEDROCK_MODEL_ID: $BEDROCK_MODEL_ID"
fi

# Check if AWS credentials are set
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
  echo "Warning: AWS credentials not found in environment variables."
  echo "Make sure you have configured AWS credentials using aws configure or environment variables."
fi

# Install required packages
echo -e "\nInstalling required packages..."
pip install -r ../requirements.txt

# Create test query input file
echo -e "\nCreating test.txt with sample questions..."
cat > test.txt << EOF
What is the main topic of document 1?
How does document processing work?
Extract the key points from the documents.
Is there any information about AI integration?
EOF

echo "Created test.txt with sample questions. Edit this file to add your own questions."

# Run the tests
echo -e "\n======= Testing Options ======="
echo "1) Test semantic search only"
echo "2) Test full RAG service"
echo "3) Run both tests"
echo "4) Exit"

echo -n "Select an option (1-4): "
read option

case $option in
  1)
    # Test semantic search
    echo -e "\nTesting semantic search..."
    echo -n "Enter your search query: "
    read query
    python test_semantic_search.py --query "$query"
    ;;
  2)
    # Test RAG service
    echo -e "\nTesting RAG service..."
    echo -n "Enter your question: "
    read query
    python test_rag_service.py --query "$query"
    ;;
  3)
    # Run both tests with the same query
    echo -e "\nRunning both tests..."
    echo -n "Enter your query: "
    read query
    echo -e "\n--- Semantic Search Test ---"
    python test_semantic_search.py --query "$query"
    echo -e "\n--- RAG Service Test ---"
    python test_rag_service.py --query "$query"
    ;;
  4)
    # Exit
    echo "Exiting..."
    exit 0
    ;;
  *)
    echo "Invalid option. Exiting."
    exit 1
    ;;
esac

echo -e "\n======= Test Complete ======="
echo "You can run individual tests with the following commands:"
echo "  python test_semantic_search.py --query \"Your search query\""
echo "  python test_rag_service.py --query \"Your question\""
echo ""
echo "For more options, use the --help flag:"
echo "  python test_semantic_search.py --help"
echo "  python test_rag_service.py --help" 