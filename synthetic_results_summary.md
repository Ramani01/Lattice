# 30-DAG Statistical Generalization Benchmark Results

| Graph Scale   | Planning Strategy                    | Success Rate (%)   | Mean Conflicts (95% CI)   |   Variance (Var) | Mean Latency (95% CI)   |
|---------------|--------------------------------------|--------------------|---------------------------|------------------|-------------------------|
| Small (N=10)  | 1. Deterministic Topo (No LLM)       | 100.0%             | 0.00 ± 0.00               |             0    | 0.0240s ± 0.0119s       |
| Small (N=10)  | 2. Baseline LLM (Control)            | 0.0%               | 21.00 ± 1.82              |             8.67 | 0.0361s ± 0.0031s       |
| Small (N=10)  | 3. Lattica Single-Agent              | 0.0%               | 21.00 ± 1.82              |             8.67 | 0.0273s ± 0.0042s       |
| Small (N=10)  | 4. AI Execution Planner (Reconciled) | 100.0%             | 0.00 ± 0.00               |             0    | 0.0547s ± 0.0135s       |
| Medium (N=25) | 1. Deterministic Topo (No LLM)       | 100.0%             | 0.00 ± 0.00               |             0    | 0.0197s ± 0.0028s       |
| Medium (N=25) | 2. Baseline LLM (Control)            | 0.0%               | 71.20 ± 4.90              |            62.4  | 0.0333s ± 0.0051s       |
| Medium (N=25) | 3. Lattica Single-Agent              | 0.0%               | 71.20 ± 4.90              |            62.4  | 0.0312s ± 0.0048s       |
| Medium (N=25) | 4. AI Execution Planner (Reconciled) | 100.0%             | 0.00 ± 0.00               |             0    | 0.0389s ± 0.0065s       |
| Large (N=50)  | 1. Deterministic Topo (No LLM)       | 100.0%             | 0.00 ± 0.00               |             0    | 0.0159s ± 0.0020s       |
| Large (N=50)  | 2. Baseline LLM (Control)            | 0.0%               | 150.10 ± 6.82             |           121.21 | 0.0325s ± 0.0045s       |
| Large (N=50)  | 3. Lattica Single-Agent              | 0.0%               | 150.10 ± 6.82             |           121.21 | 0.0333s ± 0.0062s       |
| Large (N=50)  | 4. AI Execution Planner (Reconciled) | 100.0%             | 0.00 ± 0.00               |             0    | 0.0665s ± 0.0190s       |
