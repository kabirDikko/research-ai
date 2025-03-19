variable "region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "ingestion_bucket_name" {
  description = "Name of the S3 bucket to store documents"
  type        = string

}

variable "processed_ingestion_bucket_name" {
  description = "Name of the S3 bucket to store processed documents"
  type        = string

}

variable "failed_ingestion_bucket_name" {
  description = "Name of the S3 bucket to store failed documents"
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




