# AWS Migration Validation Checklist

## 🎯 Overview

This checklist ensures all components of the BetterPrompts AWS migration are properly validated before, during, and after the migration. Each item includes verification steps and success criteria.

## 📋 Pre-Migration Validation

### Infrastructure Readiness

#### AWS Account Setup
- [ ] **AWS Organization configured**
  ```bash
  aws organizations describe-organization
  # Success: Organization details returned
  ```

- [ ] **Separate accounts for dev/staging/prod**
  ```bash
  aws organizations list-accounts
  # Success: 3+ accounts listed (dev, staging, prod)
  ```

- [ ] **IAM roles and policies created**
  ```bash
  aws iam list-roles | grep betterprompts
  # Success: All required roles present
  ```

- [ ] **Cost allocation tags configured**
  ```bash
  aws ce list-cost-category-definitions
  # Success: Project, Environment, Owner tags defined
  ```

### Terraform Infrastructure

- [ ] **State backend initialized**
  ```bash
  aws s3 ls s3://betterprompts-terraform-state/
  aws dynamodb describe-table --table-name betterprompts-terraform-locks
  # Success: Both resources exist and are accessible
  ```

- [ ] **Terraform plan executes without errors**
  ```bash
  cd infrastructure/terraform
  terraform init
  terraform plan -var-file=environments/development.tfvars
  # Success: Plan completes with expected resource count
  ```

### Team Readiness

- [ ] **AWS training completed**
  - Team members can navigate AWS Console
  - Understanding of EKS, RDS, and other services
  - Terraform knowledge demonstrated

- [ ] **Runbooks prepared**
  - Deployment procedures documented
  - Rollback procedures tested
  - Emergency contacts listed

## 🏗️ Infrastructure Validation

### Network Layer

- [ ] **VPC created with correct CIDR**
  ```bash
  aws ec2 describe-vpcs --filters "Name=tag:Project,Values=BetterPrompts"
  # Success: VPC with 10.0.0.0/16 (or configured CIDR)
  ```

- [ ] **Subnets in multiple AZs**
  ```bash
  aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-xxx"
  # Success: 12 subnets across 3 AZs (public, private, database, ML)
  ```

- [ ] **NAT Gateways operational**
  ```bash
  aws ec2 describe-nat-gateways --filter "Name=state,Values=available"
  # Success: 1-3 NAT Gateways based on environment
  ```

- [ ] **VPC Endpoints created**
  ```bash
  aws ec2 describe-vpc-endpoints
  # Success: S3 and DynamoDB endpoints present
  ```

### Compute Layer (EKS)

- [ ] **EKS cluster running**
  ```bash
  aws eks describe-cluster --name betterprompts-${ENVIRONMENT}
  # Success: Status = ACTIVE
  ```

- [ ] **kubectl configured**
  ```bash
  kubectl cluster-info
  kubectl get nodes
  # Success: Cluster accessible, nodes ready
  ```

- [ ] **Node groups healthy**
  ```bash
  kubectl get nodes -L node_group
  # Success: System (2+), Application (3+), GPU (1+) nodes
  ```

- [ ] **Spot instances running**
  ```bash
  kubectl get nodes -L node.kubernetes.io/lifecycle
  # Success: Some nodes labeled as "spot"
  ```

### Data Layer

- [ ] **RDS PostgreSQL accessible**
  ```bash
  aws rds describe-db-instances --db-instance-identifier betterprompts-${ENVIRONMENT}
  # Success: Status = available, Engine = postgres 16.x
  ```

- [ ] **pgvector extension enabled**
  ```sql
  psql -h ${RDS_ENDPOINT} -U admin -d betterprompts -c "\dx"
  # Success: vector extension listed
  ```

- [ ] **ElastiCache Redis running**
  ```bash
  aws elasticache describe-cache-clusters
  # Success: Cluster status = available
  ```

- [ ] **Redis connectivity verified**
  ```bash
  redis-cli -h ${REDIS_ENDPOINT} ping
  # Success: PONG response
  ```

### Storage Layer

- [ ] **S3 buckets created**
  ```bash
  aws s3 ls | grep betterprompts
  # Success: models, assets, backups, logs buckets exist
  ```

- [ ] **Bucket policies configured**
  ```bash
  aws s3api get-bucket-policy --bucket betterprompts-models-${ENVIRONMENT}
  # Success: Policy exists with proper permissions
  ```

- [ ] **Lifecycle policies active**
  ```bash
  aws s3api get-bucket-lifecycle-configuration --bucket betterprompts-logs-${ENVIRONMENT}
  # Success: Rules for archival/deletion configured
  ```

## 🚀 Application Validation

### Container Registry

- [ ] **ECR repositories created**
  ```bash
  aws ecr describe-repositories | grep betterprompts
  # Success: All service repositories present
  ```

- [ ] **Images pushed successfully**
  ```bash
  aws ecr list-images --repository-name betterprompts/frontend
  # Success: Latest images available
  ```

### Kubernetes Deployments

- [ ] **All pods running**
  ```bash
  kubectl get pods -A | grep -v Running | grep -v Completed
  # Success: No pods in error states
  ```

- [ ] **Services exposed**
  ```bash
  kubectl get svc
  # Success: All services have endpoints
  ```

- [ ] **Ingress/ALB configured**
  ```bash
  kubectl get ingress
  # Success: ALB provisioned with healthy targets
  ```

### Application Health

- [ ] **Health checks passing**
  ```bash
  for svc in frontend api-gateway intent-classifier technique-selector prompt-generator; do
    curl -f http://${svc}/health || echo "$svc health check failed"
  done
  # Success: All return 200 OK
  ```

- [ ] **Database connectivity**
  ```bash
  kubectl exec -it deployment/api-gateway -- psql -h ${RDS_ENDPOINT} -U app -c "SELECT 1"
  # Success: Query returns 1
  ```

- [ ] **Redis connectivity**
  ```bash
  kubectl exec -it deployment/api-gateway -- redis-cli -h ${REDIS_ENDPOINT} ping
  # Success: PONG response
  ```

## ⚡ Auto-scaling Validation

### Cluster Autoscaler

- [ ] **Cluster Autoscaler running**
  ```bash
  kubectl -n kube-system get deployment cluster-autoscaler
  # Success: 1/1 replicas ready
  ```

- [ ] **Node scaling tested**
  ```bash
  # Create high pod count
  kubectl scale deployment/frontend --replicas=20
  kubectl get nodes -w
  # Success: New nodes added within 5 minutes
  ```

### Horizontal Pod Autoscaler

- [ ] **HPA configured for all services**
  ```bash
  kubectl get hpa
  # Success: All services have HPA with proper metrics
  ```

- [ ] **HPA scaling tested**
  ```bash
  # Generate load
  kubectl run -it --rm load-test --image=busybox -- sh
  # Run load test against service
  kubectl get hpa -w
  # Success: Replicas increase under load
  ```

### Vertical Pod Autoscaler

- [ ] **VPA providing recommendations**
  ```bash
  kubectl get vpa
  kubectl describe vpa frontend-vpa
  # Success: Recommendations present
  ```

## 💰 Cost Optimization Validation

### Spot Instances

- [ ] **Spot instance handler running**
  ```bash
  kubectl -n kube-system get ds aws-node-termination-handler
  # Success: Running on all nodes
  ```

- [ ] **Spot instances in use**
  ```bash
  aws ec2 describe-instances --filters "Name=instance-lifecycle,Values=spot" \
    "Name=instance-state-name,Values=running"
  # Success: Multiple spot instances running
  ```

### Resource Controls

- [ ] **Resource quotas applied**
  ```bash
  kubectl describe resourcequota -A
  # Success: Quotas enforced in all namespaces
  ```

- [ ] **Limit ranges configured**
  ```bash
  kubectl describe limitrange -A
  # Success: Default limits set
  ```

### Cost Monitoring

- [ ] **Prometheus rules loaded**
  ```bash
  kubectl -n monitoring get configmap cost-monitoring-rules
  # Success: ConfigMap exists
  ```

- [ ] **Grafana dashboards accessible**
  ```bash
  kubectl -n monitoring port-forward svc/grafana 3000:3000
  # Browse to http://localhost:3000
  # Success: Cost dashboard visible
  ```

## 🔒 Security Validation

### Network Security

- [ ] **Security groups configured**
  ```bash
  aws ec2 describe-security-groups --filters "Name=tag:Project,Values=BetterPrompts"
  # Success: Minimal required rules only
  ```

- [ ] **Network policies applied**
  ```bash
  kubectl get networkpolicy
  # Success: Policies restricting traffic
  ```

### Data Security

- [ ] **Encryption at rest enabled**
  ```bash
  aws rds describe-db-instances --db-instance-identifier betterprompts-${ENVIRONMENT} \
    --query 'DBInstances[0].StorageEncrypted'
  # Success: true
  ```

- [ ] **Secrets properly managed**
  ```bash
  kubectl get secrets
  aws secretsmanager list-secrets
  # Success: No plaintext secrets in configs
  ```

### Access Control

- [ ] **IRSA configured**
  ```bash
  kubectl get sa -A -o yaml | grep eks.amazonaws.com/role-arn
  # Success: Service accounts have IAM roles
  ```

- [ ] **Pod security standards**
  ```bash
  kubectl get ns --show-labels | grep pod-security
  # Success: Namespaces have security labels
  ```

## 📊 Performance Validation

### Response Times

- [ ] **API latency within SLA**
  ```bash
  curl -w "@curl-format.txt" -o /dev/null -s https://api.betterprompts.ai/health
  # Success: p95 < 200ms
  ```

- [ ] **ML inference performance**
  ```bash
  # Test inference endpoint
  time curl -X POST https://api.betterprompts.ai/v1/analyze \
    -H "Content-Type: application/json" \
    -d '{"text": "Test prompt"}'
  # Success: p95 < 500ms
  ```

### Load Testing

- [ ] **Sustained load handled**
  ```bash
  k6 run scripts/load-test.js
  # Success: 10,000 RPS with <1% error rate
  ```

- [ ] **Auto-scaling under load**
  ```bash
  # During load test
  kubectl get hpa -w
  kubectl get nodes -w
  # Success: Pods and nodes scale appropriately
  ```

## 🔍 Monitoring Validation

### Metrics Collection

- [ ] **Prometheus scraping metrics**
  ```bash
  kubectl -n monitoring port-forward svc/prometheus 9090:9090
  # Browse to http://localhost:9090/targets
  # Success: All targets UP
  ```

- [ ] **CloudWatch metrics flowing**
  ```bash
  aws cloudwatch list-metrics --namespace "AWS/EKS"
  # Success: Cluster metrics present
  ```

### Alerting

- [ ] **Critical alerts configured**
  ```bash
  kubectl -n monitoring get prometheusrule
  # Success: Alert rules present
  ```

- [ ] **Alert notifications working**
  ```bash
  # Trigger test alert
  kubectl -n monitoring exec -it alertmanager-0 -- amtool alert add test
  # Success: Alert received via configured channel
  ```

### Logging

- [ ] **Container logs collected**
  ```bash
  kubectl logs -n kube-system fluentd-xxxxx
  # Success: Logs forwarding to destination
  ```

- [ ] **CloudWatch logs groups created**
  ```bash
  aws logs describe-log-groups | grep betterprompts
  # Success: Log groups for all components
  ```

## ✅ Post-Migration Validation

### Traffic Validation

- [ ] **DNS resolving correctly**
  ```bash
  dig api.betterprompts.ai
  nslookup api.betterprompts.ai
  # Success: Points to ALB
  ```

- [ ] **SSL certificates valid**
  ```bash
  openssl s_client -connect api.betterprompts.ai:443 -servername api.betterprompts.ai
  # Success: Certificate valid and not expired
  ```

### Data Integrity

- [ ] **Database record counts match**
  ```sql
  -- Run on both old and new databases
  SELECT COUNT(*) FROM users;
  SELECT COUNT(*) FROM prompts;
  -- Success: Counts match exactly
  ```

- [ ] **Application functionality verified**
  - User can register/login
  - Prompts can be created/analyzed
  - ML features working correctly

### Cost Tracking

- [ ] **Costs within budget**
  ```bash
  aws ce get-cost-and-usage \
    --time-period Start=$(date -d '7 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
    --granularity DAILY \
    --metrics UnblendedCost
  # Success: Daily costs align with projections
  ```

- [ ] **Cost optimization active**
  ```bash
  # Check savings plan utilization
  aws ce get-savings-plans-utilization
  # Success: >80% utilization
  ```

## 📝 Documentation Validation

- [ ] **Runbooks updated**
  - Deployment procedures
  - Troubleshooting guides
  - Emergency procedures

- [ ] **Architecture diagrams current**
  - Network topology
  - Application architecture
  - Data flow diagrams

- [ ] **Team trained**
  - Can perform deployments
  - Can troubleshoot issues
  - Understand monitoring

## 🚨 Emergency Validation

- [ ] **Rollback procedure tested**
  - Can rollback application changes
  - Database restore verified
  - DNS failover works

- [ ] **Disaster recovery plan**
  - Backup restoration tested
  - Cross-region failover documented
  - RTO/RPO targets defined

- [ ] **On-call setup**
  - Escalation path defined
  - Contact information current
  - Alert routing configured

---

## Validation Sign-off

| Component | Validated By | Date | Notes |
|-----------|--------------|------|-------|
| Infrastructure | | | |
| Application | | | |
| Security | | | |
| Performance | | | |
| Cost | | | |
| Documentation | | | |

**Final Approval**:
- Technical Lead: _________________ Date: _______
- Infrastructure Lead: _____________ Date: _______
- Security Lead: ___________________ Date: _______
- Product Owner: ___________________ Date: _______

---

This checklist should be completed in phases throughout the migration, with final validation performed before cutting over production traffic.