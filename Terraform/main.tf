terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

resource "local_file" "first" {
  content  = "First file"
  filename = "${path.module}/first.txt"
}

resource "local_file" "second" {
  content  = "Second file, depends on first"
  filename = "${path.module}/second.txt"
  depends_on = [local_file.first]
}

variable "file_content" {
  description = "Content for the hello.txt file"
  type        = string
  default     = "Hello from a variable!"
}

resource "local_file" "variable_example" {
  content  = var.file_content
  filename = "${path.module}/variable_hello.txt"
}
resource "local_file" "another_example" {
  content  = "This is another  file content"
  filename = "${path.module}/another_hello.txt"
}

module "my_file" {
  source   = ".//modules/file_writer"
  filename = "${path.module}/module_file.txt"
  content  = "Created by a module!"
}

output "module_file_path" {
  value = module.my_file.written_file
}