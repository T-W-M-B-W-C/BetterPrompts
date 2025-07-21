# Outputs for RDS Module

output "instance_id" {
  description = "The RDS instance ID"
  value       = aws_db_instance.main.id
}

output "instance_arn" {
  description = "The ARN of the RDS instance"
  value       = aws_db_instance.main.arn
}

output "endpoint" {
  description = "The connection endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "address" {
  description = "The hostname of the RDS instance"
  value       = aws_db_instance.main.address
}

output "port" {
  description = "The database port"
  value       = aws_db_instance.main.port
}

output "database_name" {
  description = "The database name"
  value       = aws_db_instance.main.db_name
}

output "username" {
  description = "The master username for the database"
  value       = aws_db_instance.main.username
  sensitive   = true
}

output "security_group_id" {
  description = "The security group ID of the RDS instance"
  value       = aws_security_group.rds.id
}

output "parameter_group_id" {
  description = "The db parameter group id"
  value       = aws_db_parameter_group.postgres.id
}

output "subnet_group_id" {
  description = "The db subnet group id"
  value       = aws_db_subnet_group.main.id
}

output "read_replica_endpoints" {
  description = "The connection endpoints for read replicas"
  value       = [for replica in aws_db_instance.read_replica : replica.endpoint]
  sensitive   = true
}

output "kms_key_id" {
  description = "The KMS key ID used for encryption"
  value       = aws_kms_key.rds.id
}

output "kms_key_arn" {
  description = "The KMS key ARN used for encryption"
  value       = aws_kms_key.rds.arn
}

output "secret_arn" {
  description = "The ARN of the secret containing the RDS credentials"
  value       = aws_secretsmanager_secret.rds_credentials.arn
}

output "secret_name" {
  description = "The name of the secret containing the RDS credentials"
  value       = aws_secretsmanager_secret.rds_credentials.name
}