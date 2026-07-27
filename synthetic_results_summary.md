# 30-DAG Statistical Generalization Benchmark Results

| Graph Scale   | Planning Strategy                    | Success Rate (%)   | Mean Conflicts (95% CI)   |   Variance (Var) | Mean Latency (95% CI)   |
|---------------|--------------------------------------|--------------------|---------------------------|------------------|-------------------------|
| Small (N=10)  | 1. Deterministic Topo (No LLM)       | 100.0%             | 0.00 ± 0.00               |             0    | 0.0393s ± 0.0345s       |
| Small (N=10)  | 2. Baseline LLM (Control)            | 0.0%               | 21.00 ± 1.82              |             8.67 | 0.0662s ± 0.0553s       |
| Small (N=10)  | 3. Lattica Single-Agent              | 0.0%               | 21.00 ± 1.82              |             8.67 | 0.0544s ± 0.0205s       |
| Small (N=10)  | 4. AI Execution Planner (Reconciled) | 100.0%             | 0.00 ± 0.00               |             0    | 0.0642s ± 0.0194s       |
| Medium (N=25) | 1. Deterministic Topo (No LLM)       | 100.0%             | 0.00 ± 0.00               |             0    | 0.0286s ± 0.0121s       |
| Medium (N=25) | 2. Baseline LLM (Control)            | 0.0%               | 71.20 ± 4.90              |            62.4  | 0.0366s ± 0.0059s       |
| Medium (N=25) | 3. Lattica Single-Agent              | 0.0%               | 71.20 ± 4.90              |            62.4  | 0.0424s ± 0.0135s       |
| Medium (N=25) | 4. AI Execution Planner (Reconciled) | 100.0%             | 0.00 ± 0.00               |             0    | 0.0498s ± 0.0141s       |
| Large (N=50)  | 1. Deterministic Topo (No LLM)       | 100.0%             | 0.00 ± 0.00               |             0    | 0.0240s ± 0.0019s       |
| Large (N=50)  | 2. Baseline LLM (Control)            | 0.0%               | 150.10 ± 6.82             |           121.21 | 0.0408s ± 0.0056s       |
| Large (N=50)  | 3. Lattica Single-Agent              | 0.0%               | 150.10 ± 6.82             |           121.21 | 0.0375s ± 0.0060s       |
| Large (N=50)  | 4. AI Execution Planner (Reconciled) | 100.0%             | 0.00 ± 0.00               |             0    | 0.0567s ± 0.0194s       |
