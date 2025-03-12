resource "aws_lambda_function" "ingest" {
  function_name    = var.ingest_function_name
  handler          = var.ingest_handler
  runtime          = var.runtime
  role             = var.lambda_role_arn
  filename         = var.ingest_zip_file
  source_code_hash = filebase64sha256(var.ingest_zip_file)
  environment {
    variables = var.ingest_env_vars
  }
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
}
