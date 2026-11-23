terraform {
  required_version = ">= 1.5.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

# host = null nutzt den Standard-Socket des Systems. Auf macOS mit Docker Desktop
# kann der Socket woanders liegen: dann docker_host in terraform.tfvars setzen.
provider "docker" {
  host = var.docker_host
}

resource "docker_image" "nginx" {
  name         = "nginx:alpine"
  keep_locally = true
}

resource "docker_container" "webserver" {
  name  = var.container_name
  image = docker_image.nginx.image_id

  ports {
    internal = 80
    external = var.host_port
  }

  # Eigene index.html statt der nginx-Standardseite (Bind-Mount, absoluter Pfad).
  volumes {
    host_path      = "${abspath(path.module)}/index.html"
    container_path = "/usr/share/nginx/html/index.html"
    read_only      = true
  }
}
