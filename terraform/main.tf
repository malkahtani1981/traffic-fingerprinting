# Multi-cloud VM provisioning for the traffic-fingerprinting suite.
#
# Pick ONE provider by setting `cloud_provider` and its matching variables, then:
#   terraform init
#   terraform apply -var="cloud_provider=aws"
#
# Each provider block is gated by `count` so only the selected cloud is created.

terraform {
  required_version = ">= 1.3.0"
  required_providers {
    aws          = { source = "hashicorp/aws", version = "~> 5.0" }
    google       = { source = "hashicorp/google", version = "~> 5.0" }
    azurerm      = { source = "hashicorp/azurerm", version = "~> 3.0" }
    digitalocean = { source = "digitalocean/digitalocean", version = "~> 2.0" }
  }
}

# ---------------------------------------------------------------------------
# AWS EC2
# ---------------------------------------------------------------------------
provider "aws" {
  region = var.aws_region
}

data "aws_ami" "ubuntu" {
  count       = var.cloud_provider == "aws" ? 1 : 0
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

resource "aws_instance" "vm" {
  count         = var.cloud_provider == "aws" ? 1 : 0
  ami           = data.aws_ami.ubuntu[0].id
  instance_type = var.aws_instance_type
  key_name      = var.aws_key_name

  tags = {
    Name = var.vm_name
  }
}

# ---------------------------------------------------------------------------
# Google Cloud Compute Engine
# ---------------------------------------------------------------------------
provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
  zone    = var.gcp_zone
}

resource "google_compute_instance" "vm" {
  count        = var.cloud_provider == "gcp" ? 1 : 0
  name         = var.vm_name
  machine_type = var.gcp_machine_type
  zone         = var.gcp_zone

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
    }
  }

  network_interface {
    network = "default"
    access_config {} # ephemeral public IP
  }
}

# ---------------------------------------------------------------------------
# Microsoft Azure
# ---------------------------------------------------------------------------
provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
  count    = var.cloud_provider == "azure" ? 1 : 0
  name     = "${var.vm_name}-rg"
  location = var.azure_location
}

resource "azurerm_virtual_network" "vnet" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${var.vm_name}-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.rg[0].location
  resource_group_name = azurerm_resource_group.rg[0].name
}

resource "azurerm_subnet" "subnet" {
  count                = var.cloud_provider == "azure" ? 1 : 0
  name                 = "${var.vm_name}-subnet"
  resource_group_name  = azurerm_resource_group.rg[0].name
  virtual_network_name = azurerm_virtual_network.vnet[0].name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_public_ip" "pip" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${var.vm_name}-pip"
  location            = azurerm_resource_group.rg[0].location
  resource_group_name = azurerm_resource_group.rg[0].name
  allocation_method   = "Static"
}

resource "azurerm_network_interface" "nic" {
  count               = var.cloud_provider == "azure" ? 1 : 0
  name                = "${var.vm_name}-nic"
  location            = azurerm_resource_group.rg[0].location
  resource_group_name = azurerm_resource_group.rg[0].name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.subnet[0].id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.pip[0].id
  }
}

resource "azurerm_linux_virtual_machine" "vm" {
  count                 = var.cloud_provider == "azure" ? 1 : 0
  name                  = var.vm_name
  resource_group_name   = azurerm_resource_group.rg[0].name
  location              = azurerm_resource_group.rg[0].location
  size                  = var.azure_vm_size
  admin_username        = var.admin_username
  network_interface_ids = [azurerm_network_interface.nic[0].id]

  admin_ssh_key {
    username   = var.admin_username
    public_key = file(var.ssh_public_key_path)
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts"
    version   = "latest"
  }
}

# ---------------------------------------------------------------------------
# DigitalOcean Droplet
# ---------------------------------------------------------------------------
provider "digitalocean" {
  token = var.do_token
}

resource "digitalocean_droplet" "vm" {
  count  = var.cloud_provider == "do" ? 1 : 0
  name   = var.vm_name
  region = var.do_region
  size   = var.do_size
  image  = "ubuntu-22-04-x64"
}
</content>
