resource "aws_opensearchserverless_collection" "this" {
  name = var.collection_name
  type = "SEARCH"
  depends_on = [aws_opensearchserverless_security_policy.encryption_policy]
}


resource "aws_opensearchserverless_security_policy" "encryption_policy" {
  name        = "${var.collection_name}-encryption-policy"
  type        = "encryption"
  description = "encryption policy for ${var.collection_name}"
  policy = jsonencode({
    Rules = [
      {
        Resource = [
          "collection/${var.collection_name}"
        ],
        ResourceType = "collection"
      }
    ],
    AWSOwnedKey = true
  })
}


resource "aws_opensearchserverless_access_policy" "data_policy" {
  name        = "${var.collection_name}-data-policy"
  type        = "data"
  description = "Data access policy for ${var.collection_name}"
  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "index",
          Resource = [
            "index/${var.collection_name}/*"
          ],
          Permission = [
            "aoss:*"
          ]
        },
        {
          ResourceType = "collection", 
          Resource = [
            "collection/${var.collection_name}"
          ],
          Permission = [
            "aoss:*"
          ]
        }
      ],
      Principal = [
        data.aws_caller_identity.current.arn
      ]
    }
  ])
}

# Creates a network security policy
resource "aws_opensearchserverless_security_policy" "network_policy" {
  name        = "${var.collection_name}-network-policy"
  type        = "network"
  description = "Network security policy for ${var.collection_name}"
  policy = jsonencode([
    {
      Description = "VPC access for collection endpoint",
      Rules = [
        {
          ResourceType = "collection",
          Resource = [
            "collection/${var.collection_name}"
          ]
        }
      ],
      AllowFromPublic = false,
      SourceVPCEs = [
        var.vpc_endpoint_id
      ]
    },
    {
      Description = "Public access for dashboards", 
      Rules = [
        {
          ResourceType = "dashboard",
          Resource = [
            "collection/${var.collection_name}"
          ]
        }
      ],
      AllowFromPublic = true
    }
  ])
}