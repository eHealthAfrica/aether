// Gather2-data

// ECR repository
resource "aws_ecr_repository" "gather2_couchdb" {
  name = "${var.project}-couchdb-${var.environment}"
}

// ECR repository
resource "aws_ecr_repository" "gather2_couchdb_sync" {
  name = "${var.project}-couchdb-sync-${var.environment}"
}

// ECR repository
resource "aws_ecr_repository" "gather2_couchdb_sync_nginx" {
  name = "${var.project}-couchdb-sync-nginx-${var.environment}"
}

data "credstash_secret" "couchdb_password" {
  name = "${var.project}-${var.environment}-couchdb-password"
}

data "credstash_secret" "database_password" {
  name = "${var.project}-${var.environment}-database-password"
}

data "credstash_secret" "gather2_token" {
  name = "${var.project}-${var.environment}-token"
}

data "credstash_secret" "google_client_id" {
  name = "${var.project}-${var.environment}-google-client-id"
}

data "credstash_secret" "gather2_sync_sentry_dsn" {
  name = "${var.project}-${var.environment}-sentry-dsn"
}

data "credstash_secret" "aws_key_sync" {
  name = "ecs-secrets-${var.environment}-aws_key"
}

data "credstash_secret" "aws_secret_key_sync" {
  name = "ecs-secrets-${var.environment}-aws_secret_key"
}

data "template_file" "gather2_couchdb_sync" {
  template = "${file("${path.module}/files/gather2_couchdb_sync.json")}"

  vars {
    image_url = "${aws_ecr_repository.gather2_couchdb_sync.repository_url}:${var.deploy_branch}"
    nginx_image_url = "${aws_ecr_repository.gather2_couchdb_sync_nginx.repository_url}"
    couchdb_image_url = "${aws_ecr_repository.gather2_couchdb.repository_url}"
    couchdb_password = "${data.credstash_secret.database_password.value}"
    database_hostname = "${var.database_hostname}"
    database_name = "${replace("${var.project}", "-", "_")}"
    database_user = "${replace("${var.project}", "-", "")}"
    database_password = "${data.credstash_secret.gather2_core.value}"
    database_port = "${var.database_port}"
    django_use_x_forwarded_port = "1"
    django_http_x_forwarded_proto = "1"
    django_use_x_forwarded_host = "1"
    gather2_token = "${data.credstash_secret.gather2_token.value}"
    google_client_id = "${data.credstash_secret.google_client_id.value}"
    gather2_core_url = "${replace("https://core-gather-${var.environment}.ehealthafrica.org", "-prod", "")}"
    sentry_dsn = "${data.credstash_secret.gather2_sync_sentry_dsn.value}"
    domain = ".${var.domain}"
    aws_key = "${data.credstash_secret.aws_key_sync.value}"
    aws_secret_key = "${data.credstash_secret.aws_secret_key_sync.value}"
  }
}

resource "aws_alb" "gather2_couchdb_sync" {
  internal = false
  subnets = ["${var.public_subnets}"]
  security_groups = ["${aws_security_group.lb_sg.id}"]

  enable_deletion_protection = false

  tags {
    key = "stack"
    name =  "${var.project}-couchdb-sync-${var.environment}"
  }
}

resource "aws_route53_record" "gather2_couchdb_sync" {
  zone_id = "${lookup("${var.route53_zone_id}","${var.domain}")}"
  name    = "${replace("${var.couchdb_sync_url}-${var.environment}", "-prod", "")}"
  type    = "A"

  alias {
    name                   = "${aws_alb.gather2_couchdb_sync.dns_name}"
    zone_id                = "${aws_alb.gather2_couchdb_sync.zone_id}"
    evaluate_target_health = true
  }
}

resource "aws_alb_target_group" "gather2_couchdb_sync" {
  name     = "${var.project}-couchdb-sync-${var.environment}"
  port     = 80
  protocol = "HTTP"
  vpc_id   = "${var.vpc_id}"

  health_check {
    path = "/health"
  }
}

resource "aws_alb_listener" "gather2_couchdb_sync_http" {
  load_balancer_arn = "${aws_alb.gather2_couchdb_sync.id}"
  port              = "80"
  protocol          = "HTTP"

  default_action {
    target_group_arn = "${aws_alb_target_group.gather2_couchdb_sync.id}"
    type             = "forward"
  }
}

resource "aws_alb_listener" "gather2_couchdb_sync_https" {
  load_balancer_arn = "${aws_alb.gather2_couchdb_sync.id}"
  port = "443"
  protocol = "HTTPS"
  ssl_policy = "ELBSecurityPolicy-2015-05"
  certificate_arn =  "${lookup(var.ssl_certificate_id, var.domain)}"

  default_action {
    target_group_arn = "${aws_alb_target_group.gather2_couchdb_sync.arn}"
    type = "forward"
  }
}

resource "aws_ecs_task_definition" "gather2_couchdb_sync" {
  family  = "${var.project}-couchdb-sync-${var.environment}"
  container_definitions = "${data.template_file.gather2_couchdb_sync.rendered}"

  volume {
    name  = "redis-data"
    host_path = "/data/redis"
  }

  volume {
    name  = "couchdb-data"
    host_path = "/data/couchdb"
  }

  volume {
    name = "static-couchdb-sync"
  }
}

data "aws_ecs_task_definition" "gather2_couchdb_sync" {
  task_definition = "${aws_ecs_task_definition.gather2_couchdb_sync.family}"
}

resource "aws_ecs_service" "gather2_couchdb_sync" {
  name            = "${var.project}-couchdb-sync"
  cluster         = "${aws_ecs_cluster.cluster.id}"
  task_definition = "${aws_ecs_task_definition.gather2_couchdb_sync.family}:${max("${aws_ecs_task_definition.gather2_couchdb_sync.revision}", "${data.aws_ecs_task_definition.gather2_couchdb_sync.revision}")}"
  desired_count   = 1
  iam_role        = "${var.iam_role_id}"

  load_balancer {
    target_group_arn = "${aws_alb_target_group.gather2_couchdb_sync.id}"
    container_name   = "couchdb-sync-nginx"
    container_port = 80
  }

  depends_on = [
    "aws_alb_listener.gather2_couchdb_sync_http"
  ]
}

output "couchdb_sync_target_group" {
  value = "${aws_alb_target_group.gather2_couchdb_sync.arn}"
}
