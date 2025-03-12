region                = "us-east-1"
s3_bucket_name        = "research-ingestion-bucket"
ingest_zip_file       = "../lambda_functions/ingest_function/ingest.zip"
query_zip_file        = "../lambda_functions/query_function/query.zip"
bedrock_endpoint_url  = "https://bedrock.example.com"

# OpenSearch Serverless specific variables
collection_name       = "story-documents"
