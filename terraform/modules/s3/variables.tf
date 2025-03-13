variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "lambda_function_arn" {
  description = "ARN of the Lambda function to trigger"
  type        = string
}

variable "lambda_function_name" {
  description = "Name of the Lambda function"
  type        = string
}


variable "failed_ingestion_retention_days" {
  description = "Number of days to retain failed ingestion files before deletion"
  type        = number
  default     = 5
}
