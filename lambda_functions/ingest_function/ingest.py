import boto3
import os
import json
import requests
import datetime
import io
import sys

# Print Python path for debugging
print(f"Python path before modification: {sys.path}")

# Add the Lambda layer path to sys.path to ensure we use the layer version of PIL
sys.path.insert(0, '/opt/python')

# Print Python path after modification for debugging
print(f"Python path after modification: {sys.path}")

# Print available modules in /opt/python
try:
    print(f"Contents of /opt/python: {os.listdir('/opt/python')}")
except Exception as e:
    print(f"Error listing /opt/python: {str(e)}")

# Now import PIL from the Lambda layer
try:
    from PIL import Image
    print(f"Successfully imported PIL from {Image.__file__}")
except Exception as e:
    print(f"Error importing PIL: {str(e)}")
    raise

try:
    from pillow_heif import register_heif_opener
    print(f"Successfully imported pillow_heif")
except Exception as e:
    print(f"Error importing pillow_heif: {str(e)}")
    raise

# Register HEIF opener with Pillow
try:
    register_heif_opener()
    print("Successfully registered HEIF opener")
except Exception as e:
    print(f"Error registering HEIF opener: {str(e)}")
    raise

def lambda_handler(event, context):
    # Extract bucket and object details from the S3 event
    record = event['Records'][0]
    bucket_name = record['s3']['bucket']['name']
    object_key = record['s3']['object']['key']
    
    # Determine file extension to handle accordingly
    file_ext = object_key.split('.')[-1].lower()
    s3_client = boto3.client('s3')
    
    # Download file to temporary storage in Lambda (/tmp)
    local_path = f"/tmp/{os.path.basename(object_key)}"
    s3_client.download_file(bucket_name, object_key, local_path)
    
    extracted_text = ""
    
    # Get the error bucket name from environment variables
    error_bucket = os.environ.get("ERROR_BUCKET")
    if not error_bucket:
        print("ERROR_BUCKET environment variable not set, using default")
        error_bucket = f"{bucket_name}-failed-ingestion"
    
    # Convert HEIC/TIFF to JPG if needed
    if file_ext in ['heic', 'heif', 'tiff', 'tif']:
        try:
            converted_path = convert_image_to_jpg(local_path)
            if converted_path:
                local_path = converted_path
                file_ext = 'jpg'
            else:
                raise Exception("Image conversion failed")
        except Exception as e:
            # Move failed file to error bucket
            error_key = f"failed_conversions/{object_key}"
            try:
                s3_client.copy_object(
                    CopySource={'Bucket': bucket_name, 'Key': object_key},
                    Bucket=error_bucket,
                    Key=error_key
                )
                print(f"Moved failed file to error bucket: {error_key}")
            except Exception as copy_error:
                print(f"Failed to move file to error bucket: {str(copy_error)}")
            
            extracted_text = f"Error converting {file_ext} image to JPG: {str(e)}"
    
    if not extracted_text:  # Only process if no conversion error
        if file_ext == 'pdf':
            extracted_text = process_pdf(local_path)
        elif file_ext in ['jpg', 'jpeg', 'png']:
            extracted_text = process_image(local_path)
        elif file_ext in ['mp3', 'wav', 'ogg']:
            # Voice processing is deferred for now
            extracted_text = "Voice recording processing is pending."
        else:
            extracted_text = f"File type {file_ext} is not supported for extraction."
            # Move unsupported file to error bucket
            error_key = f"unsupported_files/{object_key}"
            try:
                s3_client.copy_object(
                    CopySource={'Bucket': bucket_name, 'Key': object_key},
                    Bucket=error_bucket,
                    Key=error_key
                )
                print(f"Moved unsupported file to error bucket: {error_key}")
            except Exception as copy_error:
                print(f"Failed to move file to error bucket: {str(copy_error)}")
    
    # Prepare metadata for indexing
    metadata = {
        "bucket_name": bucket_name,
        "object_key": object_key,
    }
    
    # Save the extracted text and metadata to OpenSearch
    os_response = index_to_opensearch(extracted_text, metadata)
    print("OpenSearch indexing response:", os_response.text)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            "extracted_text": extracted_text,
            "open_search_response": os_response.text
        })
    }

def convert_image_to_jpg(file_path):
    """
    Convert HEIC/TIFF images to JPG format
    Returns the path to converted JPG file or None if conversion fails
    """
    try:
        with open(file_path, 'rb') as image_file:
            image_data = image_file.read()
            
        with io.BytesIO(image_data) as image_bytes:
            image = Image.open(image_bytes)
            
            # Handle multi-page TIFF
            if hasattr(image, 'n_frames') and image.n_frames > 1:
                image.seek(0)
            
            # Convert color mode if needed
            if image.mode in ['RGBA', 'P', 'CMYK']:
                image = image.convert('RGB')
            
            # Save as JPG
            jpg_path = os.path.splitext(file_path)[0] + '.jpg'
            image.save(jpg_path, format='JPEG', quality=95)
            return jpg_path
            
    except Exception as e:
        print(f"Error converting image: {str(e)}")
        raise

def process_pdf(file_path):
    textract = boto3.client('textract')
    with open(file_path, 'rb') as document:
        file_bytes = document.read()
    
    # Use Textract's synchronous API to process the PDF
    response = textract.analyze_document(
        Document={'Bytes': file_bytes},
        FeatureTypes=["TABLES", "FORMS"]
    )
    return extract_text_from_response(response)

def process_image(file_path):
    textract = boto3.client('textract')
    with open(file_path, 'rb') as document:
        file_bytes = document.read()
    
    response = textract.detect_document_text(
        Document={'Bytes': file_bytes}
    )
    return extract_text_from_response(response)

def extract_text_from_response(response):
    """
    Helper function to extract text from a Textract response by concatenating LINE blocks.
    """
    lines = []
    for block in response.get('Blocks', []):
        if block['BlockType'] == 'LINE':
            lines.append(block['Text'])
    return "\n".join(lines)

def index_to_opensearch(extracted_text, metadata):
    """
    Index the document in OpenSearch with the extracted text and metadata.
    """
    # Retrieve the OpenSearch endpoint from the Lambda environment variables
    opensearch_endpoint = os.environ.get("OPENSEARCH_ENDPOINT")
    if not opensearch_endpoint:
        raise Exception("OPENSEARCH_ENDPOINT environment variable not set")
    
    # Define the index name; adjust as needed.
    index_name = "documents"
    
    # Create a document ID by sanitizing the object_key
    document_id = metadata.get("object_key").replace("/", "-")
    
    # Build the URL for the document in the OpenSearch index
    url = f"{opensearch_endpoint}/{index_name}/_doc/{document_id}"
    
    headers = {"Content-Type": "application/json"}
    
    # Prepare the document payload
    document = {
        "bucket_name": metadata.get("bucket_name"),
        "object_key": metadata.get("object_key"),
        "extracted_text": extracted_text,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    
    # Index (or update) the document using an HTTP PUT request
    response = requests.put(url, headers=headers, data=json.dumps(document))
    return response