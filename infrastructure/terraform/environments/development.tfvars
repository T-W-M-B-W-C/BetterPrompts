# Development Environment Configuration

environment = "development"
aws_region  = "us-east-1"

# Contact Information
owner_email = "dev-team@betterprompts.ai"
alarm_email = "dev-alerts@betterprompts.ai"

# VPC Configuration
vpc_cidr         = "10.0.0.0/16"
public_subnets   = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
private_subnets  = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]
database_subnets = ["10.0.21.0/24", "10.0.22.0/24", "10.0.23.0/24"]
ml_subnets       = ["10.0.31.0/24", "10.0.32.0/24", "10.0.33.0/24"]

# EKS Configuration
eks_cluster_version = "1.28"

# Cost-optimized smaller instances for development
system_node_group_config = {
  instance_types = ["t3a.small"]
  scaling_config = {
    desired_size = 1
    min_size     = 1
    max_size     = 2
  }
  labels = {}
}

application_node_group_config = {
  instance_types = ["t3a.medium", "t3.medium"]
  scaling_config = {
    desired_size = 2
    min_size     = 1
    max_size     = 3
  }
  labels = {
    workload = "application"
  }
}

# No GPU nodes in development to save costs
gpu_node_group_config = null

# Enable spot instances for additional cost savings
enable_spot_instances = true
spot_instance_pools   = 4

# RDS Configuration - Smaller instance for dev
rds_instance_class        = "db.t4g.medium"
rds_allocated_storage     = 100
rds_max_allocated_storage = 200

# ElastiCache Configuration - Smaller instance for dev
elasticache_node_type = "cache.t4g.micro"

# Cost Controls
monthly_budget_usd = 1000

# Disable some features in dev to save costs
enable_flow_logs              = false
performance_insights_enabled  = false
enhanced_monitoring_interval  = 0