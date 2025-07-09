output "security_group_id" {
  description = "ID of the security group"
  value       = aws_security_group.devops_ai_agent_sg.id
}
