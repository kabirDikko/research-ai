variable "ingest_function_name" {
  description = "Lambda function name for ingestion"
  type        = string
}

variable "query_function_name" {
  description = "Lambda function name for query handling"
  type        = string
}

variable "ingest_handler" {
  description = "Handler for the ingestion Lambda function"
  type        = string
}

variable "query_handler" {
  description = "Handler for the query Lambda function"
  type        = string
}

variable "runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.9"
}

variable "lambda_role_arn" {
  description = "IAM Role ARN for Lambda functions"
  type        = string
}

variable "ingest_zip_file" {
  description = "Path to the zipped code for ingest Lambda"
  type        = string
}

variable "query_zip_file" {
  description = "Path to the zipped code for query Lambda"
  type        = string
}

variable "ingest_env_vars" {
  description = "Environment variables for ingest Lambda"
  type        = map(string)
  default     = {}
}

variable "query_env_vars" {
  description = "Environment variables for query Lambda"
  type        = map(string)
  default     = {}
}
