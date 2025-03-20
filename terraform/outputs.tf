
output "opensearch_collection_endpoint" {
  value = module.opensearch.collection_endpoint
}

output "api_gateway_url" {
  value = module.api_gateway.invoke_url
}

output "lambda_role_arn" {
  value       = aws_iam_role.lambda_role.arn
  description = "ARN of the Lambda IAM role for use in serverless.yml"
}

output "ingestion_bucket_name" {
  value = module.s3.ingestion_bucket_name
}

output "failed_ingestion_bucket_name" {
  value = module.s3.failed_ingestion_bucket_name
}

output "processed_ingestion_bucket_name" {
  value = module.s3.processed_ingestion_bucket_name
}

output "opensearch_dashboard_endpoint" {
  value = module.opensearch.dashboard_endpoint
}

