provider "aws" {
  region = "${var.aws_region}"
}

provider "credstash" {
  table  = "credential-store"
  region = "us-east-1"
}
