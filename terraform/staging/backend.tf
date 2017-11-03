terraform {
  backend "s3" {
        bucket = "eha-staging-state-files"
        key = "gather2-staging/terraform.tfstate"
        region = "eu-west-1"
        lock_table = "gather2-staging-terraform-lock"
  }
}
