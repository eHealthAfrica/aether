module "rds" {
  source = "git@github.com:eHealthAfrica/ehealth-deployment.git//terraform//modules//rds"
  project = "${var.project}"
  environment = "${var.environment}"
  project_billing_id = "${var.project_billing_id}"
  cluster_name = "ehealth-africa-dev"
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
  database_hostname = "${module.rds.database_hostname}"
  service = "couchdb"
  container_memory = 512
  data_dir = "/var/lib/couchdb"
  app = "sync"
  port = 5984
  domain = "ehealthafrica"
}

module "redis" {
  // source = "git@github.com:eHealthAfrica/ehealth-deployment.git//terraform//modules//generic_ecs_service"
  source = "../../../ehealth-deployment/terraform/modules/generic_ecs_data_service"
  environment = "${var.environment}"
  project = "${var.project}"
  image_url = "redis"
  database_hostname = "${module.rds.database_hostname}"
  service = "redis"
  container_memory = 512
  app = "sync"
  port = 6379
  data_dir = "/data"
  domain = "ehealthafrica"
}
