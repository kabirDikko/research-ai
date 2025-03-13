output "bucket_name" {
  value = aws_s3_bucket.this.bucket
}

output "bucket_arn" {
  value = aws_s3_bucket.this.arn
}

output "failed_ingestion_bucket_name" {
  value = aws_s3_bucket.failed_ingestion.bucket
}

output "failed_ingestion_bucket_arn" {
  value = aws_s3_bucket.failed_ingestion.arn
}

