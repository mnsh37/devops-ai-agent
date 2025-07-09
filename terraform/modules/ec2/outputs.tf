output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.devops_ai_agent.id
}
output "public_ip" {
  description = "Public IP of the EC2 instance"
  value       = aws_instance.devops_ai_agent.public_ip
}