# Common
variable "cloud_provider" {
  description = "Which cloud to provision on: aws | gcp | azure | do"
  type        = string
  validation {
    condition     = contains(["aws", "gcp", "azure", "do"], var.cloud_provider)
    error_message = "cloud_provider must be one of: aws, gcp, azure, do."
  }
}

variable "vm_name" {
  description = "Name for the VM / resources"
  type        = string
  default     = "traffic-fingerprint-node"
}

variable "admin_username" {
  description = "Admin/SSH username for the VM"
  type        = string
  default     = "ubuntu"
}

variable "ssh_public_key_path" {
  description = "Path to your SSH public key (used by Azure)"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

# AWS
variable "aws_region" {
  type    = string
  default = "us-east-1"
}
variable "aws_instance_type" {
  type    = string
  default = "t3.small"
}
variable "aws_key_name" {
  description = "Name of an existing EC2 key pair"
  type        = string
  default     = ""
}

# GCP
variable "gcp_project" {
  type    = string
  default = ""
}
variable "gcp_region" {
  type    = string
  default = "us-central1"
}
variable "gcp_zone" {
  type    = string
  default = "us-central1-a"
}
variable "gcp_machine_type" {
  type    = string
  default = "e2-small"
}

# Azure
variable "azure_location" {
  type    = string
  default = "eastus"
}
variable "azure_vm_size" {
  type    = string
  default = "Standard_B1ms"
}

# DigitalOcean
variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  default     = ""
  sensitive   = true
}
variable "do_region" {
  type    = string
  default = "nyc3"
}
variable "do_size" {
  type    = string
  default = "s-1vcpu-2gb"
}
</content>
