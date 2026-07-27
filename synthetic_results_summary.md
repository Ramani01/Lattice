# 30-DAG Statistical Generalization Benchmark Results

| Graph Scale   | Planning Strategy                    | Success Rate (%)   | Mean Conflicts (95% CI)   |   Variance (Var) | Mean Latency (95% CI)   |
|---------------|--------------------------------------|--------------------|---------------------------|------------------|-------------------------|
| Small (N=10)  | 1. Deterministic Topo (No LLM)       | 100.0%             | 0.00 ± 0.00               |             0    | 0.0944s ± 0.0914s       |
| Small (N=10)  | 2. Baseline LLM (Control)            | 0.0%               | 21.00 ± 1.82              |             8.67 | 0.2212s ± 0.3225s       |
| Small (N=10)  | 3. Lattica Single-Agent              | 0.0%               | 21.00 ± 1.82              |             8.67 | 0.1171s ± 0.0515s       |
| Small (N=10)  | 4. AI Execution Planner (Reconciled) | 100.0%             | 0.00 ± 0.00               |             0    | 0.2505s ± 0.2445s       |
| Medium (N=25) | 1. Deterministic Topo (No LLM)       | 100.0%             | 0.00 ± 0.00               |             0    | 0.0311s ± 0.0082s       |
| Medium (N=25) | 2. Baseline LLM (Control)            | 0.0%               | 71.20 ± 4.90              |            62.4  | 0.1016s ± 0.0529s       |
| Medium (N=25) | 3. Lattica Single-Agent              | 0.0%               | 71.20 ± 4.90              |            62.4  | 0.0622s ± 0.0106s       |
| Medium (N=25) | 4. AI Execution Planner (Reconciled) | 100.0%             | 0.00 ± 0.00               |             0    | 0.1463s ± 0.0581s       |
| Large (N=50)  | 1. Deterministic Topo (No LLM)       | 100.0%             | 0.00 ± 0.00               |             0    | 0.0268s ± 0.0063s       |
| Large (N=50)  | 2. Baseline LLM (Control)            | 0.0%               | 150.10 ± 6.82             |           121.21 | 0.0817s ± 0.0608s       |
| Large (N=50)  | 3. Lattica Single-Agent              | 0.0%               | 150.10 ± 6.82             |           121.21 | 0.0513s ± 0.0159s       |
| Large (N=50)  | 4. AI Execution Planner (Reconciled) | 100.0%             | 0.00 ± 0.00               |             0    | 0.1533s ± 0.1427s       |
