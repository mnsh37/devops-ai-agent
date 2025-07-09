# This file defines the variables for the security group module in Terraform.
# It includes variables for VPC ID, ingress CIDR blocks, and tags.

variable "vpc_id" {
  description = "VPC ID for the security group"
  type        = string
}
variable "ingress_cidr_blocks" {
  description = "CIDR blocks for security group ingress rules"
  type        = list(string)
}
variable "tags" {
  description = "Tags to apply to the security group"
  type        = map(string)
  default     = {}
}
