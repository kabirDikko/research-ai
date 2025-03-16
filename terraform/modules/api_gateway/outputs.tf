output "invoke_url" {
  value       = length(aws_api_gateway_deployment.this) > 0 ? aws_api_gateway_deployment.this[0].invoke_url : ""
  description = "The URL to invoke the API Gateway"
}

output "id" {
  value       = length(aws_api_gateway_rest_api.this) > 0 ? aws_api_gateway_rest_api.this[0].id : ""
  description = "The ID of the API Gateway"
}

output "execution_arn" {
  value       = length(aws_api_gateway_rest_api.this) > 0 ? aws_api_gateway_rest_api.this[0].execution_arn : ""
  description = "The execution ARN of the API Gateway"
}

output "stage_name" {
  value       = length(aws_api_gateway_stage.this) > 0 ? aws_api_gateway_stage.this[0].stage_name : ""
  description = "The name of the API Gateway stage"
}
