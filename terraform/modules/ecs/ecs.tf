resource "aws_ecs_cluster" "cluster" {
  name = "${var.project}-${var.environment}"
}

resource "aws_route53_zone" "internal" {
  name = "${var.project}.${var.environment}"
  vpc_id = "${var.vpc_id}"

  tags {
    Environment = "${var.environment}"
  }
}
