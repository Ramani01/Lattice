# 🚀 Lattice: AI-Assisted Microservices Migration Planner

Lattice is an enterprise-grade microservices architecture migration engine and dynamic topology discovery platform. It automatically extracts microservice dependency graphs from Kubernetes/Istio (Kiali), Datadog APM, eBPF network trace logs, Docker Compose, and code AST analysis.

Lattice combines a **100% constraint-safe deterministic graph engine** with **LLM release note enrichment** to guarantee zero-downtime microservice migration paths with 0 dependency conflicts.

---

## 🏗️ System Architecture & Workflow

```
                        ┌─────────────────────────────────────────┐
                        │   Ingestion & Topology Discovery       │
                        │  (Kiali, Datadog, eBPF, Docker, AST)    │
                        └────────────────────┬────────────────────┘
                                             │
                                             ▼
                        ┌─────────────────────────────────────────┐
                        │   Neo4j Graph & Centrality Analytics    │
                        │  (PageRank, Betweenness, CBR, DI)       │
                        └────────────────────┬────────────────────┘
                                             │
                                             ▼
                 ┌───────────────────────────────────────────────────────┐
                 │          Federated Dual-Agent Architecture            │
                 ├───────────────────────────┬───────────────────────────┤
                 │  Deterministic Topo       │   LLM Plan Enricher       │
                 │  Planner (Kahn's Depth)   │   & Explainer             │
                 │  (0-Conflict Guaranteed)  │   (Release Notes & PRs)   │
                 └─────────────┬─────────────┴─────────────┬─────────────┘
                               │                           │
                               └─────────────┬─────────────┘
                                             │
                                             ▼
                        ┌─────────────────────────────────────────┐
                        │  GitOps & Istio Traffic Shadowing       │
                        │ (DestinationRules, VirtualServices, PRs)│
                        └─────────────────────────────────────────┘
```

---

## 🛠️ Prerequisites

- **Python**: 3.10 or higher
- **Local LLM Engine** *(Optional for Offline Mode)*: [Ollama](https://ollama.ai) (`qwen2:1.5b`, `phi3:mini`, `gemma:7b-instruct-q4_K_M`)
- **Graph Database** *(Optional - Pure Python Fallback Included)*: [Neo4j v5.0+](https://neo4j.com)

---

## ⚡ Quick Start (One-Command Demos)

### 1. Run the Interactive Streamlit Web App
```bash
python -m streamlit run live_app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser to interact with the visual dashboard.

### 2. Run the Full Automated Test Suite (12 Unit Tests)
```bash
python tests/run_all_tests.py
```

### 3. Run the 30-DAG Statistical Generalization Benchmark
```bash
python synthetic_benchmark.py
```

---

## 🔒 Safe / No-Credential Mode (Local Offline Lab)

Lattice runs completely **offline without requiring cloud API keys, AWS credentials, or HashiCorp Vault tokens**.

- **Provider**: Select `Local Docker Lab` or `eBPF Connection Logs` in the sidebar.
- **Database Fallback**: If Neo4j is offline, Lattice automatically switches to the **Pure Python In-Memory Topological Engine** with zero configuration required.
- **LLM Fallback**: If Ollama is offline or uninstalled, Lattice uses structured deterministic fallbacks so all UI features remain 100% operational.

---

## 📊 Benchmark Results & Expected Output

### Statistical Rigor Suite (30 Synthetic Microservice DAGs)

| Graph Scale | Planning Strategy | Success Rate (%) | Mean Conflicts (95% CI) | Variance ($\sigma^2$) | Mean Latency (95% CI) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Small ($N=10$)** | **1. Deterministic Topo** | **100.0%** | **0.00 ± 0.00** | **0.00** | 0.0393s ± 0.0345s |
| Small ($N=10$) | 2. Baseline LLM (Control) | 0.0% | 21.00 ± 1.82 | 8.67 | 0.0662s ± 0.0553s |
| Small ($N=10$) | **4. AI Execution Planner (Reconciled)** | **100.0%** | **0.00 ± 0.00** | **0.00** | 0.0642s ± 0.0194s |
| **Medium ($N=25$)** | **1. Deterministic Topo** | **100.0%** | **0.00 ± 0.00** | **0.00** | 0.0286s ± 0.0121s |
| Medium ($N=25$) | 2. Baseline LLM (Control) | 0.0% | 71.20 ± 4.90 | 62.40 | 0.0366s ± 0.0059s |
| Medium ($N=25$) | **4. AI Execution Planner (Reconciled)** | **100.0%** | **0.00 ± 0.00** | **0.00** | 0.0498s ± 0.0141s |
| **Large ($N=50$)** | **1. Deterministic Topo** | **100.0%** | **0.00 ± 0.00** | **0.00** | 0.0240s ± 0.0019s |
| Large ($N=50$) | 2. Baseline LLM (Control) | 0.0% | 150.10 ± 6.82 | 121.21 | 0.0408s ± 0.0056s |
| Large ($N=50$) | **4. AI Execution Planner (Reconciled)** | **100.0%** | **0.00 ± 0.00** | **0.00** | 0.0567s ± 0.0194s |

---

## 🧪 Test Suite Organization (`tests/`)

- **[`tests/test_graph_metrics.py`](file:///c:/Users/hp/Desktop/lattice_capstone/tests/test_graph_metrics.py)**: PageRank, Betweenness Centrality, and reachability.
- **[`tests/test_cycle_detection.py`](file:///c:/Users/hp/Desktop/lattice_capstone/tests/test_cycle_detection.py)**: Topological depth binning and cycle fallback handling.
- **[`tests/test_validator_rules.py`](file:///c:/Users/hp/Desktop/lattice_capstone/tests/test_validator_rules.py)**: Dependency rule validation and missing caller/callee detection.
- **[`tests/test_discovery_parsers.py`](file:///c:/Users/hp/Desktop/lattice_capstone/tests/test_discovery_parsers.py)**: eBPF JSONL network trace and Docker Compose parsers.
- **[`tests/test_gitops_manifests.py`](file:///c:/Users/hp/Desktop/lattice_capstone/tests/test_gitops_manifests.py)**: Istio `DestinationRule` and `VirtualService` 10% traffic-mirroring YAML generation.