// Gather2-odk-importer

// ECR core repository
resource "aws_ecr_repository" "gather2_odk_importer" {
  name = "${var.gather2_odk_importer_container_name}-${var.environment}"
}

resource "aws_ecr_repository" "gather2_odk_importer_nginx" {
  name = "${var.gather2_odk_importer_container_name}-nginx-${var.environment}"
}

resource "aws_alb" "gather2_odk_importer" {
  internal = false
  subnets = ["${var.public_subnets}"]
  security_groups = ["${aws_security_group.lb_sg.id}"]

  enable_deletion_protection = false

  tags {
    key = "stack"
    name =  "${var.project}-${var.environment}"
  }
}

resource "aws_route53_record" "gather2_odk_importer" {
  zone_id = "${var.route53_zone_id}"
  name    = "odk-gather-${var.environment}"
  type    = "A"

  alias {
    name                   = "${aws_alb.gather2_odk_importer.dns_name}"
    zone_id                = "${aws_alb.gather2_odk_importer.zone_id}"
    evaluate_target_health = true
  }
}

resource "aws_alb_target_group" "gather2_odk_importer" {
  name     = "gather2-odk-${var.environment}"
  port     = "${var.gather2_odk_importer_nginx_host_port}"
  protocol = "HTTP"
  vpc_id   = "${var.vpc_id}"
}

resource "aws_alb_listener" "gather2_odk_importer_http" {
  load_balancer_arn = "${aws_alb.gather2_odk_importer.id}"
  port              = "80"
  protocol          = "HTTP"

  default_action {
    target_group_arn = "${aws_alb_target_group.gather2_odk_importer.id}"
    type             = "forward"
  }
}

resource "aws_alb_listener" "gather2_odk_importer_https" {
  load_balancer_arn = "${aws_alb.gather2_odk_importer.id}"
  port = "443"
  protocol = "HTTPS"
  ssl_policy = "ELBSecurityPolicy-2015-05"
  certificate_arn =  "${lookup(var.ssl_certificate_id, var.domain)}"

  default_action {
    target_group_arn = "${aws_alb_target_group.gather2_odk_importer.arn}"
    type = "forward"
  }
}

data "credstash_secret" "gather2_odk_importer" {
  name = "${var.project}-${var.environment}-database-password"
}

data "template_file" "gather2_odk_importer" {
  template = "${file("${path.module}/files/gather2_odk_importer_task_definition.json")}"

  vars {
    image_url = "${aws_ecr_repository.gather2_odk_importer.repository_url}"
    application_container_name = "${var.gather2_odk_importer_container_name}"
    nginx_container_name = "${var.gather2_odk_importer_nginx_container_name}"
    host_port = "${var.gather2_odk_importer_nginx_host_port}",
    nginx_image_url = "${aws_ecr_repository.gather2_odk_importer_nginx.repository_url}:latest"
    database_hostname = "${var.database_hostname}"
    database_user = "${var.database_user}"
    database_password = "${data.credstash_secret.gather2_odk_importer.value}"
    database_name = "${var.database_name}"
    database_port = "${var.database_port}"
    django_use_x_forwarded_port = "1"
    django_http_x_forwarded_proto = "1"
    django_use_x_forwarded_host = "1"
  }
}

resource "aws_ecs_task_definition" "gather2_odk_importer" {
  family  = "${var.project}-${var.environment}"
  container_definitions = "${data.template_file.gather2_odk_importer.rendered}"

  volume {
    name  = "static-odk-importer"
  }
}

data "aws_ecs_task_definition" "gather2_core" {
  task_definition = "${aws_ecs_task_definition.gather2_odk_importer.family}"
}

resource "aws_ecs_service" "gather2_odk_importer" {
  name            = "gather2-odk-importer"
  cluster         = "${aws_ecs_cluster.cluster.id}"
  task_definition = "${aws_ecs_task_definition.gather2_odk_importer.family}:${max("${aws_ecs_task_definition.gather2_odk_importer.revision}", "${data.aws_ecs_task_definition.gather2_odk_importer.revision}")}"
  desired_count   = 1
  iam_role        = "${var.iam_role_id}"

  load_balancer {
    target_group_arn = "${aws_alb_target_group.gather2_odk_importer.id}"
    container_name   = "${var.gather2_odk_importer_nginx_container_name}"
    container_port   = 80
  }
  depends_on = [
    "aws_alb_listener.gather2_odk_importer_http"
  ]
}
