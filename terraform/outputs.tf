output "s3_bucket_name" {
  value = module.s3.bucket_name
}


output "opensearch_domain_endpoint" {
  value = module.opensearch.collection_endpoint
}

output "api_gateway_url" {
  value = module.api_gateway.invoke_url
}

# Output the Lambda role ARN for use in serverless.yml
output "lambda_role_arn" {
  value       = aws_iam_role.lambda_role.arn
  description = "ARN of the Lambda IAM role for use in serverless.yml"
}