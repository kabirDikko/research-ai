terraform {
  backend "s3" {
    bucket         = "screenplay-ai-remote-state-bucket"
    key            = "state/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    use_lockfile = true
  }
}