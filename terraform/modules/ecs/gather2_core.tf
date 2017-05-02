// Gather2 core

// ECR core repository
resource "aws_ecr_repository" "gather2_core" {
  name = "${var.gather2_core_container_name}-${var.environment}"
}

resource "aws_ecr_repository" "gather2_core_nginx" {
  name = "${var.gather2_core_container_name}-nginx-${var.environment}"
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
  zone_id = "${var.route53_zone_id}"
  name    = "core-gather-${var.environment}"
  type    = "A"

  alias {
    name                   = "${aws_alb.gather2_core.dns_name}"
    zone_id                = "${aws_alb.gather2_core.zone_id}"
    evaluate_target_health = true
  }
}

resource "aws_alb_target_group" "gather2_core" {
  name     = "gather2-core-${var.environment}"
  port     = "${var.gather2_core_nginx_host_port}"
  protocol = "HTTP"
  vpc_id   = "${var.vpc_id}"
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

data "template_file" "gather2_core" {
  template = "${file("${path.module}/files/gather2_core_task_definition.json")}"

  vars {
    image_url  = "${aws_ecr_repository.gather2_core.repository_url}:latest"
    application_container_name = "${var.gather2_core_container_name}"
    nginx_container_name = "${var.gather2_core_nginx_container_name}"
    host_port = "${var.gather2_core_nginx_host_port}"
    nginx_image_url  = "${aws_ecr_repository.gather2_core_nginx.repository_url}:latest"
    database_hostname = "${var.database_hostname}"
    database_user = "${var.database_user}"
    database_password = "${data.credstash_secret.gather2_core.value}"
    database_name = "${var.database_name}"
    database_port = "${var.database_port}"
    django_use_x_forwarded_port = "1"
    django_http_x_forwarded_proto = "1"
    django_use_x_forwarded_host = "1"
  }
}

resource "aws_ecs_task_definition" "gather2_core" {
  family                = "${var.project}-${var.environment}"
  container_definitions = "${data.template_file.gather2_core.rendered}"

  volume {
    name = "static-core"
  }
}

data "aws_ecs_task_definition" "gather2_core" {
  task_definition = "${aws_ecs_task_definition.gather2_core.family}"
}

resource "aws_ecs_service" "gather2_core" {
  name            = "${var.gather2_core_container_name}"
  cluster         = "${aws_ecs_cluster.cluster.id}"
  task_definition = "${aws_ecs_task_definition.gather2_core.family}:${max("${aws_ecs_task_definition.gather2_core.revision}", "${data.aws_ecs_task_definition.gather2_core.revision}")}"
  desired_count   = 1
  iam_role        = "${var.iam_role_id}"

  load_balancer {
    target_group_arn = "${aws_alb_target_group.gather2_core.id}"
    container_name   = "${var.gather2_core_nginx_container_name}"
    container_port   = 80
  }
  depends_on = [
    "aws_alb_listener.gather2_core_http"
  ]
}
