# Variables for EKS Module

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
}

variable "cluster_version" {
  description = "Kubernetes version to use for the EKS cluster"
  type        = string
  default     = "1.28"
}

variable "vpc_id" {
  description = "VPC ID where the cluster will be deployed"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs where the nodes will be deployed"
  type        = list(string)
}

variable "enable_irsa" {
  description = "Enable IAM Roles for Service Accounts"
  type        = bool
  default     = true
}

variable "openid_connect_audiences" {
  description = "List of audiences for the OpenID Connect identity provider"
  type        = list(string)
  default     = ["sts.amazonaws.com"]
}

variable "public_access_cidrs" {
  description = "List of CIDR blocks that can access the public API server endpoint"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# Node Group Configurations
variable "system_node_group_config" {
  description = "Configuration for system node group"
  type = object({
    instance_types = list(string)
    scaling_config = object({
      desired_size = number
      min_size     = number
      max_size     = number
    })
    labels = map(string)
  })
  default = {
    instance_types = ["t3a.medium"]
    scaling_config = {
      desired_size = 2
      min_size     = 2
      max_size     = 4
    }
    labels = {}
  }
}

variable "application_node_group_config" {
  description = "Configuration for application node group"
  type = object({
    instance_types = list(string)
    scaling_config = object({
      desired_size = number
      min_size     = number
      max_size     = number
    })
    labels = map(string)
  })
  default = {
    instance_types = ["c6i.xlarge"]
    scaling_config = {
      desired_size = 3
      min_size     = 3
      max_size     = 9
    }
    labels = {
      workload = "application"
    }
  }
}

variable "gpu_node_group_config" {
  description = "Configuration for GPU node group"
  type = object({
    instance_types = list(string)
    scaling_config = object({
      desired_size = number
      min_size     = number
      max_size     = number
    })
    labels = map(string)
    taints = list(object({
      key    = string
      value  = string
      effect = string
    }))
  })
  default = null
}

# Spot Instance Configuration
variable "enable_spot_instances" {
  description = "Enable spot instances for cost optimization"
  type        = bool
  default     = false
}

variable "spot_instance_pools" {
  description = "Number of spot instance pools to use"
  type        = number
  default     = 4
}

variable "spot_max_price" {
  description = "Maximum price for spot instances (empty string for on-demand price)"
  type        = string
  default     = ""
}

# EKS Add-on Versions
variable "addon_versions" {
  description = "Versions of EKS add-ons"
  type = object({
    vpc_cni        = string
    kube_proxy     = string
    coredns        = string
    ebs_csi_driver = string
  })
  default = {
    vpc_cni        = "v1.15.1-eksbuild.1"
    kube_proxy     = "v1.28.1-eksbuild.1"
    coredns        = "v1.10.1-eksbuild.2"
    ebs_csi_driver = "v1.23.0-eksbuild.1"
  }
}

# Add-on Features
variable "enable_cluster_autoscaler" {
  description = "Enable Cluster Autoscaler"
  type        = bool
  default     = true
}

variable "enable_metrics_server" {
  description = "Enable Metrics Server"
  type        = bool
  default     = true
}

variable "enable_aws_load_balancer_controller" {
  description = "Enable AWS Load Balancer Controller"
  type        = bool
  default     = true
}

variable "tags" {
  description = "A map of tags to add to all resources"
  type        = map(string)
  default     = {}
}