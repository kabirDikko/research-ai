import os
import boto3
import time
import urllib.parse
from pillow_heif import register_heif_opener
from PIL import Image
import io
import json
import requests
import datetime
import re

register_heif_opener()

s3_client = boto3.client('s3')
textract_client = boto3.client('textract')
opensearch_endpoint = os.environ.get('OPENSEARCH_ENDPOINT')
INGESTION_BUCKET = os.environ.get('INGESTION_BUCKET')
FAILED_INGESTION_BUCKET = os.environ.get('FAILED_INGESTION_BUCKET')
PROCESSED_INGESTION_BUCKET = os.environ.get('PROCESSED_INGESTION_BUCKET')

# Add Bedrock client for embeddings
bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.environ.get('AWS_REGION', 'us-east-1')
)

# Constants for embedding model
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"
EMBEDDING_DIMENSION = 1536  # Titan model dimension


def get_embeddings(text, max_chunk_size=8000):
    """
    Generate embeddings using Amazon Bedrock Titan Embeddings model.
    For longer texts, we chunk the text and create embeddings for each chunk.
    """
    if not text or not text.strip():
        print("Empty text provided for embeddings")
        return None
        
    try:
        # Ensure we don't exceed the model's maximum input size
        if len(text) > max_chunk_size:
            print(f"Text exceeds maximum size, truncating to {max_chunk_size} characters")
            text = text[:max_chunk_size]
            
        # Prepare the request body according to Titan embedding model requirements
        request_body = json.dumps({
            "inputText": text,
            "dimensions": EMBEDDING_DIMENSION,
            "normalize": True
        })

        # Call Bedrock to get embeddings
        response = bedrock_runtime.invoke_model(
            modelId=EMBEDDING_MODEL_ID,
            contentType="application/json",
            accept="*/*",
            body=request_body
        )
        
        # Parse the response
        response_body = json.loads(response.get("body").read())
        embedding = response_body.get("embedding")
        
        return embedding
    except Exception as e:
        print(f"Error generating embeddings: {str(e)}")
        return None


def get_s3_object_with_retry(bucket, key, max_retries=3):
    """Get an S3 object with retry logic to handle eventual consistency"""
    for attempt in range(max_retries):
        try:
            return s3_client.get_object(Bucket=bucket, Key=key)
        except s3_client.exceptions.NoSuchKey:
            if attempt == max_retries - 1:
                raise
            print(f"Object {key} not found in {bucket} (attempt {attempt+1}/{max_retries}), retrying...")
            time.sleep(2 ** attempt)  # Exponential backoff

def check_s3_object_exists_with_retry(bucket, key, max_retries=3):
    """Check if an S3 object exists with retry logic"""
    for attempt in range(max_retries):
        try:
            s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404' or e.response['Error']['Code'] == 'NoSuchKey':
                if attempt == max_retries - 1:
                    return False
                print(f"Object {key} not found in {bucket} (attempt {attempt+1}/{max_retries}), retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                # If it's a different error, raise it
                raise e

def sanitize_id(key):
    """Create a safe document ID for OpenSearch"""
    # Replace slashes with underscores
    doc_id = key.replace('/', '_')
    # Replace spaces with underscores
    doc_id = doc_id.replace(' ', '_')
    # Remove any characters that aren't alphanumeric, underscore, or hyphen
    doc_id = re.sub(r'[^\w\-]', '', doc_id)
    # Ensure the ID isn't too long (OpenSearch has limits)
    if len(doc_id) > 512:
        doc_id = doc_id[:512]
    return doc_id

def lambda_handler(event, context):
    processed_files = []
    failed_files = []

    # Process files from S3 event trigger
    for record in event.get('Records', []):
        if record.get('s3'):
            bucket = record['s3']['bucket']['name']
            # URL-decode the key to handle special characters and spaces
            encoded_key = record['s3']['object']['key']
            key = urllib.parse.unquote_plus(encoded_key)
            
            print(f"Processing event for object - Original key: {encoded_key}")
            print(f"Decoded key: {key}")
            
            # Check if the file exists with retry logic
            if not check_s3_object_exists_with_retry(bucket, key):
                print(f"File {key} does not exist in {bucket} after multiple attempts, skipping processing")
                failed_files.append(key)
                continue
                
            try:
                # Only process files from the ingestion bucket
                if bucket == INGESTION_BUCKET:
                    process_file(bucket, key)
                    processed_files.append(key)
                # Process files in the processed bucket with Textract
                elif bucket == PROCESSED_INGESTION_BUCKET:
                    extract_and_index_text(bucket, key)
                    processed_files.append(key)
            except Exception as e:
                print(f"Error processing {key}: {str(e)}")
                move_to_failed_bucket(bucket, key)
                failed_files.append(key)

    return {
        'processed': processed_files,
        'failed': failed_files
    }

def process_file(bucket, key):
    """Process a single file from the ingestion bucket and move to processed bucket"""
    if key.lower().endswith('.textclipping'):
        print(f"Unsupported file type: {key}")
        move_to_failed_bucket(bucket, key)
        raise ValueError(f"Unsupported file type: {key}")

    try:
        # Get just the filename without any folder structure
        filename = os.path.basename(key)
        
        # Determine output format
        if key.lower().endswith(('.heic', '.heif', '.tiff', '.tif')):
            # Use just the base filename without path for the destination
            dest_filename = os.path.splitext(filename)[0] + '.jpg'
            
            # Get the file from S3 with retry logic
            response = get_s3_object_with_retry(bucket, key)
            image_data = response['Body'].read()

            with io.BytesIO(image_data) as image_bytes:
                image = Image.open(image_bytes)

                if hasattr(image, 'n_frames') and image.n_frames > 1:
                    image.seek(0)

                if image.mode in ['RGBA', 'P', 'CMYK']:
                    image = image.convert('RGB')

                jpeg_buffer = io.BytesIO()
                image.save(jpeg_buffer, format='JPEG', quality=95)
                jpeg_buffer.seek(0)

                s3_client.put_object(
                    Bucket=PROCESSED_INGESTION_BUCKET,
                    Key=dest_filename,
                    Body=jpeg_buffer.getvalue(),
                    ContentType='image/jpeg'
                )
                
                print(f"Successfully converted {key} to JPEG and moved to processed bucket as {dest_filename}")
        else:
            # For other file types, just copy to processed bucket with just the filename
            s3_client.copy_object(
                CopySource={'Bucket': bucket, 'Key': key},
                Bucket=PROCESSED_INGESTION_BUCKET,
                Key=filename
            )
            print(f"Successfully moved {key} to processed bucket as {filename}")
            
    except Exception as e:
        print(f"Error processing file {key}: {str(e)}")
        move_to_failed_bucket(bucket, key)
        raise e

def extract_and_index_text(bucket, key):
    """Extract text from image using Textract, generate embeddings, and index in OpenSearch"""
    try:
        #TODO: Add support for other file types(.wav. mp3, etc.)
        if not key.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')):
            print(f"Skipping non-image/PDF file for Textract: {key}")
            return
        
        # Verify the file exists before processing with retry logic
        if not check_s3_object_exists_with_retry(bucket, key):
            print(f"File {key} does not exist in {bucket} after multiple attempts, skipping text extraction")
            return
            
        # Call Amazon Textract to extract text - use appropriate method for file type
        if key.lower().endswith('.pdf'):
            # For PDFs, we need to use the asynchronous API
            print(f"Starting asynchronous Textract job for PDF: {key}")
            
            # Start the asynchronous job
            response = textract_client.start_document_text_detection(
                DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': key}}
            )
            job_id = response['JobId']
            print(f"Started Textract job with ID: {job_id}")
            
            # Wait for the job to complete
            status = 'IN_PROGRESS'
            while status == 'IN_PROGRESS':
                time.sleep(5)
                response = textract_client.get_document_text_detection(JobId=job_id)
                status = response['JobStatus']
                print(f"Textract job status: {status}")
            
            if status == 'SUCCEEDED':
                # Get all pages of results
                extracted_text = ""
                pages = []
                
                # Get the first page of results
                pages.append(response)
                
                # If there are more pages, get them
                next_token = response.get('NextToken', None)
                while next_token:
                    response = textract_client.get_document_text_detection(
                        JobId=job_id,
                        NextToken=next_token
                    )
                    pages.append(response)
                    next_token = response.get('NextToken', None)
                
                # Extract text from all pages
                for page in pages:
                    for item in page['Blocks']:
                        if item['BlockType'] == 'LINE':
                            extracted_text += item['Text'] + "\n"
                
                # Continue with the extracted text
                print(f"Successfully extracted text from PDF: {key}")
            else:
                print(f"Textract job failed with status: {status}")
                raise Exception(f"Textract job failed with status: {status}")
        else:
            # For images, use the synchronous API
            response = textract_client.detect_document_text(
                Document={'S3Object': {'Bucket': bucket, 'Name': key}}
            )
            
            # Extract text blocks
            extracted_text = ""
            for item in response["Blocks"]:
                if item["BlockType"] == "LINE":
                    extracted_text += item["Text"] + "\n"
        
        if extracted_text.strip():
            # Generate embeddings using Bedrock
            print(f"Generating embeddings for extracted text from {key}")
            vector_embedding = get_embeddings(extracted_text)
            
            if not vector_embedding:
                print(f"Failed to generate embeddings for {key}, skipping indexing")
                return
                
            # Index the extracted text and embeddings in OpenSearch
            document = {
                "filename": os.path.basename(key),  # Just use the filename without path
                "text": extracted_text,  # Text field for search
                "vector": vector_embedding,  # Vector field for semantic search
                "text-metadata": json.dumps({  # Metadata about the document
                    "source_bucket": bucket,
                    "source_key": key,
                    "extraction_time": datetime.datetime.now().isoformat(),
                    "file_type": os.path.splitext(key)[1][1:].lower()
                })
            }
            
            # Check if OpenSearch endpoint is configured
            if not opensearch_endpoint:
                print("ERROR: OpenSearch endpoint is not configured. Cannot index document.")
                return
                
            # Create a safe document ID using just the filename
            index_id = sanitize_id(os.path.basename(key))
            
            # Force the https:// scheme if not present
            endpoint = opensearch_endpoint
            if not endpoint.startswith(('http://', 'https://')):
                endpoint = f"https://{endpoint}"
                
            # Ensure the URL is properly formed
            url = f"{endpoint}/documents/_doc/{index_id}"
            
            print(f"Indexing document with embeddings to OpenSearch URL: {url}")
            headers = {"Content-Type": "application/json"}
            
            try:
                response = requests.put(url, headers=headers, data=json.dumps(document))
                if response.status_code >= 200 and response.status_code < 300:
                    print(f"Successfully indexed text and embeddings from {key}")
                else:
                    print(f"Failed to index text from {key}: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"ERROR: Failed to connect to OpenSearch: {str(e)}")
        else:
            print(f"No text extracted from {key}")
    except Exception as e:
        print(f"Error extracting or indexing text from {key}: {str(e)}")
        # Don't raise the exception to allow processing to continue

def move_to_failed_bucket(source_bucket, key):
    """Move failed files to the failed ingestion bucket"""
    try:
        # Check if the file exists in the source bucket with retry logic
        if not check_s3_object_exists_with_retry(source_bucket, key, max_retries=2):
            print(f"File {key} does not exist in {source_bucket} after multiple attempts, skipping move to failed bucket")
            return
            
        # Get just the filename without any folder structure
        filename = os.path.basename(key)
        
        # If we get here, the file exists and we can try to copy it
        s3_client.copy_object(
            CopySource={'Bucket': source_bucket, 'Key': key},
            Bucket=FAILED_INGESTION_BUCKET,
            Key=filename
        )
        print(f"Moved failed file {key} to failed bucket as {filename}")
        
        #TODO: Delete the original file after copying to failed bucket
    except Exception as e:
        print(f"Error moving failed file {key} to failed bucket: {str(e)}")