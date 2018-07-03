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
  app = "odk"
  application_memory = 512
  http_rule_priority = 30
  domain = "ehealthafrica"
}

module "kernel" {
  source = "git@github.com:eHealthAfrica/ehealth-deployment.git//terraform//modules//generic_ecs_service"
  environment = "${var.environment}"
  project = "${var.project}"
  database_hostname = "${module.rds.database_hostname}"
  app = "kernel"
  application_memory = 512
  http_rule_priority = 31
  domain = "ehealthafrica"
}
