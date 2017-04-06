terraform {
  backend "s3" {
        bucket = "eha-dev-state-files"
        key = "gather2-dev/terraform.tfstate"
        region = "eu-west-1"
        lock_table = "gather2-dev-terraform-lock"
  }
}