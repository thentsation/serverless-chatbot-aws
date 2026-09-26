resource "aws_ecr_repository" "orchestrator" {
  name         = "${var.project_name}-orchestrator"
  force_delete = true
}

resource "null_resource" "docker_upload" {
  provisioner "local-exec" {
    command = "bash ${var.docker_script} ${aws_ecr_repository.orchestrator.repository_url} ${aws_ecr_repository.orchestrator.name} ${var.region}"
  }

  depends_on = [aws_ecr_repository.orchestrator]
}
