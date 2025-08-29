# BetterPrompts AWS Phase 0 Migration

## 🚀 Quick Start (2 Minutes)

```bash
# One command deployment
./scripts/deploy-to-aws.sh

# Access your app
# Frontend: http://[EC2-IP]:3000
# API: http://[EC2-IP]/api/v1
```

## 📁 Files Created

- **docs/aws-migration-phase0.md** - Complete migration guide with all details
- **docs/aws-quick-reference.md** - Quick command reference
- **scripts/aws-create-resources.sh** - Creates all AWS resources
- **scripts/deploy-to-aws.sh** - One-click deployment script
- **scripts/teardown-aws.sh** - Cleanup script

## 🎯 What This Does

Creates a minimal AWS environment for faster development:
- Single EC2 instance (t3.xlarge)
- RDS PostgreSQL with pgvector
- ElastiCache Redis
- Simple VPC with public access
- No production features (no auto-scaling, CDN, etc.)

## 💰 Cost

~$7/day or ~$215/month

## 🛠️ Requirements

- AWS CLI installed and configured
- GitHub repository with BetterPrompts code
- OpenAI and Anthropic API keys

## ⚡ Benefits

1. **Faster builds** - No local Docker overhead
2. **Better performance** - AWS infrastructure
3. **Team access** - Shared development environment
4. **Persistent data** - Survives restarts

## 🧹 Cleanup

```bash
# Delete everything when done
./scripts/teardown-aws.sh
```

## ⚠️ Important Notes

- This is for DEVELOPMENT ONLY
- Security is minimal (public access)
- No backups or redundancy
- Update API keys in .env.aws before deploying

## 📚 Next Steps

See `docs/aws-migration-phase0.md` for:
- Detailed setup instructions
- Troubleshooting guide
- Phase 1 production recommendations