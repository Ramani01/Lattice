# Graph Report - lattice_capstone  (2026-07-30)

## Corpus Check
- 42 files · ~66,406 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 293 nodes · 481 edges · 22 communities (18 shown, 4 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 23 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ff4a26ff`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- dynamic_discovery.py
- agent.py
- live_app.py
- generate_gitops_pipeline
- calculate_betweenness_centrality
- run_synthetic_benchmark
- validate_plan
- build_research_doc.py
- fetch_vault_secrets
- run_blast_radius_analysis
- calculate_risk_score
- ingest.py
- clean_docx_asterisks.py
- lattice-capstone
- Lattica: GraphRAG-Based Infrastructure Impact Analysis & Safe Execution Planning Framework
- 🚀 Lattice: AI-Assisted Microservices Migration Planner
- Walkthrough - Lattica PQC Migration Planner (Dynamic Discovery & Graph Discovery Agent Upgrade)
- rules/graphify.md
- workflows/graphify.md
- synthetic_results_summary.md

## God Nodes (most connected - your core abstractions)
1. `compute_deterministic_topo_plan()` - 15 edges
2. `compute_scc_condensation()` - 13 edges
3. `DiscoveryProvider` - 12 edges
4. `DockerComposeProvider` - 12 edges
5. `EbpfLogsProvider` - 12 edges
6. `calculate_pagerank()` - 12 edges
7. `calculate_betweenness_centrality()` - 12 edges
8. `validate_plan()` - 12 edges
9. `generate_gitops_pipeline()` - 11 edges
10. `run_agent()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `_generate_single_plan()` --calls--> `get_depth()`  [INFERRED]
  agent.py → live_app.py
- `load_context()` --calls--> `scan_services()`  [INFERRED]
  agent.py → discovery.py
- `run_reproducible_demo()` --calls--> `create_provenance_edge()`  [EXTRACTED]
  run_demo.py → agent.py
- `run_reproducible_demo()` --calls--> `compute_scc_condensation()`  [EXTRACTED]
  run_demo.py → agent.py
- `run_reproducible_demo()` --calls--> `compute_deterministic_topo_plan()`  [EXTRACTED]
  run_demo.py → agent.py

## Import Cycles
- None detected.

## Communities (22 total, 4 thin omitted)

### Community 0 - "dynamic_discovery.py"
Cohesion: 0.08
Nodes (29): LatticeConfig, Lattice Enterprise Configuration System Centralized, environment-aware…, Lattice Discovery Package Contains dynamic infrastructure and codebase…, DatadogApmProvider, DiscoveryProvider, DockerComposeProvider, EbpfLogsProvider, KialiIstioProvider (+21 more)

### Community 1 - "agent.py"
Cohesion: 0.10
Nodes (35): AgentState, build_agent_graph(), calculate_betweenness_centrality(), calculate_pagerank(), call_ollama(), compute_deterministic_topo_plan(), compute_scc_condensation(), create_provenance_edge() (+27 more)

### Community 2 - "live_app.py"
Cohesion: 0.07
Nodes (27): calculate_betweenness_centrality(), calculate_pagerank(), call_ollama(), call_ollama_stream(), connect_neo4j(), generate_mermaid_flowchart(), get_depth(), get_ollama_models() (+19 more)

### Community 3 - "generate_gitops_pipeline"
Cohesion: 0.14
Nodes (19): Lattice GitOps Package Contains Istio traffic-shadowing manifest generators,…, apply_local_git_changes(), create_github_pull_request(), extract_service_context(), generate_destination_rule(), generate_gitops_pipeline(), generate_virtual_service(), Any (+11 more)

### Community 4 - "calculate_betweenness_centrality"
Cohesion: 0.15
Nodes (11): calculate_betweenness_centrality(), calculate_pagerank(), Calculates PageRank metrics using pure Python power iteration., Calculates Betweenness Centrality metrics using pure Python Brandes' algorithm., Executes the pipeline: fetch nodes/edges -> connect to Neo4j -> clear ->…, run_ingestion_and_analysis(), Lattice Graph Package Contains graph analytics, PageRank, Betweenness…, TestGraphMetrics (+3 more)

### Community 5 - "run_synthetic_benchmark"
Cohesion: 0.24
Nodes (11): Lattice Benchmark Package Contains 30-DAG statistical generalization suite and…, Renders a sleek, state-of-the-art 4-Way Scientific Benchmark Comparison view., render_4way_comparison_ui(), compute_stats(), generate_synthetic_dag(), plot_synthetic_rigor_chart(), Generates a 4-panel publication plot detailing statistical rigor across DAG…, Generates a directed acyclic graph (DAG) representing microservice architecture… (+3 more)

### Community 6 - "validate_plan"
Cohesion: 0.22
Nodes (7): Any, Lattice Deterministic Plan Validator Decoupled validation logic for execution…, Validate plan for dependency violations, routing to binary or execution…, Validate execution plan containing both Transition and Target stages., validate_execution_plan(), validate_plan(), TestValidatorRules

### Community 7 - "build_research_doc.py"
Cohesion: 0.33
Nodes (10): add_markdown(), add_page_number(), add_table(), build(), configure(), is_table_line(), parse_table_line(), Build a polished Word version of the Lattice research-paper draft. (+2 more)

### Community 8 - "fetch_vault_secrets"
Cohesion: 0.36
Nodes (8): fetch_vault_secrets(), get_aws_secret(), get_hashicorp_secret(), Any, Retrieves credentials in real-time from AWS Secrets Manager using boto3. Raises…, Retrieves credentials from HashiCorp Vault via requests GET., Unified entrypoint to fetch secrets in real-time. No mock data or static…, Lattice Utilities Package Contains secrets manager integrations for AWS Secrets…

### Community 9 - "run_blast_radius_analysis"
Cohesion: 0.28
Nodes (7): calculate_betweenness_centrality(), calculate_pagerank(), Calculates PageRank metrics using pure Python power iteration., Calculates Betweenness Centrality metrics using pure Python Brandes' algorithm., run_blast_radius_analysis(), Scan the services directory for crypto configurations., scan_services()

### Community 10 - "calculate_risk_score"
Cohesion: 0.33
Nodes (3): calculate_risk_score(), Calculates a composite asset Risk Score (0 - 100) combining Change Blast Radius…, TestIdentityResolutionAndRiskScore

### Community 11 - "ingest.py"
Cohesion: 0.29
Nodes (6): ingest_to_neo4j(), load_inventory(), parse_docker_compose(), Parse docker-compose.yml to extract service dependencies., Load discovery inventory JSON., Ingest inventory and dependencies into Neo4j.

### Community 12 - "clean_docx_asterisks.py"
Cohesion: 0.67
Nodes (3): clean_paragraphs(), clean_table(), Remove literal asterisks from all editable text in the research-paper DOCX.

### Community 15 - "Lattica: GraphRAG-Based Infrastructure Impact Analysis & Safe Execution Planning Framework"
Cohesion: 0.11
Nodes (17): A. Stage 1: Graph Discovery Agent, Abstract, B. Stage 2: Topological Ingestion & Infrastructure Mapping, C. Real-World Codebase Validation (DevSecOps), C. Stage 3: Blast Radius Analysis, D. Large-Scale Statistical Generalization & Scale Invariance (30-DAG Evaluation), D. Stage 4: AI Execution Planning Agents, E. Stage 5: GitOps CI/CD Pipeline (+9 more)

### Community 16 - "🚀 Lattice: AI-Assisted Microservices Migration Planner"
Cohesion: 0.12
Nodes (16): 1. Run the Reproducible End-to-End System Demo, 1. Virtual Environment Setup, 2. Run the Verified Automated Test Suite (19/19 Unit & Integration Tests), 3. Run the Interactive Streamlit Web App, 4. Run the 30-DAG Statistical Generalization Benchmark, 📊 Benchmark Results & Expected Output, 🛠️ Environment Setup & Reproducibility, 🔌 Integration Classification Matrix (+8 more)

### Community 17 - "Walkthrough - Lattica PQC Migration Planner (Dynamic Discovery & Graph Discovery Agent Upgrade)"
Cohesion: 0.22
Nodes (8): 1. Accomplishments & Key Findings, 2. Codebase Architecture, 3. Results Visualization, 4. Verification & Testing Process, 5. GitOps & CI/CD Pipeline Automation (Production Upgrade), 6. Secure Secrets Retrieval & Clustered Neo4j Database Deployment (Production Level), Ingested Service Ingestion Pipeline, Walkthrough - Lattica PQC Migration Planner (Dynamic Discovery & Graph Discovery Agent Upgrade)

## Knowledge Gaps
- **36 isolated node(s):** `LatticeConfig`, `lattice-capstone`, `graphify`, `Workflow: graphify`, `🏗️ System Architecture & Workflow` (+31 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `validate_plan()` connect `validate_plan` to `agent.py`, `live_app.py`, `generate_gitops_pipeline`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `EbpfLogsProvider` connect `dynamic_discovery.py` to `live_app.py`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `generate_gitops_pipeline()` connect `generate_gitops_pipeline` to `live_app.py`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `DiscoveryProvider` (e.g. with `DiscoveryError` and `GraphAnalysisError`) actually correct?**
  _`DiscoveryProvider` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `DockerComposeProvider` (e.g. with `DiscoveryError` and `GraphAnalysisError`) actually correct?**
  _`DockerComposeProvider` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `LatticeConfig`, `lattice-capstone`, `graphify` to the rest of the system?**
  _36 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `dynamic_discovery.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07585568917668825 - nodes in this community are weakly interconnected._