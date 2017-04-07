terraform {
  backend "s3" {
        bucket = "eha-production-state-files"
        key = "gather2-prod/terraform.tfstate"
        region = "eu-west-1"
        lock_table = "gather2-prod-terraform-lock"
  }
}