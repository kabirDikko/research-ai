variable "region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket to store documents"
  type        = string
  default     = "your-unique-bucket-name"
}

variable "ingest_zip_file" {
  description = "Path to the zipped code for the ingest lambda function"
  type        = string
}

variable "query_zip_file" {
  description = "Path to the zipped code for the query lambda function"
  type        = string
}

variable "bedrock_endpoint_url" {
  description = "The Bedrock endpoint URL for LLM inference"
  type        = string
}

variable "collection_name" {
  description = "The name of the OpenSearch Serverless collection"
  type        = string
}

variable "lambda_invoke_arn" {
  description = "The ARN of the Lambda function to invoke"
  type        = string
  default     = null
}




