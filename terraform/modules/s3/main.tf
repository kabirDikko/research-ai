resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name

  lifecycle {
    prevent_destroy = true
  }
}

# Create a bucket for failed ingestions
resource "aws_s3_bucket" "failed_ingestion" {
  bucket = "${var.bucket_name}-failed-ingestion"

  lifecycle {
    prevent_destroy = true
  }
}

# Add lifecycle policy to failed ingestion bucket to expire objects after a certain period
resource "aws_s3_bucket_lifecycle_configuration" "failed_ingestion_lifecycle" {
  bucket = aws_s3_bucket.failed_ingestion.id

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


