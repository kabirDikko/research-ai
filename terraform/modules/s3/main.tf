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

    expiration {
      days = var.failed_ingestion_retention_days
    }
  }
}

resource "aws_s3_bucket_notification" "this" {
  bucket = aws_s3_bucket.this.id

  lambda_function {
    lambda_function_arn = var.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
  }
}

resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.this.arn
}
