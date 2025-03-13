resource "aws_lambda_function" "ingest" {
  function_name    = var.ingest_function_name
  handler          = var.ingest_handler
  runtime          = var.runtime
  role             = var.lambda_role_arn
  filename         = var.ingest_zip_file
  source_code_hash = filebase64sha256(var.ingest_zip_file)
  timeout          = 30  # Increase timeout for image processing
  memory_size      = 512 # Increase memory for image processing

  # Add the Pillow Lambda layer
  layers = [
    "arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p39-pillow:1"
  ]

  environment {
    variables = merge(var.ingest_env_vars, {
      ERROR_BUCKET = var.failed_ingestion_bucket_name
    })
  }

  # Enable basic CloudWatch logging
  tracing_config {
    mode = "PassThrough"
  }

  depends_on = [aws_cloudwatch_log_group.ingest_logs]
}

resource "aws_cloudwatch_log_group" "ingest_logs" {
  name              = "/aws/lambda/${var.ingest_function_name}"
  retention_in_days = 1 # Minimum retention period
}

resource "aws_lambda_function" "query" {
  function_name    = var.query_function_name
  handler          = var.query_handler
  runtime          = var.runtime
  role             = var.lambda_role_arn
  filename         = var.query_zip_file
  source_code_hash = filebase64sha256(var.query_zip_file)
  environment {
    variables = var.query_env_vars
  }

  # Enable basic CloudWatch logging
  tracing_config {
    mode = "PassThrough"
  }

  depends_on = [aws_cloudwatch_log_group.query_logs]
}

resource "aws_cloudwatch_log_group" "query_logs" {
  name              = "/aws/lambda/${var.query_function_name}"
  retention_in_days = 1 # Minimum retention period
}
