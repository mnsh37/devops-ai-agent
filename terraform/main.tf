# Assembles resources from modules and configures AWS provider for devops-ai-agent

provider "aws" {
  region = var.region
}
data "aws_vpc" "default" {
  default = true
}
module "ec2" {
  source             = "./modules/ec2"
  instance_type      = var.instance_type
  ami_id             = var.ami_id
  key_name           = var.key_name
  security_group_ids = [module.security_group.security_group_id]
  tags = {
    Name        = "DevOpsAIAgentInstance"
    Environment = "Development"
  }
}
module "security_group" {
  source             = "./modules/security_group"
  vpc_id             = data.aws_vpc.default.id
  ingress_cidr_blocks = var.ingress_cidr_blocks
  tags = {
    Name        = "DevOpsAIAgentSG"
    Environment = "Development"
  }
}
