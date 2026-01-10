variable "filename" { type = string }
variable "content" { type = string }

resource "local_file" "mod_file" {
  content  = var.content
  filename = var.filename
}

output "written_file" {
  value = local_file.mod_file.filename
}