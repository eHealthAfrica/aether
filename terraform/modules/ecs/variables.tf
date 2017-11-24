variable "aws_region" { default = "eu-west-1" }
variable "domain" {}
variable "environment" {}
variable "database_hostname" {}
variable "database_port" { default="5432" }
variable "internal_sg_id" {}
variable "iam_role_id" {}
variable "project" {}

# URL's
variable "kernel_url" {}
variable "odk_url" {}
variable "couchdb_sync_url" {}

variable "route53_zone_id" {
  type = "map"
  default = {
    ehealthafrica.org = "Z1B5Q25BUE3TXB"
    aether.org = "ZUBAIJA96RBHB"
  }
}

// aether kernel variables
variable "aether_kernel_container_name" { default="aether-kernel"}
variable "aether_kernel_nginx_host_port" { default=81 }
variable "aether_kernel_nginx_container_name" { default="aether-kernel-nginx" }
variable "aether_couchdb_container_name" { default="aether-couchdb" }

// aether ODK importer
variable "aether_odk_importer_container_name" { default="aether-odk-importer" }
variable "aether_odk_importer_nginx_host_port" { default=82 }
variable "aether_odk_importer_nginx_container_name" { default="aether-odk-importer-nginx" }

variable "private_subnets" { type="list" }
variable "public_subnets" { type="list" }
variable "vpc_id" {}
variable "deploy_branch" {}

variable "ssl_certificate_id" {
  type = "map"
  default = {
    ehealthafrica.org = "arn:aws:acm:eu-west-1:387526361725:certificate/b093a099-e453-4290-90b4-8a97f43174ec"
    aether.org = "arn:aws:acm:eu-west-1:387526361725:certificate/fbaf389d-f290-42ab-8902-0c051fa922e2"

  }
}

variable "bastion_sg_id" {
  type = "map"
  default = {
    dev = "sg-1241916b"
    prod = "sg-1b0e9762"
  }
}
