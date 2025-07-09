# Terraform variables for DevOps AI Agent deployment
# This file defines the variables used in the Terraform configuration for deploying the DevOps AI Agent.


variable "region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

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

variable "ingress_cidr_blocks" {
  description = "CIDR blocks for security group ingress rules"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}