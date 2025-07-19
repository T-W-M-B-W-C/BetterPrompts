# Phase 1: Analysis and Planning
/sc:analyze current_infrastructure
  - Analyze existing project structure, dependencies, and resource requirements
  - Identify Python data science/ML components and JavaScript frontend assets
  - Assess current database, storage, and compute needs

/sc:estimate aws_migration_scope
  - Calculate resource requirements for AWS
  - Estimate costs for MVP and scaled versions
  - Identify potential bottlenecks and optimization points

# Phase 2: Architecture Design
/sc:design aws_architecture_mvp
  - Design AWS architecture for Python backend (EC2/ECS/Lambda)
  - Plan ML/AI deployment (SageMaker vs EC2 with GPU)
  - Design frontend hosting (S3 + CloudFront)
  - Include RDS/DynamoDB for data persistence
  - Add scaling components (ALB, Auto Scaling Groups)

/sc:design scaling_strategy
  - Design horizontal scaling for compute resources
  - Plan database read replicas and caching (ElastiCache)
  - Design CDN strategy for static assets
  - Include monitoring and alerting architecture

# Phase 3: Implementation
/sc:implement aws_infrastructure_code
  - Create Terraform/CloudFormation templates
  - Implement VPC, subnets, and security groups
  - Set up IAM roles and policies
  - Configure networking and load balancers

/sc:implement containerization
  - Dockerize Python backend services
  - Create docker-compose for local testing
  - Build CI/CD pipeline configuration
  - Implement health checks and logging

/sc:implement deployment_pipeline
  - Set up GitHub Actions/GitLab CI for automated deployments
  - Implement blue-green deployment strategy
  - Configure environment-specific configurations
  - Set up automated testing in pipeline

# Phase 4: Migration Execution
/sc:build aws_resources
  - Deploy infrastructure using IaC
  - Build and push Docker images to ECR
  - Deploy database schemas and initial data
  - Configure monitoring and logging services

/sc:implement data_migration
  - Create data migration scripts
  - Implement zero-downtime migration strategy
  - Set up data validation and rollback procedures
  - Configure backup and recovery processes

# Phase 5: Testing and Validation
/sc:test aws_deployment
  - Run integration tests on AWS infrastructure
  - Perform load testing for MVP capacity
  - Test auto-scaling triggers
  - Validate disaster recovery procedures

/sc:troubleshoot migration_issues
  - Debug any deployment problems
  - Optimize performance bottlenecks
  - Fine-tune resource allocations
  - Resolve security and access issues

# Phase 6: Optimization and Documentation
/sc:improve cost_optimization
  - Implement cost-saving measures (spot instances, reserved capacity)
  - Optimize resource utilization
  - Set up cost alerts and budgets
  - Implement automated resource scheduling

/sc:cleanup unused_resources
  - Remove old infrastructure components
  - Clean up temporary migration resources
  - Optimize Docker images and dependencies
  - Archive old deployment artifacts

/sc:document aws_architecture
  - Document final architecture and design decisions
  - Create runbooks for common operations
  - Document scaling procedures
  - Create disaster recovery documentation

# Phase 7: Git and Task Management
/sc:git create_migration_branch
  - Set up feature branches for migration code
  - Implement proper commit structure
  - Tag releases appropriately

/sc:task track_migration_progress
  - Track completion of migration milestones
  - Monitor blockers and dependencies
  - Update stakeholders on progress