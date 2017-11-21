terraform {
  backend "s3" {
        bucket = "eha-production-state-files"
        key = "aether-prod/terraform.tfstate"
        region = "eu-west-1"
        lock_table = "aether-prod-terraform-lock"
  }
}