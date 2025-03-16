locals {
  create_api_gateway = var.lambda_invoke_arn != null && var.lambda_invoke_arn != ""
}

# Use local.create_api_gateway for conditional creation
resource "aws_api_gateway_rest_api" "this" {
  count       = local.create_api_gateway ? 1 : 0
  name        = var.api_name
  description = var.api_description
}

resource "aws_api_gateway_resource" "query_resource" {
  count       = local.create_api_gateway ? 1 : 0
  rest_api_id = aws_api_gateway_rest_api.this[0].id
  parent_id   = aws_api_gateway_rest_api.this[0].root_resource_id
  path_part   = var.resource_path
}

resource "aws_api_gateway_method" "post_method" {
  count         = local.create_api_gateway ? 1 : 0
  rest_api_id   = aws_api_gateway_rest_api.this[0].id
  resource_id   = aws_api_gateway_resource.query_resource[0].id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_integration" {
  count                   = local.create_api_gateway ? 1 : 0
  rest_api_id             = aws_api_gateway_rest_api.this[0].id
  resource_id             = aws_api_gateway_resource.query_resource[0].id
  http_method             = aws_api_gateway_method.post_method[0].http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.lambda_invoke_arn
}

resource "aws_api_gateway_deployment" "this" {
  count       = local.create_api_gateway ? 1 : 0
  depends_on  = [aws_api_gateway_integration.lambda_integration[0]]
  rest_api_id = aws_api_gateway_rest_api.this[0].id
  
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.query_resource[0].id,
      aws_api_gateway_method.post_method[0].id,
      aws_api_gateway_integration.lambda_integration[0].id
    ]))
  }
  
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "this" {
  count         = local.create_api_gateway ? 1 : 0
  deployment_id = aws_api_gateway_deployment.this[0].id
  rest_api_id   = aws_api_gateway_rest_api.this[0].id
  stage_name    = var.stage_name
}