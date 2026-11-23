variable "container_name" {
  type        = string
  description = "Name des nginx-Containers."
  default     = "expense-manager-web"
}

variable "host_port" {
  type        = number
  description = "Host-Port, der auf den Container-Port 80 abgebildet wird."
  default     = 8080

  validation {
    condition     = var.host_port > 1024 && var.host_port <= 65535
    error_message = "host_port muss ein unprivilegierter Port zwischen 1025 und 65535 sein."
  }
}

variable "docker_host" {
  type        = string
  description = "Docker-Socket (z. B. unix:///Users/<name>/.docker/run/docker.sock). null = Standard des Systems."
  default     = null
}
