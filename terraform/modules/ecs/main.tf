resource "aws_s3_bucket" "deployment-config-bucket" {
    bucket = "eha-deployment-config"
    acl = "private"

    versioning {
      enabled = true
    }
}