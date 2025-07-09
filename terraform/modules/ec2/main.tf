# EC2 instance provisioning along with inital setuo -> setuo_enviornment.sh
# The repo must be public for the script to be downloaded successfully.

resource "aws_instance" "devops_ai_agent" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = var.security_group_ids
  associate_public_ip_address = true
  user_data = <<-EOF
              #!/bin/bash
              curl -o /tmp/setup_environment.sh https://raw.githubusercontent.com/mnsh37/devops-ai-agent/main/scripts/bootstrap.sh 
              chmod +x /tmp/setup_environment.sh
              /tmp/setup_environment.sh
              EOF
  tags = var.tags
}
