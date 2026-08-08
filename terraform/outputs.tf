# Emits the public IP of whichever VM was created, so you can drop it into
# the Ansible inventory.

output "vm_public_ip" {
  description = "Public IP address of the provisioned VM"
  value = coalesce(
    try(aws_instance.vm[0].public_ip, ""),
    try(google_compute_instance.vm[0].network_interface[0].access_config[0].nat_ip, ""),
    try(azurerm_public_ip.pip[0].ip_address, ""),
    try(digitalocean_droplet.vm[0].ipv4_address, ""),
    "unknown",
  )
}

output "ansible_inventory_line" {
  description = "Ready-to-paste line for ansible/inventory.ini"
  value = format(
    "%s ansible_host=%s ansible_user=%s",
    var.vm_name,
    coalesce(
      try(aws_instance.vm[0].public_ip, ""),
      try(google_compute_instance.vm[0].network_interface[0].access_config[0].nat_ip, ""),
      try(azurerm_public_ip.pip[0].ip_address, ""),
      try(digitalocean_droplet.vm[0].ipv4_address, ""),
      "unknown",
    ),
    var.admin_username,
  )
}
