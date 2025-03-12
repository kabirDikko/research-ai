output "collection_endpoint" {
  value = "https://${aws_opensearchserverless_collection.this.name}.aoss-serverless.${var.region}.opensearch.amazonaws.com"
}
