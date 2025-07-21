# Staging Environment Configuration

environment = "staging"
aws_region  = "us-east-1"

# Contact Information
owner_email = "platform-team@betterprompts.ai"
alarm_email = "staging-alerts@betterprompts.ai"

# VPC Configuration
vpc_cidr         = "10.1.0.0/16"
public_subnets   = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
private_subnets  = ["10.1.11.0/24", "10.1.12.0/24", "10.1.13.0/24"]
database_subnets = ["10.1.21.0/24", "10.1.22.0/24", "10.1.23.0/24"]
ml_subnets       = ["10.1.31.0/24", "10.1.32.0/24", "10.1.33.0/24"]

# EKS Configuration
eks_cluster_version = "1.28"

# Mid-sized instances for staging
system_node_group_config = {
  instance_types = ["t3a.medium"]
  scaling_config = {
    desired_size = 2
    min_size     = 2
    max_size     = 3
  }
  labels = {}
}

application_node_group_config = {
  instance_types = ["t3a.large", "t3.large", "c5a.large"]
  scaling_config = {
    desired_size = 3
    min_size     = 2
    max_size     = 5
  }
  labels = {
    workload = "application"
  }
}

# Limited GPU nodes for staging ML testing
gpu_node_group_config = {
  instance_types = ["g4dn.xlarge"]
  scaling_config = {
    desired_size = 1
    min_size     = 0
    max_size     = 2
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

# Enable spot instances for cost savings
enable_spot_instances = true
spot_instance_pools   = 4

# RDS Configuration - Mid-sized instance for staging
rds_instance_class        = "db.r6g.large"
rds_allocated_storage     = 200
rds_max_allocated_storage = 500

# ElastiCache Configuration - Mid-sized instance for staging
elasticache_node_type = "cache.r6g.medium"

# Cost Controls
monthly_budget_usd = 2500

# Enable some monitoring features in staging
enable_flow_logs              = true
performance_insights_enabled  = true
enhanced_monitoring_interval  = 60