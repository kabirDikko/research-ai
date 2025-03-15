output "bucket_name" {
  description = "Name of the main S3 bucket"
  value       = aws_s3_bucket.this.id
}

output "bucket_arn" {
  description = "ARN of the main S3 bucket"
  value       = aws_s3_bucket.this.arn
}

output "failed_ingestion_bucket_name" {
  description = "Name of the failed ingestion S3 bucket"
  value       = aws_s3_bucket.failed_ingestion.id
}

output "failed_ingestion_bucket_arn" {
  description = "ARN of the failed ingestion S3 bucket"
  value       = aws_s3_bucket.failed_ingestion.arn
}

