module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "story-generator-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true
  enable_vpn_gateway = true

  # Enable DNS hostnames for VPC endpoint
  enable_dns_hostnames = true
  enable_dns_support   = true
}

# Security group for VPC endpoint
resource "aws_security_group" "vpc_endpoint" {
  name        = "opensearch-vpc-endpoint-sg"
  description = "Security group for OpenSearch Serverless VPC endpoint"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }
}

resource "aws_opensearchserverless_vpc_endpoint" "vpc_endpoint" {
  name               = "story-generator-vpc-endpoint"
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnets
  security_group_ids = [aws_security_group.vpc_endpoint.id]
}

# Create IAM Role for Lambda functions
resource "aws_iam_role" "lambda_role" {
  name = "story-generator-lambda_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "story-generator-lambda_policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = "s3:*",
        Resource = "*"
      },
      {
        Effect   = "Allow",
        Action   = ["textract:*", "rekognition:*"],
        Resource = "*"
      },
      {
        Effect   = "Allow",
        Action   = ["es:ESHttpPost", "es:ESHttpPut", "es:ESHttpGet"],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}



module "s3" {
  source      = "./modules/s3"
  ingestion_bucket_name = var.ingestion_bucket_name
  processed_ingestion_bucket_name = var.processed_ingestion_bucket_name
  failed_ingestion_bucket_name = var.failed_ingestion_bucket_name
}

module "opensearch" {
  source          = "./modules/opensearch"
  collection_name = "story-documents"
  vpc_endpoint_id = aws_opensearchserverless_vpc_endpoint.vpc_endpoint.id
}


module "bedrock" {
  source               = "./modules/bedrock"
  bedrock_endpoint_url = var.bedrock_endpoint_url
}

module "api_gateway" {
  source            = "./modules/api_gateway"
  api_name          = "story-generator-api"
  api_description   = "API for story generation"
  resource_path     = "query"
  lambda_invoke_arn = var.lambda_invoke_arn
  stage_name        = "prod"
}



