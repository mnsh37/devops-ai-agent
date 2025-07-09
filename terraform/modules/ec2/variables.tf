# Variables for EC2 module
# This file defines the variables for the EC2 module in Terraform.
# It includes variables for instance type, AMI ID, key name, security group IDs, and tags.

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}
variable "ami_id" {
  description = "AMI ID for the EC2 instance"
  type        = string
}
variable "key_name" {
  description = "SSH key pair name for EC2 access"
  type        = string
}
variable "security_group_ids" {
  description = "List of security group IDs to attach to the EC2 instance"
  type    = list(string)
}
variable "tags" {
  description = "Tags to apply to the EC2 instance"
  type        = map(string)
  default     = {}
}