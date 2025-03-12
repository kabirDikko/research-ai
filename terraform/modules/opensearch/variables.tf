variable "collection_name" {
  description = "Name of the OpenSearch Serverless collection"
  type        = string
  default     = "story-documents"
}

variable "vpc_endpoint_id" {
  description = "The ID of the VPC endpoint"
  type        = string
}

variable "region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-east-1"
}

