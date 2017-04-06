variable "environment" { default = "dev" }
variable "project" { default = "gather2" }
variable "project_billing_id" { default = "gather2" }
variable "aws_region" { default = "eu-west-1" }

# RDS
variable "db_engine_type" { default="postgres" }
variable "db_engine_version" { default="9.5.4" }

//Because we create the VPC's separately we need to
//specify ID's here
variable "vpc_id" {
 default = "vpc-021b2966"
}

// and subnets
variable "public_subnets" {
 default = "subnet-51a0a427,subnet-c91011ad,subnet-cdd29095"
}

// and subnets
variable "private_subnets" {
 default = "subnet-5ca0a42a,subnet-ca1011ae,subnet-ced29096"
}
