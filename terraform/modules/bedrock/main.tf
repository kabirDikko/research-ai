resource "aws_ssm_parameter" "bedrock_endpoint" {
  name        = "/bedrock/endpoint"
  description = "Bedrock LLM endpoint URL for story generation"
  type        = "String"
  value       = var.bedrock_endpoint_url
}

output "bedrock_endpoint" {
  value = aws_ssm_parameter.bedrock_endpoint.value
}
