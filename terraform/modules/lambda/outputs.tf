output "ingest_function_arn" {
  value = aws_lambda_function.ingest.arn
}

output "ingest_function_name" {
  value = aws_lambda_function.ingest.function_name
}

output "query_lambda_invoke_arn" {
  value = aws_lambda_function.query.invoke_arn
}
