import os
import boto3
from pillow_heif import register_heif_opener
from PIL import Image
import io
import json

register_heif_opener()

s3_client = boto3.client('s3')

SOURCE_BUCKET = os.environ.get('SOURCE_BUCKET')
DESTINATION_BUCKET = os.environ.get('DESTINATION_BUCKET')

def handler(event, context):
    processed_files = []
    skipped_files = []

    existing_files = get_existing_files()

    # Check if this is an S3 event trigger
    if event.get('Records') and len(event.get('Records', [])) > 0 and event['Records'][0].get('s3'):
        # Process files from S3 event trigger
        for record in event['Records']:
            key = record['s3']['object']['key']
            process_file(key, existing_files, processed_files, skipped_files)
    else:
        # This is a manual invocation - process all files in the bucket
        print("Manual invocation detected - processing all files in the source bucket")
        process_all_files(existing_files, processed_files, skipped_files)

    return {
        'processed': processed_files,
        'skipped': skipped_files
    }

def get_existing_files():
    existing_files = set()
    paginator = s3_client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=DESTINATION_BUCKET):
        for obj in page.get('Contents', []):
            existing_files.add(obj['Key'])
    return existing_files

def process_all_files(existing_files, processed_files, skipped_files):
    """Process all files in the source bucket"""
    paginator = s3_client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=SOURCE_BUCKET):
        for obj in page.get('Contents', []):
            key = obj['Key']
            process_file(key, existing_files, processed_files, skipped_files)

def process_file(key, existing_files, processed_files, skipped_files):
    if key.lower().endswith('.textclipping'):
        skipped_files.append(key)
        return

    dest_key = key
    if key.lower().endswith(('.heic', '.heif', '.tiff', '.tif')):
        dest_key = os.path.splitext(key)[0] + '.jpg'

    if dest_key in existing_files:
        skipped_files.append(key)
        return

    try:
        if key.lower().endswith(('.heic', '.heif', '.tiff', '.tif')):
            response = s3_client.get_object(Bucket=SOURCE_BUCKET, Key=key)
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
                    Bucket=DESTINATION_BUCKET,
                    Key=dest_key,
                    Body=jpeg_buffer.getvalue(),
                    ContentType='image/jpeg'
                )

        else:
            s3_client.copy_object(
                CopySource={'Bucket': SOURCE_BUCKET, 'Key': key},
                Bucket=DESTINATION_BUCKET,
                Key=key
            )

        processed_files.append(dest_key)

    except Exception as e:
        skipped_files.append(key)
        print(f"Error processing {key}: {e}")