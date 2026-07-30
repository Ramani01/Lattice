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

## 🔌 Integration Classification Matrix

To maintain transparent capstone boundaries, all components are explicitly classified across three implementation tiers:

| Component Category | Integration Status | Provider / Module | Operational Behavior & Fallback Details |
| :--- | :--- | :--- | :--- |
| **Topology Discovery** | **Fully Implemented (Native)** | `DockerComposeProvider`, `EbpfLogsProvider`, AST Scanner | Native local parsing of `docker-compose.yml`, eBPF network trace log streams (`.jsonl`), and Python code AST parsing ([dynamic_discovery.py](file:///c:/Users/hp/Desktop/lattice_capstone/dynamic_discovery.py)). |
| **Topology Discovery** | **Optional API Connectors** | `KialiIstioProvider`, `DatadogApmProvider` | Standardized interface connectors for Kubernetes/Istio Kiali REST API and Datadog APM API. |
| **Graph Analytics** | **Live + Fallback** | Neo4j Engine & Pure Python Centrality | Connects to live Neo4j database (`bolt://127.0.0.1:7687`); falls back automatically to pure Python in-memory algorithms (`calculate_pagerank`, `calculate_betweenness_centrality`) if Neo4j is unreachable. |
| **Migration Planning** | **Fully Implemented (Core)** | Deterministic Topo Planner & Tarjan SCC | Pure Python graph algorithms providing 100% constraint-safe execution DAG ordering and cycle condensation with 0 conflicts ([agent.py](file:///c:/Users/hp/Desktop/lattice_capstone/agent.py)). |
| **LLM Enrichment** | **Optional Local LLM + Fallback** | `enrich_plan_with_llm` (Ollama integration) | Queries local [Ollama](https://ollama.ai) engine (`qwen2`, `phi3`) for release notes; falls back automatically to deterministic template enrichment if Ollama is unavailable. |
| **Secrets Management** | **Live External Integration** | AWS Secrets Manager & HashiCorp Vault | Real-time live API/SDK integrations via `boto3` and HashiCorp Vault REST API ([secrets_manager.py](file:///c:/Users/hp/Desktop/lattice_capstone/secrets_manager.py)). |
| **GitOps Delivery** | **Implemented + Dry-Run Safeguard** | Istio Manifest Generators & GitHub REST API | Generates 100% compliant Istio `DestinationRule` & `VirtualService` YAML manifests locally. GitHub REST API PR creation enforces mandatory `dry_run = True` safeguard ([gitops_pipeline.py](file:///c:/Users/hp/Desktop/lattice_capstone/gitops_pipeline.py)). |

---

## 🛠️ Environment Setup & Reproducibility

### 1. Virtual Environment Setup

#### Linux / macOS:
```bash
# Create a virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install editable package dependencies
pip install -e .
```

#### Windows (PowerShell / CMD):
```powershell
# Create a virtual environment
python -m venv venv

# Activate virtual environment (PowerShell)
.\venv\Scripts\Activate.ps1

# Install editable package dependencies
pip install -e .
```

---

## ⚡ Quick Start & Verified Test Execution

### 1. Run the Reproducible End-to-End System Demo
```bash
python run_demo.py
```

### 2. Run the Verified Automated Test Suite (19/19 Unit & Integration Tests)
```bash
python tests/run_all_tests.py
```

### 3. Run the Interactive Streamlit Web App
```bash
python -m streamlit run live_app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser to interact with the visual dashboard.

### 4. Run the 30-DAG Statistical Generalization Benchmark
```bash
python synthetic_benchmark.py
```

---

---

## 🛡️ Security & Threat Model

1. **Credential Handling & Token Masking**: All GitHub Personal Access Tokens (PATs), AWS secret keys, and HashiCorp Vault tokens are masked (`ghp_****`) in terminal logs and session states.
2. **Unsafe PR Generation Safeguard**: Mandatory `dry_run = True` default enforces local YAML preview generation, requiring explicit `--apply` user confirmation before executing remote GitHub REST API commits.
3. **Untrusted Repository Scanning**: The AST code scanner operates strictly read-only, parsing local ASTs without executing untrusted third-party code.


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