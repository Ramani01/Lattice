# Lattice: AI-Assisted Microservices Migration Planner

Lattice is an enterprise-grade microservices migration planner and dynamic topology discovery engine. It supports real-time service graph ingestion from Kubernetes/Istio (Kiali), Datadog APM, eBPF network trace logs, Docker Compose, and deep static code analysis.

## Key Features
- **Dynamic Infrastructure Discovery**: Automatically extracts microservice dependencies and builds a transactional Neo4j service graph.
- **Topological Centrality Analysis**: Calculates PageRank, Betweenness Centrality, and Change Blast Radius (CBR).
- **Federated Dual-Agent Planner**: Uses GraphRAG domain decomposition to sequence multi-phase, zero-downtime rolling upgrades.
- **GitOps & CI/CD Automation**: Automatically generates Istio traffic shadowing rules (`DestinationRule` & `VirtualService`) and stages GitHub PRs for migration phases.