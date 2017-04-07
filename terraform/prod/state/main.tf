module "backend" {
  source = "git@github.com:eHealthAfrica/ehealth-deployment//terraform//modules//backend"
  project = "${var.project}"
  environment = "${var.environment}"
}