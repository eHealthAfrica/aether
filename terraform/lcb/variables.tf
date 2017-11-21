variable "environment" { default = "prod" }
variable "project" { default = "aether-lcb" }
variable "project_billing_id" { default = "aether" }
variable "aws_region" { default = "eu-west-1" }

# RDS
variable "db_engine_type" { default="postgres" }
variable "db_engine_version" { default="9.5.4" }

//Because we create the VPC's separately we need to
//specify ID's here
variable "vpc_id" {
 default = "vpc-a10230c5"
}

// and subnets
variable "public_subnets" {
 default = "subnet-7aaeaa0c,subnet-22161746,subnet-19d49641"
}

// and subnets
variable "private_subnets" {
 default = "subnet-7daeaa0b,subnet-21161745,subnet-1ad49642"
}

// Core URL
variable "core_url" { default="lakechadbasin" }
variable "odk_url" { default="lakechadbasin-odk" }
variable "couchdb_sync_url" { default="lakechadbasin-couchdb-sync" }

// Domain 
variable "domain" { default="aether.org" }
