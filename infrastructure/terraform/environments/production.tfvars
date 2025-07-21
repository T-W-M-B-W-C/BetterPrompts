# Production Environment Configuration

environment = "production"
aws_region  = "us-east-1"

# Contact Information
owner_email = "platform-team@betterprompts.ai"
alarm_email = "production-alerts@betterprompts.ai"

# VPC Configuration
vpc_cidr         = "10.2.0.0/16"
public_subnets   = ["10.2.1.0/24", "10.2.2.0/24", "10.2.3.0/24"]
private_subnets  = ["10.2.11.0/24", "10.2.12.0/24", "10.2.13.0/24"]
database_subnets = ["10.2.21.0/24", "10.2.22.0/24", "10.2.23.0/24"]
ml_subnets       = ["10.2.31.0/24", "10.2.32.0/24", "10.2.33.0/24"]

# EKS Configuration
eks_cluster_version = "1.28"

# Production-grade instances
system_node_group_config = {
  instance_types = ["t3a.medium"]
  scaling_config = {
    desired_size = 2
    min_size     = 2
    max_size     = 4
  }
  labels = {}
}

application_node_group_config = {
  instance_types = ["c6i.xlarge", "c6a.xlarge", "c5.xlarge"]
  scaling_config = {
    desired_size = 3
    min_size     = 3
    max_size     = 9
  }
  labels = {
    workload = "application"
  }
}

# GPU nodes for production ML workloads
gpu_node_group_config = {
  instance_types = ["g4dn.xlarge"]
  scaling_config = {
    desired_size = 1
    min_size     = 1
    max_size     = 5
  }
  labels = {
    workload = "ml"
    gpu      = "true"
  }
  taints = [{
    key    = "nvidia.com/gpu"
    value  = "true"
    effect = "NO_SCHEDULE"
  }]
}

# Enable spot instances for non-critical workloads
enable_spot_instances = true
spot_instance_pools   = 6
spot_max_price        = "0.5"

# RDS Configuration - Production instance with Multi-AZ
rds_instance_class        = "db.r6g.xlarge"
rds_allocated_storage     = 500
rds_max_allocated_storage = 2000

# ElastiCache Configuration - Production cluster
elasticache_node_type = "cache.r6g.large"

# Cost Controls
monthly_budget_usd = 5000

# Enable all monitoring and security features in production
enable_flow_logs              = true
performance_insights_enabled  = true
enhanced_monitoring_interval  = 60
deletion_protection          = true

# SSL Certificate ARN for production domain
# acm_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"