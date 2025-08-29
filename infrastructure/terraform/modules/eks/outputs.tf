# Outputs for EKS Module

output "cluster_id" {
  description = "The ID/name of the EKS cluster"
  value       = aws_eks_cluster.main.id
}

output "cluster_name" {
  description = "The name of the EKS cluster"
  value       = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = aws_security_group.cluster_security_group.id
}

output "cluster_ca_certificate" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = aws_eks_cluster.main.certificate_authority[0].data
}

output "cluster_version" {
  description = "The Kubernetes version for the cluster"
  value       = aws_eks_cluster.main.version
}

output "oidc_provider" {
  description = "The OpenID Connect identity provider (OIDC provider)"
  value       = try(aws_iam_openid_connect_provider.cluster[0].arn, null)
}

output "oidc_issuer_url" {
  description = "The URL on the EKS cluster OIDC Issuer"
  value       = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

output "cluster_primary_security_group_id" {
  description = "The cluster primary security group ID created by EKS"
  value       = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
}

output "node_security_group_id" {
  description = "Security group ID attached to the EKS nodes"
  value       = aws_security_group.cluster_security_group.id
}

output "cluster_iam_role_arn" {
  description = "IAM role ARN of the EKS cluster"
  value       = aws_iam_role.cluster.arn
}

output "node_group_iam_role_arn" {
  description = "IAM role ARN of the EKS node groups"
  value       = aws_iam_role.node_group.arn
}

output "system_node_group_id" {
  description = "The ID of the system node group"
  value       = aws_eks_node_group.system.id
}

output "application_node_group_id" {
  description = "The ID of the application node group"
  value       = aws_eks_node_group.application.id
}

output "gpu_node_group_id" {
  description = "The ID of the GPU node group"
  value       = try(aws_eks_node_group.gpu[0].id, null)
}

output "spot_asg_name" {
  description = "The name of the spot instance Auto Scaling Group"
  value       = try(aws_autoscaling_group.spot[0].name, null)
}