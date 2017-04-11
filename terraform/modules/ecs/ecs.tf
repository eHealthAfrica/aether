resource "aws_ecs_cluster" "cluster" {
  name = "${var.project}-${var.environment}"
}
data "external" "current_task_def" {
  program = ["python", "${path.module}/files/find_task_def.py"]

  query = {
    family_prefix = "${var.project}-${var.environment}"
  }
}
