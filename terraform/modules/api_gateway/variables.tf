variable "api_name" {
  description = "Name of the API Gateway"
  type        = string
}

variable "api_description" {
  description = "Description for the API Gateway"
  type        = string
}

variable "resource_path" {
  description = "Path part for the query resource"
  type        = string
  default     = "query"
}

variable "lambda_invoke_arn" {
  description = "Lambda function invoke ARN for integration"
  type        = string
  default     = null
}

variable "stage_name" {
  description = "Deployment stage name"
  type        = string
  default     = "prod"
}
