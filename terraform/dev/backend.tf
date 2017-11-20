terraform {
  backend "s3" {
        bucket = "eha-dev-state-files"
        key = "aether-dev/terraform.tfstate"
        region = "eu-west-1"
        lock_table = "aether-dev-terraform-lock"
  }
}
