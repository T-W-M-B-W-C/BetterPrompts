# Variables for RDS Module

variable "identifier" {
  description = "The name of the RDS instance"
  type        = string
}

variable "engine" {
  description = "The database engine"
  type        = string
  default     = "postgres"
}

variable "engine_version" {
  description = "The engine version to use"
  type        = string
  default     = "16.1"
}

variable "instance_class" {
  description = "The instance type of the RDS instance"
  type        = string
}

variable "allocated_storage" {
  description = "The allocated storage in gigabytes"
  type        = number
}

variable "max_allocated_storage" {
  description = "The upper limit to which Amazon RDS can automatically scale the storage"
  type        = number
  default     = 0
}

variable "storage_type" {
  description = "One of standard (magnetic), gp2 (general purpose SSD), gp3 (general purpose SSD), or io1 (provisioned IOPS SSD)"
  type        = string
  default     = "gp3"
}

variable "storage_throughput" {
  description = "The storage throughput value for the DB instance (only for gp3)"
  type        = number
  default     = 125
}

variable "storage_iops" {
  description = "The amount of provisioned IOPS (only for gp3 and io1)"
  type        = number
  default     = 3000
}

variable "database_name" {
  description = "The name of the database to create when the DB instance is created"
  type        = string
  default     = null
}

variable "username" {
  description = "Username for the master DB user"
  type        = string
}

variable "password" {
  description = "Password for the master DB user. If not specified, a random password will be generated"
  type        = string
  default     = ""
  sensitive   = true
}

variable "port" {
  description = "The port on which the DB accepts connections"
  type        = number
  default     = 5432
}

variable "vpc_id" {
  description = "VPC ID for the DB subnet group and security group"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for the DB subnet group"
  type        = list(string)
}

variable "allowed_security_groups" {
  description = "List of security group IDs allowed to connect to the RDS instance"
  type        = list(string)
  default     = []
}

variable "multi_az" {
  description = "Specifies if the RDS instance is multi-AZ"
  type        = bool
  default     = false
}

variable "availability_zone" {
  description = "The AZ for the RDS instance"
  type        = string
  default     = null
}

variable "backup_retention_days" {
  description = "The days to retain backups for"
  type        = number
  default     = 7
}

variable "backup_window" {
  description = "The daily time range during which automated backups are created"
  type        = string
  default     = "03:00-04:00"
}

variable "maintenance_window" {
  description = "The window to perform maintenance in"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

variable "deletion_protection" {
  description = "If the DB instance should have deletion protection enabled"
  type        = bool
  default     = false
}

variable "performance_insights_enabled" {
  description = "Specifies whether Performance Insights are enabled"
  type        = bool
  default     = false
}

variable "enhanced_monitoring_interval" {
  description = "The interval, in seconds, between points when Enhanced Monitoring metrics are collected"
  type        = number
  default     = 0
}

variable "enabled_cloudwatch_logs_exports" {
  description = "List of log types to enable for exporting to CloudWatch logs"
  type        = list(string)
  default     = []
}

variable "enabled_extensions" {
  description = "List of PostgreSQL extensions to enable"
  type        = list(string)
  default     = []
}

variable "create_read_replica" {
  description = "Whether to create read replicas"
  type        = bool
  default     = false
}

variable "read_replica_count" {
  description = "Number of read replicas to create"
  type        = number
  default     = 0
}

variable "read_replica_instance_class" {
  description = "The instance type of the read replica instances"
  type        = string
  default     = ""
}

variable "alarm_cpu_threshold" {
  description = "The CPU utilization threshold for alarms"
  type        = number
  default     = 75
}

variable "alarm_free_storage_threshold" {
  description = "The free storage space threshold for alarms (in bytes)"
  type        = number
  default     = 10737418240 # 10GB
}

variable "alarm_sns_topic_arn" {
  description = "The ARN of the SNS topic for alarm notifications"
  type        = string
  default     = ""
}

variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default     = {}
}