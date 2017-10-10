// Gather2 core

// ECR core repository
resource "aws_ecr_repository" "gather2_core" {
  name = "${var.project}-core-${var.environment}"
}

resource "aws_ecr_repository" "gather2_core_nginx" {
  name = "${var.project}-core-nginx-${var.environment}"
}

resource "aws_alb" "gather2_core" {
  internal        = false
  subnets = ["${var.public_subnets}"]
  security_groups = ["${aws_security_group.lb_sg.id}"]

  enable_deletion_protection = false

  tags {
    key = "stack"
    name =  "${var.project}-${var.environment}"
  }
}

resource "aws_route53_record" "gather2_core" {
  zone_id = "${lookup("${var.route53_zone_id}","${var.domain}")}"
  name    = "${replace("${var.core_url}-${var.environment}", "-prod", "")}"
  type    = "A"

  alias {
    name                   = "${aws_alb.gather2_core.dns_name}"
    zone_id                = "${aws_alb.gather2_core.zone_id}"
    evaluate_target_health = true
  }
}

resource "aws_alb_target_group" "gather2_core" {
  name     = "${var.project}-core-${var.environment}"
  port     = 80
  protocol = "HTTP"
  vpc_id   = "${var.vpc_id}"

  health_check {
    path = "/health"
  }
}

resource "aws_alb_listener" "gather2_core_http" {
  load_balancer_arn = "${aws_alb.gather2_core.id}"
  port              = "80"
  protocol          = "HTTP"

  default_action {
    target_group_arn = "${aws_alb_target_group.gather2_core.id}"
    type             = "forward"
  }
}

resource "aws_alb_listener" "gather2_core_https" {
  load_balancer_arn = "${aws_alb.gather2_core.id}"
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy = "ELBSecurityPolicy-2015-05"
  certificate_arn =  "${lookup(var.ssl_certificate_id, var.domain)}"

  default_action {
    target_group_arn = "${aws_alb_target_group.gather2_core.id}"
    type             = "forward"
  }
}

data "credstash_secret" "gather2_core" {
  name = "${var.project}-${var.environment}-database-password"
}

data "credstash_secret" "gather2_core_sentry_dsn" {
  name = "${var.project}-${var.environment}-sentry-dsn"
}

data "credstash_secret" "aws_key_core" {
  name = "ecs-secrets-${var.environment}-aws_key"
}

data "credstash_secret" "aws_secret_key_core" {
  name = "ecs-secrets-${var.environment}-aws_secret_key"
}

data "template_file" "gather2_core" {
  template = "${file("${path.module}/files/gather2_core_task_definition.json")}"

  vars {
    image_url  = "${aws_ecr_repository.gather2_core.repository_url}:${var.deploy_branch}"
    application_container_name = "${var.gather2_core_container_name}"
    nginx_container_name = "${var.gather2_core_nginx_container_name}"
    host_port = "${var.gather2_core_nginx_host_port}"
    nginx_image_url  = "${aws_ecr_repository.gather2_core_nginx.repository_url}:latest"
    database_hostname = "${var.database_hostname}"
    database_password = "${data.credstash_secret.gather2_core.value}"
    database_name = "${replace("${var.project}", "-", "_")}"
    database_user = "${replace("${var.project}", "-", "")}"
    database_port = "${var.database_port}"
    django_use_x_forwarded_port = "1"
    django_http_x_forwarded_proto = "1"
    django_use_x_forwarded_host = "1"
    domain = ".${var.domain}"
    sentry_dsn = "${data.credstash_secret.gather2_core_sentry_dsn.value}"
    aws_key = "${data.credstash_secret.aws_key_core.value}"
    aws_secret_key = "${data.credstash_secret.aws_secret_key_core.value}"
  }
}

resource "aws_ecs_task_definition" "gather2_core" {
  family                = "${var.project}-core-${var.environment}"
  container_definitions = "${data.template_file.gather2_core.rendered}"

  volume {
    name = "static-core"
  }

  volume {
    host_path = "/data/upload-data"
    name = "upload-data"
  }
}

data "aws_ecs_task_definition" "gather2_core" {
  task_definition = "${aws_ecs_task_definition.gather2_core.family}"
}

resource "aws_ecs_service" "gather2_core" {
  name            = "${var.project}-core"
  cluster         = "${aws_ecs_cluster.cluster.id}"
  task_definition = "${aws_ecs_task_definition.gather2_core.family}:${max("${aws_ecs_task_definition.gather2_core.revision}", "${data.aws_ecs_task_definition.gather2_core.revision}")}"
  desired_count   = 1
  iam_role        = "${var.iam_role_id}"

  load_balancer {
    target_group_arn = "${aws_alb_target_group.gather2_core.id}"
    container_name   = "core-nginx"
    container_port   = 80
  }
  depends_on = [
    "aws_alb_listener.gather2_core_http"
  ]
}

output "core_target_group" {
  value = "${aws_alb_target_group.gather2_core.arn}"
}
