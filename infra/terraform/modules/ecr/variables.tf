variable "project_name" {
  description = "The name of the project."
  type        = string

}

variable "docker_script" {
  description = "Path to the Docker script."
  type        = string
}

variable "region" {
  description = "The AWS region to deploy resources in."
  type        = string

}