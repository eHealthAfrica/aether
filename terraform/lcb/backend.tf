terraform {
  backend "s3" {
        bucket = "eha-prod-state-files"
        key = "aether-lake-chad-basin-prod/terraform.tfstate"
        region = "eu-west-1"
        lock_table = "aether-lake-chad-basin-prod-terraform-lock"
  }
}
