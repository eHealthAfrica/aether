### Security

resource "aws_security_group" "lb_sg" {
  description = "controls access to the application ALB"

  vpc_id = "${var.vpc_id}"
  name   = "${var.project}-${var.environment}_alb"

  ingress {
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol    = "tcp"
    from_port   = 443
    to_port     = 443
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"

    cidr_blocks = [
      "0.0.0.0/0",
    ]
  }

  tags {
    "Name" = "${var.project}-${var.environment}"
  }
}

resource "aws_security_group_rule" "gather2_ecs" {
  type = "ingress"
  protocol  = "tcp"
  from_port = "10000"
  to_port   = "50000"
  security_group_id =  "${var.internal_sg_id}"
  source_security_group_id = "${aws_security_group.lb_sg.id}"
}

resource "aws_security_group_rule" "gather2_efs" {
  type = "ingress"
  protocol  = "tcp"
  from_port = "2049"
  to_port   = "2049"
  security_group_id =  "${var.internal_sg_id}"
  source_security_group_id = "${var.internal_sg_id}"
}

resource "aws_security_group_rule" "bastion" {
  type = "ingress"
  protocol  = "tcp"
  from_port = 22
  to_port   = 22
  security_group_id =  "${var.internal_sg_id}"
  source_security_group_id = "${lookup(var.bastion_sg_id, var.environment)}"
}

resource "aws_security_group_rule" "rds" {
  type = "ingress"
  protocol  = "tcp"
  from_port = 5432
  to_port   = 5432
  security_group_id =  "${var.internal_sg_id}"
  source_security_group_id = "${var.internal_sg_id}"
}

