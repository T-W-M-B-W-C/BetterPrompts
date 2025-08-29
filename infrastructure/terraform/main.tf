# BetterPrompts AWS Infrastructure - Main Configuration
# This is the root module that orchestrates all infrastructure components

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }
  
  # S3 backend for state management
  backend "s3" {
    bucket         = "betterprompts-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "betterprompts-terraform-locks"
  }
}

# Provider configurations
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = local.common_tags
  }
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_ca_certificate)
  token                  = data.aws_eks_cluster_auth.main.token
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_ca_certificate)
    token                  = data.aws_eks_cluster_auth.main.token
  }
}

# Data sources
data "aws_eks_cluster_auth" "main" {
  name = module.eks.cluster_name
}

data "aws_availability_zones" "available" {
  state = "available"
}

# Local variables
locals {
  name        = "betterprompts"
  environment = var.environment
  
  common_tags = {
    Project     = "BetterPrompts"
    Environment = var.environment
    ManagedBy   = "Terraform"
    CostCenter  = var.cost_center
    Owner       = var.owner_email
  }
  
  azs = slice(data.aws_availability_zones.available.names, 0, 3)
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"
  
  name               = "${local.name}-${local.environment}"
  cidr               = var.vpc_cidr
  availability_zones = local.azs
  
  # Subnet configuration
  public_subnets    = var.public_subnets
  private_subnets   = var.private_subnets
  database_subnets  = var.database_subnets
  ml_subnets        = var.ml_subnets
  
  # NAT Gateway configuration (cost optimization)
  enable_nat_gateway     = true
  single_nat_gateway     = var.environment != "production"
  one_nat_gateway_per_az = var.environment == "production"
  
  # VPC endpoints for cost optimization
  enable_s3_endpoint      = true
  enable_dynamodb_endpoint = true
  
  tags = local.common_tags
}

# EKS Module
module "eks" {
  source = "./modules/eks"
  
  cluster_name    = "${local.name}-${local.environment}"
  cluster_version = var.eks_cluster_version
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
  
  # IRSA (IAM Roles for Service Accounts)
  enable_irsa = true
  
  # OIDC Provider
  openid_connect_audiences = ["sts.amazonaws.com"]
  
  # Cluster addons
  enable_cluster_autoscaler = true
  enable_metrics_server     = true
  enable_aws_load_balancer_controller = true
  
  # Node groups configuration
  system_node_group_config = {
    instance_types = ["t3a.medium"]
    scaling_config = {
      desired_size = 2
      min_size     = 2
      max_size     = 4
    }
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
  
  # Spot instances for cost optimization
  enable_spot_instances = true
  spot_instance_pools   = 4
  spot_max_price        = "0.5"
  
  tags = local.common_tags
}

# RDS Module (PostgreSQL with pgvector)
module "rds" {
  source = "./modules/rds"
  
  identifier = "${local.name}-${local.environment}"
  
  # Engine configuration
  engine         = "postgres"
  engine_version = "16.1"
  
  # Instance configuration
  instance_class               = var.rds_instance_class
  allocated_storage           = var.rds_allocated_storage
  max_allocated_storage       = var.rds_max_allocated_storage
  storage_type                = "gp3"
  storage_throughput          = 125
  storage_iops                = 3000
  
  # Database configuration
  database_name = "betterprompts"
  username      = "betterprompts_admin"
  port          = 5432
  
  # pgvector extension
  enabled_extensions = ["pgvector", "pg_stat_statements"]
  
  # Network configuration
  vpc_id                  = module.vpc.vpc_id
  subnet_ids              = module.vpc.database_subnet_ids
  allowed_security_groups = [module.eks.node_security_group_id]
  
  # High availability
  multi_az               = var.environment == "production"
  backup_retention_days  = var.environment == "production" ? 7 : 1
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  # Performance insights
  performance_insights_enabled = var.environment == "production"
  
  # Monitoring
  enabled_cloudwatch_logs_exports = ["postgresql"]
  
  # Read replicas
  create_read_replica = var.environment == "production"
  read_replica_count  = var.environment == "production" ? 1 : 0
  
  tags = local.common_tags
}

# ElastiCache Module (Redis)
module "elasticache" {
  source = "./modules/elasticache"
  
  name = "${local.name}-${local.environment}"
  
  # Engine configuration
  engine_version = "7.0"
  node_type      = var.elasticache_node_type
  
  # Cluster configuration
  cluster_mode_enabled     = true
  num_shards              = 3
  replicas_per_shard      = var.environment == "production" ? 1 : 0
  
  # Network configuration
  vpc_id                  = module.vpc.vpc_id
  subnet_ids              = module.vpc.database_subnet_ids
  allowed_security_groups = [module.eks.node_security_group_id]
  
  # Performance configuration
  parameter_group_family = "redis7"
  parameters = {
    maxmemory-policy = "allkeys-lru"
  }
  
  # Maintenance
  maintenance_window = "sun:05:00-sun:06:00"
  
  # Backup
  snapshot_retention_limit = var.environment == "production" ? 3 : 0
  snapshot_window         = "03:00-04:00"
  
  tags = local.common_tags
}

# S3 Module
module "s3" {
  source = "./modules/s3"
  
  environment = local.environment
  
  # Bucket configurations
  buckets = {
    models = {
      name               = "${local.name}-models-${local.environment}"
      versioning_enabled = true
      lifecycle_rules = [{
        id      = "archive-old-models"
        enabled = true
        transitions = [{
          days          = 30
          storage_class = "STANDARD_IA"
        }, {
          days          = 90
          storage_class = "GLACIER"
        }]
      }]
    }
    assets = {
      name               = "${local.name}-assets-${local.environment}"
      versioning_enabled = false
      cloudfront_enabled = true
    }
    backups = {
      name               = "${local.name}-backups-${local.environment}"
      versioning_enabled = true
      lifecycle_rules = [{
        id      = "delete-old-backups"
        enabled = true
        expiration = {
          days = 90
        }
      }]
    }
    logs = {
      name               = "${local.name}-logs-${local.environment}"
      versioning_enabled = false
      lifecycle_rules = [{
        id      = "archive-logs"
        enabled = true
        transitions = [{
          days          = 7
          storage_class = "STANDARD_IA"
        }, {
          days          = 30
          storage_class = "GLACIER"
        }]
        expiration = {
          days = 180
        }
      }]
    }
  }
  
  # Intelligent tiering for cost optimization
  enable_intelligent_tiering = true
  
  tags = local.common_tags
}

# IAM Module
module "iam" {
  source = "./modules/iam"
  
  environment    = local.environment
  eks_cluster_id = module.eks.cluster_id
  oidc_provider  = module.eks.oidc_provider
  
  # Service account configurations
  service_accounts = {
    cluster_autoscaler = {
      namespace = "kube-system"
      policy_arns = [
        "arn:aws:iam::aws:policy/AutoScalingFullAccess"
      ]
    }
    aws_load_balancer_controller = {
      namespace = "kube-system"
      policy_arns = [
        module.iam.aws_load_balancer_controller_policy_arn
      ]
    }
    external_dns = {
      namespace = "kube-system"
      policy_arns = [
        module.iam.external_dns_policy_arn
      ]
    }
    cert_manager = {
      namespace = "cert-manager"
      policy_arns = [
        module.iam.cert_manager_policy_arn
      ]
    }
    application_pods = {
      namespace = "default"
      policy_arns = [
        module.iam.application_policy_arn
      ]
    }
  }
  
  tags = local.common_tags
}

# Monitoring Module
module "monitoring" {
  source = "./modules/monitoring"
  
  environment       = local.environment
  cluster_name      = module.eks.cluster_name
  rds_instance_id   = module.rds.instance_id
  redis_cluster_id  = module.elasticache.cluster_id
  
  # Alarm configurations
  enable_alarms = true
  alarm_email   = var.alarm_email
  
  # Metrics to monitor
  metrics_config = {
    api_response_time_threshold = 200  # ms
    error_rate_threshold        = 1    # percentage
    cpu_threshold              = 80    # percentage
    memory_threshold           = 85    # percentage
    rds_cpu_threshold          = 75    # percentage
    redis_memory_threshold     = 90    # percentage
  }
  
  # Cost monitoring
  enable_cost_alerts = true
  monthly_budget     = var.monthly_budget_usd
  
  # Log retention
  log_retention_days = var.environment == "production" ? 30 : 7
  
  tags = local.common_tags
}

# Cost Optimization Module
module "cost_optimization" {
  source = "./modules/cost-optimization"
  
  environment = local.environment
  
  # Savings Plans
  enable_compute_savings_plan = var.environment == "production"
  savings_plan_term          = "ONE_YEAR"
  savings_plan_payment_option = "ALL_UPFRONT"
  
  # Reserved Instances
  rds_reserved_instances = var.environment == "production" ? {
    instance_count = 1
    instance_class = var.rds_instance_class
    term          = "ONE_YEAR"
    payment_option = "ALL_UPFRONT"
  } : null
  
  elasticache_reserved_nodes = var.environment == "production" ? {
    node_count     = 3
    node_type      = var.elasticache_node_type
    term          = "ONE_YEAR"
    payment_option = "ALL_UPFRONT"
  } : null
  
  # Auto-shutdown for non-production
  enable_auto_shutdown = var.environment != "production"
  shutdown_schedule    = "0 20 * * 1-5"  # 8 PM weekdays
  startup_schedule     = "0 8 * * 1-5"   # 8 AM weekdays
  
  tags = local.common_tags
}

# Application Load Balancer
module "alb" {
  source = "./modules/alb"
  
  name               = "${local.name}-${local.environment}"
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.public_subnet_ids
  
  # SSL configuration
  certificate_arn = var.acm_certificate_arn
  ssl_policy      = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  
  # Target groups will be managed by AWS Load Balancer Controller
  
  # WAF
  enable_waf = var.environment == "production"
  
  tags = local.common_tags
}

# Outputs
output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}

output "eks_cluster_name" {
  description = "The name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "rds_endpoint" {
  description = "The connection endpoint for the RDS instance"
  value       = module.rds.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "The connection endpoint for the Redis cluster"
  value       = module.elasticache.configuration_endpoint
  sensitive   = true
}

output "s3_bucket_names" {
  description = "The names of the S3 buckets"
  value       = module.s3.bucket_names
}

output "alb_dns_name" {
  description = "The DNS name of the Application Load Balancer"
  value       = module.alb.dns_name
}

output "monitoring_dashboard_url" {
  description = "URL to the CloudWatch dashboard"
  value       = module.monitoring.dashboard_url
}