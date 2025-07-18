# Model Serving Infrastructure

This directory contains the TorchServe-based model serving infrastructure for BetterPrompts.

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Load Balancer │────▶│   API Gateway    │────▶│   TorchServe    │
│    (Traefik)    │     │    (Kong/Nginx)  │     │   Instances     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                           │
                                ┌──────────────────────────┴───────────────────────────┐
                                │                                                      │
                        ┌───────▼────────┐                                    ┌────────▼────────┐
                        │   TorchServe   │                                    │   TorchServe    │
                        │   Instance 1   │                                    │   Instance 2    │
                        │  (GPU/CPU)     │                                    │  (GPU/CPU)      │
                        └────────────────┘                                    └─────────────────┘
                                │                                                      │
                        ┌───────▼────────┐                                    ┌────────▼────────┐
                        │  Model Store   │                                    │  Model Store    │
                        │  (S3/NFS)      │                                    │  (S3/NFS)       │
                        └────────────────┘                                    └─────────────────┘
```

## Components

1. **TorchServe**: Core model serving engine
2. **Model Store**: Centralized model storage (S3/NFS)
3. **API Gateway**: Request routing and authentication
4. **Load Balancer**: Traffic distribution
5. **Monitoring Stack**: Prometheus + Grafana
6. **Logging**: ELK Stack integration

## Directory Structure

```
model-serving/
├── torchserve/           # TorchServe configurations
│   ├── config/           # Server configurations
│   ├── handlers/         # Custom model handlers
│   └── models/           # Model archives
├── kubernetes/           # K8s deployment manifests
│   ├── base/            # Base configurations
│   └── overlays/        # Environment-specific configs
├── docker/              # Docker configurations
├── monitoring/          # Monitoring setup
├── scripts/             # Utility scripts
└── tests/              # Integration tests
```

## Model Requirements

- **Intent Classifier**: DeBERTa-v3-base with custom heads
  - Input: Text (max 512 tokens)
  - Output: Intent class, confidence scores, complexity
  - Latency: <500ms p95
  - Throughput: 1000+ RPS

## Getting Started

1. Build and archive models: `./scripts/build_models.sh`
2. Deploy to Kubernetes: `kubectl apply -k kubernetes/overlays/production`
3. Monitor: Access Grafana at http://monitoring.example.com