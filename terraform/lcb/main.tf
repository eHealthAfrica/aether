module "rds" {
  source = "git@github.com:eHealthAfrica/ehealth-deployment.git//terraform//modules//rds"
  project = "${var.project}"
  environment = "${var.environment}"
  private_subnets = "${split(",", var.private_subnets)}"
  internal_sg_id = "${module.autoscaling.internal_sg_id}"
  db_engine_type = "${var.db_engine_type}"
  db_engine_version = "${var.db_engine_version}"
  project_billing_id = "${var.project_billing_id}"
}

module "efs" {
  source = "git@github.com:eHealthAfrica/ehealth-deployment.git//terraform//modules//efs"
  private_subnets = "${split(",", var.private_subnets)}"
  aws_region = "${var.aws_region}"
  performance_mode = "maxIO"
  internal_sg_id = "${module.autoscaling.internal_sg_id}"
}

module "ecs" {
  source = "../modules/ecs"
  environment = "${var.environment}"
  vpc_id = "${var.vpc_id}"
  project = "${var.project}"
  private_subnets = "${split(",", var.private_subnets)}"
  public_subnets = "${split(",", var.public_subnets)}"
  internal_sg_id = "${module.autoscaling.internal_sg_id}"
  iam_role_id = "${module.autoscaling.aws_iam_role_ecs_service}"
  database_hostname = "${module.rds.database_hostname}"
  deploy_branch = "latest"
  domain = "gather2.org"
  core_url = "${var.core_url}"
  odk_url = "${var.odk_url}"
  couchdb_sync_url = "${var.couchdb_sync_url}"
}

# // Creates ECS cluster and SG's
module "autoscaling" {
  source = "git@github.com:eHealthAfrica/ehealth-deployment.git//terraform//modules//autoscaling"
  environment = "${var.environment}"
  project = "${var.project}"
  project_billing_id = "${var.project_billing_id}"
  private_subnets = "${split(",", var.private_subnets)}"
  vpc_id = "${var.vpc_id}"
  target_group_arns = ["${module.ecs.core_target_group}","${module.ecs.odk_importer_target_group}","${module.ecs.couchdb_sync_target_group}"]
  efs_id = "${module.efs.efs_output}"
}
