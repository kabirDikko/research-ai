output "s3_bucket_name" {
  value = module.s3.bucket_name
}

output "ingest_function_arn" {
  value = module.lambda.ingest_function_arn
}

output "opensearch_domain_endpoint" {
  value = module.opensearch.collection_endpoint
}

output "api_gateway_url" {
  value = module.api_gateway.invoke_url
}
