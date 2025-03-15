variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}


variable "failed_ingestion_retention_days" {
  description = "Number of days to retain failed ingestion files before deletion"
  type        = number
  default     = 5
}
