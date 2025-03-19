output "ingestion_bucket_name" {
  description = "Name of the ingestion S3 bucket"
  value       = aws_s3_bucket.ingestion_bucket.id
}

output "ingestion_bucket_arn" {
  description = "ARN of the ingestion S3 bucket"
  value       = aws_s3_bucket.ingestion_bucket.arn
}

output "processed_ingestion_bucket_name" {
  description = "Name of the processed ingestion S3 bucket"
  value       = aws_s3_bucket.processed_ingestion_bucket.id
}

output "processed_ingestion_bucket_arn" {
  description = "ARN of the processed ingestion S3 bucket"
  value       = aws_s3_bucket.processed_ingestion_bucket.arn
}

output "failed_ingestion_bucket_name" {
  description = "Name of the failed ingestion S3 bucket"
  value       = aws_s3_bucket.failed_ingestion_bucket.id
}

output "failed_ingestion_bucket_arn" {
  description = "ARN of the failed ingestion S3 bucket"
  value       = aws_s3_bucket.failed_ingestion_bucket.arn
}
