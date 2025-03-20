resource "aws_s3_bucket" "ingestion_bucket" {
  bucket = var.ingestion_bucket_name

}

resource "aws_s3_bucket" "processed_ingestion_bucket" {
  bucket = var.processed_ingestion_bucket_name

}

# Create a bucket for failed ingestions
resource "aws_s3_bucket" "failed_ingestion_bucket" {
  bucket = var.failed_ingestion_bucket_name

}

# Add lifecycle policy to failed ingestion bucket to expire objects after a certain period
resource "aws_s3_bucket_lifecycle_configuration" "failed_ingestion_lifecycle" {
  bucket = aws_s3_bucket.failed_ingestion_bucket.id

  rule {
    id     = "expire-failed-ingestions"
    status = "Enabled"

    filter {
      prefix = "" # Empty prefix means apply to all objects
    }

    expiration {
      days = var.failed_ingestion_retention_days
    }
  }
}


