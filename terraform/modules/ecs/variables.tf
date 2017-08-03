variable "aws_region" { default = "eu-west-1" }
variable "domain" {}
variable "environment" {}
variable "database_hostname" {}
variable "database_port" { default="5432" }
variable "internal_sg_id" {}
variable "iam_role_id" {}
variable "project" {}

# URL's
variable "core_url" {}
variable "odk_url" {}
variable "couchdb_sync_url" {}

variable "route53_zone_id" {
  type = "map"
  default = {
    ehealthafrica.org = "Z1B5Q25BUE3TXB"
    gather2.org = "ZUBAIJA96RBHB"
  }
}

// gather2 core variables
variable "gather2_core_container_name" { default="gather2-core"}
variable "gather2_core_nginx_host_port" { default=81 }
variable "gather2_core_nginx_container_name" { default="gather2-core-nginx" }
variable "gather2_couchdb_container_name" { default="gather2-couchdb" }

// gather2 ODK importer
variable "gather2_odk_importer_container_name" { default="gather2-odk-importer" }
variable "gather2_odk_importer_nginx_host_port" { default=82 }
variable "gather2_odk_importer_nginx_container_name" { default="gather2-odk-importer-nginx" }

variable "private_subnets" { type="list" }
variable "public_subnets" { type="list" }
variable "vpc_id" {}
variable "deploy_branch" {}

variable "ssl_certificate_id" {
  type = "map"
  default = {
    ehealthafrica.org = "arn:aws:acm:eu-west-1:387526361725:certificate/b093a099-e453-4290-90b4-8a97f43174ec"
    gather2.org = "arn:aws:acm:eu-west-1:387526361725:certificate/fbaf389d-f290-42ab-8902-0c051fa922e2"

  }
}

variable "bastion_sg_id" {
  type = "map"
  default = {
    dev = "sg-1241916b"
    prod = "sg-1b0e9762"
  }
}
