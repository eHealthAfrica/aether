// Aether kernel

// ECR kernel repository
resource "aws_ecr_repository" "aether_kernel" {
  name = "${var.project}-kernel-${var.environment}"
}

resource "aws_ecr_repository" "aether_kernel_nginx" {
  name = "${var.project}-kernel-nginx-${var.environment}"
}

resource "aws_alb" "aether_kernel" {
  internal        = false
  subnets = ["${var.public_subnets}"]
  security_groups = ["${aws_security_group.lb_sg.id}"]

  enable_deletion_protection = false

  tags {
    key = "stack"
    name =  "${var.project}-${var.environment}"
  }
}

resource "aws_route53_record" "aether_kernel" {
  zone_id = "${lookup("${var.route53_zone_id}","${var.domain}")}"
  name    = "${replace("${var.kernel_url}-${var.environment}", "-prod", "")}"
  type    = "A"

  alias {
    name                   = "${aws_alb.aether_kernel.dns_name}"
    zone_id                = "${aws_alb.aether_kernel.zone_id}"
    evaluate_target_health = true
  }
}

resource "aws_alb_target_group" "aether_kernel" {
  name     = "${var.project}-kernel-${var.environment}"
  port     = 80
  protocol = "HTTP"
  vpc_id   = "${var.vpc_id}"

  health_check {
    path = "/health"
  }
}

resource "aws_alb_listener" "aether_kernel_http" {
  load_balancer_arn = "${aws_alb.aether_kernel.id}"
  port              = "80"
  protocol          = "HTTP"

  default_action {
    target_group_arn = "${aws_alb_target_group.aether_kernel.id}"
    type             = "forward"
  }
}

resource "aws_alb_listener" "aether_kernel_https" {
  load_balancer_arn = "${aws_alb.aether_kernel.id}"
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy = "ELBSecurityPolicy-2015-05"
  certificate_arn =  "${lookup(var.ssl_certificate_id, var.domain)}"

  default_action {
    target_group_arn = "${aws_alb_target_group.aether_kernel.id}"
    type             = "forward"
  }
}

data "credstash_secret" "aether_kernel" {
  name = "${var.project}-${var.environment}-database-password"
}

data "credstash_secret" "aether_kernel_sentry_dsn" {
  name = "${var.project}-${var.environment}-sentry-dsn"
}

data "credstash_secret" "aws_key_kernel" {
  name = "ecs-secrets-${var.environment}-aws_key"
}

data "credstash_secret" "aws_secret_key_kernel" {
  name = "ecs-secrets-${var.environment}-aws_secret_key"
}

data "template_file" "aether_kernel" {
  template = "${file("${path.module}/files/aether_kernel_task_definition.json")}"

  vars {
    image_url  = "${aws_ecr_repository.aether_kernel.repository_url}:${var.deploy_branch}"
    application_container_name = "${var.aether_kernel_container_name}"
    nginx_container_name = "${var.aether_kernel_nginx_container_name}"
    host_port = "${var.aether_kernel_nginx_host_port}"
    nginx_image_url  = "${aws_ecr_repository.aether_kernel_nginx.repository_url}:latest"
    database_hostname = "${var.database_hostname}"
    database_password = "${data.credstash_secret.aether_kernel.value}"
    database_name = "${replace("${var.project}", "-", "_")}"
    database_user = "${replace("${var.project}", "-", "")}"
    database_port = "${var.database_port}"
    django_use_x_forwarded_port = "1"
    django_http_x_forwarded_proto = "1"
    django_use_x_forwarded_host = "1"
    domain = ".${var.domain}"
    sentry_dsn = "${data.credstash_secret.aether_kernel_sentry_dsn.value}"
    aws_key = "${data.credstash_secret.aws_key_kernel.value}"
    aws_secret_key = "${data.credstash_secret.aws_secret_key_kernel.value}"
  }
}

resource "aws_ecs_task_definition" "aether_kernel" {
  family                = "${var.project}-kernel-${var.environment}"
  container_definitions = "${data.template_file.aether_kernel.rendered}"

  volume {
    name = "static-kernel"
  }

  volume {
    host_path = "/data/upload-data"
    name = "upload-data"
  }
}

data "aws_ecs_task_definition" "aether_kernel" {
  task_definition = "${aws_ecs_task_definition.aether_kernel.family}"
}

resource "aws_ecs_service" "aether_kernel" {
  name            = "${var.project}-kernel"
  cluster         = "${aws_ecs_cluster.cluster.id}"
  task_definition = "${aws_ecs_task_definition.aether_kernel.family}:${max("${aws_ecs_task_definition.aether_kernel.revision}", "${data.aws_ecs_task_definition.aether_kernel.revision}")}"
  desired_count   = 1
  iam_role        = "${var.iam_role_id}"

  load_balancer {
    target_group_arn = "${aws_alb_target_group.aether_kernel.id}"
    container_name   = "kernel-nginx"
    container_port   = 80
  }
  depends_on = [
    "aws_alb_listener.aether_kernel_http"
  ]
}

output "kernel_target_group" {
  value = "${aws_alb_target_group.aether_kernel.arn}"
}
