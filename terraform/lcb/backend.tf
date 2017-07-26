terraform {
  backend "s3" {
        bucket = "eha-prod-state-files"
        key = "gather2-lake-chad-basin-prod/terraform.tfstate"
        region = "eu-west-1"
        lock_table = "gather2-lake-chad-basin-prod-terraform-lock"
  }
}
