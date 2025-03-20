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

register_heif_opener()

s3_client = boto3.client('s3')
textract_client = boto3.client('textract')
opensearch_endpoint = os.environ.get('OPENSEARCH_ENDPOINT')
INGESTION_BUCKET = os.environ.get('INGESTION_BUCKET')
FAILED_INGESTION_BUCKET = os.environ.get('FAILED_INGESTION_BUCKET')
PROCESSED_INGESTION_BUCKET = os.environ.get('PROCESSED_INGESTION_BUCKET')

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
        # Determine output format
        if key.lower().endswith(('.heic', '.heif', '.tiff', '.tif')):
            dest_key = os.path.splitext(key)[0] + '.jpg'
            
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
                    Key=dest_key,
                    Body=jpeg_buffer.getvalue(),
                    ContentType='image/jpeg'
                )
                
                print(f"Successfully converted {key} to JPEG and moved to processed bucket as {dest_key}")
        else:
            # For other file types, just copy to processed bucket
            s3_client.copy_object(
                CopySource={'Bucket': bucket, 'Key': key},
                Bucket=PROCESSED_INGESTION_BUCKET,
                Key=key
            )
            print(f"Successfully moved {key} to processed bucket")
            
    except Exception as e:
        print(f"Error processing file {key}: {str(e)}")
        move_to_failed_bucket(bucket, key)
        raise e

def extract_and_index_text(bucket, key):
    """Extract text from image using Textract and index in OpenSearch"""
    try:
        # Only process image files and PDFs with Textract
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
            # For now we'll use synchronous but with first page only
            # In production, you should implement the async workflow
            response = textract_client.detect_document_text(
                Document={'S3Object': {'Bucket': bucket, 'Name': key}}
            )
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
            # Index the extracted text in OpenSearch
            document = {
                "filename": key,
                "extracted_text": extracted_text,
                "source_bucket": bucket,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Send to OpenSearch
            headers = {"Content-Type": "application/json"}
            index_id = key.replace('/', '_')
            url = f"{opensearch_endpoint}/documents/_doc/{index_id}"
            
            response = requests.put(url, headers=headers, data=json.dumps(document))
            if response.status_code >= 200 and response.status_code < 300:
                print(f"Successfully indexed text from {key}")
            else:
                print(f"Failed to index text from {key}: {response.text}")
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
            
        # If we get here, the file exists and we can try to copy it
        s3_client.copy_object(
            CopySource={'Bucket': source_bucket, 'Key': key},
            Bucket=FAILED_INGESTION_BUCKET,
            Key=key
        )
        print(f"Moved failed file {key} to failed bucket")
        
        # Delete the original file after copying to failed bucket
        # Uncomment this if you want to delete after moving
        # s3_client.delete_object(Bucket=source_bucket, Key=key)
    except Exception as e:
        print(f"Error moving failed file {key} to failed bucket: {str(e)}")