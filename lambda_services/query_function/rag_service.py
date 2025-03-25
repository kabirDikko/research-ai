import os
import json
import boto3
from semantic_search import search_documents

# Initialize Bedrock client for LLM
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.environ.get('AWS_REGION', 'us-east-1')
)

# Default LLM model settings
DEFAULT_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-sonnet-20240229-v1:0')
DEFAULT_MAX_TOKENS = int(os.environ.get('MAX_TOKENS', 4096))
DEFAULT_TEMPERATURE = float(os.environ.get('TEMPERATURE', 0.7))
DEFAULT_TOP_P = float(os.environ.get('TOP_P', 0.9))

def format_context(search_results, max_context_length=10000):
    """
    Format search results into a context string for the LLM
    """
    if not search_results or not search_results.get('results'):
        return "No relevant documents found."
    
    context_parts = []
    current_length = 0
    
    for result in search_results.get('results', []):
        # Get text content
        document_text = result.get('text', '')
        filename = result.get('filename', 'unknown')
        
        # Skip empty documents
        if not document_text.strip():
            continue
            
        # Format document section
        document_section = f"Document: {filename}\n\n{document_text}\n\n"
        section_length = len(document_section)
        
        # Check if adding this document would exceed the max context length
        if current_length + section_length > max_context_length:
            # If we already have some context, break
            if context_parts:
                break
            # Otherwise, truncate this document to fit
            available_length = max_context_length - current_length - 100  # Leave some buffer
            document_section = f"Document: {filename}\n\n{document_text[:available_length]}... (truncated)\n\n"
            
        # Add document to context
        context_parts.append(document_section)
        current_length += section_length
    
    # Combine all context parts
    if context_parts:
        return "".join(context_parts)
    else:
        return "No relevant document content could be extracted."

def invoke_claude(prompt, model_id=DEFAULT_MODEL_ID, max_tokens=DEFAULT_MAX_TOKENS, 
                 temperature=DEFAULT_TEMPERATURE, top_p=DEFAULT_TOP_P):
    """
    Invoke Claude model via Amazon Bedrock
    """
    try:
        # Prepare request body based on model
        if "claude" in model_id.lower():
            # Claude-specific request format
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        else:
            # Generic request format for other models
            request_body = {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p
            }
            
        # Invoke Bedrock model
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response.get("body").read())
        
        # Extract completion based on model type
        if "claude" in model_id.lower():
            # Claude response format
            completion = response_body.get("content", [{}])[0].get("text", "")
        else:
            # Generic response format
            completion = response_body.get("completion", "")
            
        return completion
        
    except Exception as e:
        print(f"Error invoking LLM: {str(e)}")
        return f"Error generating response: {str(e)}"

def invoke_titan(prompt, model_id="amazon.titan-text-express-v1", max_tokens=DEFAULT_MAX_TOKENS,
                temperature=DEFAULT_TEMPERATURE, top_p=DEFAULT_TOP_P):
    """
    Invoke Titan model via Amazon Bedrock
    """
    try:
        # Titan-specific request format
        request_body = {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": max_tokens,
                "temperature": temperature,
                "topP": top_p,
                "stopSequences": []
            }
        }
            
        # Invoke Bedrock model
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        # Parse the response
        response_body = json.loads(response.get("body").read())
        completion = response_body.get("results", [{}])[0].get("outputText", "")
            
        return completion
        
    except Exception as e:
        print(f"Error invoking Titan LLM: {str(e)}")
        return f"Error generating response: {str(e)}"

def generate_prompt(query, context):
    """
    Generate a prompt for the LLM using the query and document context
    """
    return f"""You are a helpful AI assistant that answers questions based on the provided documents.
Use ONLY the information from the provided documents to answer the question.
If the documents don't contain the answer, say "I don't have enough information to answer this question."
Don't make up information that's not in the documents.

CONTEXT DOCUMENTS:
{context}

USER QUESTION: {query}

ANSWER:"""

def rag_query(query, top_k=5, model_id=DEFAULT_MODEL_ID, hybrid_search=True, 
             max_tokens=DEFAULT_MAX_TOKENS, temperature=DEFAULT_TEMPERATURE, 
             top_p=DEFAULT_TOP_P, include_sources=True):
    """
    Perform a RAG query: search for relevant documents and generate a response using an LLM
    """
    try:
        # Step 1: Search for relevant documents
        search_result, status_code = search_documents(query, top_k, hybrid_search)
        
        if status_code != 200:
            return {"error": search_result.get("error", "Search failed")}, status_code
            
        # Step 2: Format the context from search results
        context = format_context(search_result)
        
        # Step 3: Generate the prompt for the LLM
        prompt = generate_prompt(query, context)
        
        # Step 4: Invoke the LLM based on model type
        if "claude" in model_id.lower():
            # Use Claude-specific invocation
            response_text = invoke_claude(prompt, model_id, max_tokens, temperature, top_p)
        elif "titan" in model_id.lower():
            # Use Titan-specific invocation
            response_text = invoke_titan(prompt, model_id, max_tokens, temperature, top_p)
        else:
            # Use default Claude invocation
            response_text = invoke_claude(prompt, DEFAULT_MODEL_ID, max_tokens, temperature, top_p)
        
        # Step 5: Format and return the response
        result = {
            "query": query,
            "response": response_text
        }
        
        # Include sources if requested
        if include_sources:
            sources = []
            for doc in search_result.get("results", []):
                sources.append({
                    "filename": doc.get("filename"),
                    "score": doc.get("score"),
                    "metadata": doc.get("metadata", {})
                })
            result["sources"] = sources
            
        return result, 200
            
    except Exception as e:
        print(f"Error in RAG query: {str(e)}")
        return {"error": f"RAG query failed: {str(e)}"}, 500

def lambda_handler(event, context):
    """
    Lambda handler for the RAG service API
    Accepts query parameters:
    - q: Query text (required)
    - k: Top K results (optional, default 5)
    - model: Bedrock model ID (optional)
    - hybrid: Whether to use hybrid search (optional, default true)
    - max_tokens: Maximum tokens in response (optional)
    - temperature: LLM temperature (optional)
    - include_sources: Whether to include source documents (optional, default true)
    """
    try:
        # Parse different types of events (API Gateway, direct invocation)
        if event.get('httpMethod') == 'GET' and event.get('queryStringParameters'):
            # API Gateway GET request
            params = event.get('queryStringParameters', {})
            query_text = params.get('q', '')
            top_k = int(params.get('k', '5'))
            model_id = params.get('model', DEFAULT_MODEL_ID)
            hybrid = params.get('hybrid', 'true').lower() == 'true'
            max_tokens = int(params.get('max_tokens', DEFAULT_MAX_TOKENS))
            temperature = float(params.get('temperature', DEFAULT_TEMPERATURE))
            top_p = float(params.get('top_p', DEFAULT_TOP_P))
            include_sources = params.get('include_sources', 'true').lower() == 'true'
            
        elif event.get('body') and event.get('httpMethod') == 'POST':
            # API Gateway POST request
            body = json.loads(event.get('body', '{}'))
            query_text = body.get('query', '')
            top_k = int(body.get('top_k', 5))
            model_id = body.get('model', DEFAULT_MODEL_ID)
            hybrid = body.get('hybrid', True)
            max_tokens = int(body.get('max_tokens', DEFAULT_MAX_TOKENS))
            temperature = float(body.get('temperature', DEFAULT_TEMPERATURE))
            top_p = float(body.get('top_p', DEFAULT_TOP_P))
            include_sources = body.get('include_sources', True)
            
        elif event.get('querytext'):
            # Direct invocation with parameters
            query_text = event.get('querytext', '')
            top_k = int(event.get('top_k', 5))
            model_id = event.get('model', DEFAULT_MODEL_ID)
            hybrid = event.get('hybrid', True)
            max_tokens = int(event.get('max_tokens', DEFAULT_MAX_TOKENS))
            temperature = float(event.get('temperature', DEFAULT_TEMPERATURE))
            top_p = float(event.get('top_p', DEFAULT_TOP_P))
            include_sources = event.get('include_sources', True)
            
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
            
        # Execute the RAG query
        result, status_code = rag_query(
            query_text, top_k, model_id, hybrid, 
            max_tokens, temperature, top_p, include_sources
        )
        
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