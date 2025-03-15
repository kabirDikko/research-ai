import os
import boto3
from pillow_heif import register_heif_opener
from PIL import Image
import io
import json

register_heif_opener()

s3_client = boto3.client('s3')
INGESTION_BUCKET = os.environ.get('INGESTION_BUCKET')
FAILED_INGESTION_BUCKET = os.environ.get('FAILED_INGESTION_BUCKET')

def handler(event, context):
    processed_files = []
    failed_files = []

    # Process files from S3 event trigger
    for record in event.get('Records', []):
        if record.get('s3'):
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            try:
                process_file(bucket, key)
                processed_files.append(key)
            except Exception as e:
                print(f"Error processing {key}: {e}")
                move_to_failed_bucket(bucket, key)
                failed_files.append(key)

    return {
        'processed': processed_files,
        'failed': failed_files
    }

def process_file(bucket, key):
    """Process a single file from the bucket"""
    if key.lower().endswith('.textclipping'):
        raise ValueError(f"Unsupported file type: {key}")

    # Determine output format
    if key.lower().endswith(('.heic', '.heif', '.tiff', '.tif')):
        dest_key = os.path.splitext(key)[0] + '.jpg'
        
        # Get the file from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
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
                Bucket=INGESTION_BUCKET,
                Key=dest_key,
                Body=jpeg_buffer.getvalue(),
                ContentType='image/jpeg'
            )
    else:
        # For other file types, just copy to ingestion bucket
        s3_client.copy_object(
            CopySource={'Bucket': bucket, 'Key': key},
            Bucket=INGESTION_BUCKET,
            Key=key
        )

def move_to_failed_bucket(source_bucket, key):
    """Move failed files to the failed ingestion bucket"""
    try:
        s3_client.copy_object(
            CopySource={'Bucket': source_bucket, 'Key': key},
            Bucket=FAILED_INGESTION_BUCKET,
            Key=key
        )
    except Exception as e:
        print(f"Error moving failed file {key} to failed bucket: {e}")