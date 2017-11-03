module "rds" {
  source = "git@github.com:eHealthAfrica/ehealth-deployment.git//terraform//modules//rds"
  project = "${var.project}"
  environment = "${var.environment}"
  project_billing_id = "${var.project_billing_id}"
  cluster_name = "ehealth-africa-staging"
}

module "odk" {
  source = "git@github.com:eHealthAfrica/ehealth-deployment.git//terraform//modules//generic_ecs_service"
  environment = "${var.environment}"
  project = "${var.project}"
  database_hostname = "${module.rds.database_hostname}"
  app = "odk-importer"
  application_memory = 512
  http_rule_priority = 11
  domain = "ehealthafrica"
}

module "core" {
  source = "git@github.com:eHealthAfrica/ehealth-deployment.git//terraform//modules//generic_ecs_service"
  environment = "${var.environment}"
  project = "${var.project}"
  database_hostname = "${module.rds.database_hostname}"
  app = "core"
  application_memory = 512
  http_rule_priority = 12 
  domain = "ehealthafrica"
}

module "ui" {
  source = "git@github.com:eHealthAfrica/ehealth-deployment.git//terraform//modules//generic_ecs_service"
  environment = "${var.environment}"
  project = "${var.project}"
  database_hostname = "${module.rds.database_hostname}"
  app = "ui"
  application_memory = 512
  http_rule_priority = 14 
  domain = "ehealthafrica"
}

module "couchcb_sync" {
  source = "git@github.com:eHealthAfrica/ehealth-deployment.git//terraform//modules//generic_ecs_service"
  environment = "${var.environment}"
  project = "${var.project}"
  app = "couchdb-sync"
  database_hostname = "${module.rds.database_hostname}"
  application_memory = 512
  http_rule_priority = 13 
  domain = "ehealthafrica"
}

module "couchcb" {
  // source = "git@github.com:eHealthAfrica/ehealth-deployment.git//terraform//modules//generic_ecs_service"
  source = "../../../ehealth-deployment/terraform/modules/generic_ecs_data_service"
  image_url = "couchdb"
  environment = "${var.environment}"
  project = "${var.project}"
  service = "couchdb"
  container_memory = 512
  data_dir = "/var/lib/couchdb"
  port = 5984
}

module "redis" {
  // source = "git@github.com:eHealthAfrica/ehealth-deployment.git//terraform//modules//generic_ecs_service"
  source = "../../../ehealth-deployment/terraform/modules/generic_ecs_data_service"
  environment = "${var.environment}"
  project = "${var.project}"
  image_url = "redis"
  service = "redis"
  container_memory = 512
  port = 6379
  data_dir = "/data"
}
