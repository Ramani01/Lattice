import os
import json
import time
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from tabulate import tabulate
from agent import run_agent

# Artifact directory calculation
CONV_ID = os.environ.get("CONVERSATION_ID")
if CONV_ID:
    ARTIFACT_DIR = os.path.join(r"C:\Users\hp\.gemini\antigravity-ide\brain", CONV_ID)
else:
    brain_dir = r"C:\Users\hp\.gemini\antigravity-ide\brain"
    if os.path.exists(brain_dir):
        subdirs = [os.path.join(brain_dir, d) for d in os.listdir(brain_dir) if os.path.isdir(os.path.join(brain_dir, d))]
        ARTIFACT_DIR = max(subdirs, key=os.path.getmtime) if subdirs else "."
    else:
        ARTIFACT_DIR = "."

def generate_synthetic_dag(num_nodes: int, edge_prob: float, seed: int) -> tuple:
    """
    Generates a directed acyclic graph (DAG) representing microservice architecture dependencies.
    Returns (nodes, edges, inventory)
    """
    np.random.seed(seed)
    node_names = [f"service-{i+1}" for i in range(num_nodes)]
    
    edges = []
    # Topological lower triangular ordering guarantees valid DAG
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            if np.random.rand() < edge_prob:
                edges.append((node_names[i], node_names[j])) # caller -> callee
                
    algorithms = ["RSA-2048", "RSA-4096", "ECC-secp256r1", "AES-256-GCM"]
    
    out_deg = {n: 0 for n in node_names}
    in_deg = {n: 0 for n in node_names}
    for u, v in edges:
        out_deg[u] += 1
        in_deg[v] += 1
        
    inventory = []
    for i, name in enumerate(node_names):
        algo = algorithms[i % len(algorithms)]
        is_vuln = algo != "AES-256-GCM"
        inventory.append({
            "service": name,
            "algorithm": algo,
            "vulnerable": is_vuln,
            "change_blast_radius": out_deg[name],
            "dependency_impact": in_deg[name],
            "pagerank": round(1.0 / num_nodes, 4),
            "betweenness_centrality": 0.05
        })
        
    return node_names, edges, inventory

def compute_stats(values: list) -> dict:
    """Computes mean, variance, std dev, and 95% confidence interval."""
    if not values:
        return {"mean": 0.0, "var": 0.0, "std": 0.0, "ci_95": 0.0}
    n = len(values)
    mean = float(np.mean(values))
    var = float(np.var(values, ddof=1)) if n > 1 else 0.0
    std = float(np.std(values, ddof=1)) if n > 1 else 0.0
    # 95% Confidence Interval using t-distribution multiplier ~ 1.96
    ci_95 = 1.96 * (std / math.sqrt(n)) if n > 1 else 0.0
    return {
        "mean": mean,
        "var": var,
        "std": std,
        "ci_95": ci_95
    }

def run_synthetic_benchmark(total_dags: int = 30):
    """
    Executes the 30-DAG statistical generalization benchmark across 3 graph scales:
    - Small DAGs (N=10 nodes): 10 DAGs
    - Medium DAGs (N=25 nodes): 10 DAGs
    - Large Enterprise DAGs (N=50 nodes): 10 DAGs
    """
    print(f"=" * 80)
    print(f"STARTING 30-DAG STATISTICAL GENERALIZATION BENCHMARK SUITE")
    print(f"=" * 80)
    
    scales = [
        {"name": "Small (N=10)", "nodes": 10, "prob": 0.25, "count": 10},
        {"name": "Medium (N=25)", "nodes": 25, "prob": 0.15, "count": 10},
        {"name": "Large (N=50)", "nodes": 50, "prob": 0.08, "count": 10}
    ]
    
    modes = ["deterministic_topo", "baseline", "lattica", "federated_hybrid"]
    mode_labels = {
        "deterministic_topo": "1. Deterministic Topo (No LLM)",
        "baseline": "2. Baseline LLM (Control)",
        "lattica": "3. Lattica Single-Agent",
        "federated_hybrid": "4. AI Execution Planner (Reconciled)"
    }
    
    raw_results = {scale["name"]: {m: [] for m in modes} for scale in scales}
    all_dag_summary = []
    
    global_seed = 42
    
    for scale in scales:
        scale_name = scale["name"]
        n_nodes = scale["nodes"]
        prob = scale["prob"]
        count = scale["count"]
        
        print(f"\n>>> Benchmarking Scale: {scale_name} ({count} DAGs, N={n_nodes}, p={prob}) <<<")
        
        for i in range(count):
            seed = global_seed + i
            nodes, edges, inventory = generate_synthetic_dag(n_nodes, prob, seed)
            
            state = {
                "inventory": inventory,
                "dependencies": edges,
                "domain_partition": {},
                "boundary_edges": []
            }
            
            for m in modes:
                t0 = time.time()
                # Run mode evaluation with state injection
                res = run_agent(m, inject_state=state)
                elapsed = time.time() - t0
                
                conflicts_count = len(res["conflicts"])
                is_valid = res["is_valid"]
                
                raw_results[scale_name][m].append({
                    "dag_id": f"{scale_name}_DAG_{i+1}",
                    "nodes": n_nodes,
                    "edges": len(edges),
                    "is_valid": is_valid,
                    "conflicts_count": conflicts_count,
                    "latency": elapsed
                })
                
            print(f"  Processed {scale_name} DAG {i+1}/{count} ({len(edges)} edges)")
            
    # Compute Statistical Summaries per Scale
    stats_summary = {}
    table_rows = []
    
    for scale in scales:
        scale_name = scale["name"]
        stats_summary[scale_name] = {}
        
        for m in modes:
            runs = raw_results[scale_name][m]
            conflicts_list = [r["conflicts_count"] for r in runs]
            latency_list = [r["latency"] for r in runs]
            success_count = sum(1 for r in runs if r["is_valid"])
            success_rate = (success_count / len(runs)) * 100.0
            
            c_stats = compute_stats(conflicts_list)
            l_stats = compute_stats(latency_list)
            
            stats_summary[scale_name][m] = {
                "success_rate": success_rate,
                "conflict_stats": c_stats,
                "latency_stats": l_stats
            }
            
            table_rows.append([
                scale_name,
                mode_labels[m],
                f"{success_rate:.1f}%",
                f"{c_stats['mean']:.2f} ± {c_stats['ci_95']:.2f}",
                f"{c_stats['var']:.2f}",
                f"{l_stats['mean']:.4f}s ± {l_stats['ci_95']:.4f}s"
            ])
            
    # Output Raw JSON Dataset
    with open("synthetic_evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(raw_results, f, indent=4)
        
    # Output Markdown Table
    headers = ["Graph Scale", "Planning Strategy", "Success Rate (%)", "Mean Conflicts (95% CI)", "Variance (Var)", "Mean Latency (95% CI)"]
    summary_md = tabulate(table_rows, headers=headers, tablefmt="github")
    
    with open("synthetic_results_summary.md", "w", encoding="utf-8") as f:
        f.write("# 30-DAG Statistical Generalization Benchmark Results\n\n")
        f.write(summary_md + "\n")
        
    print("\n" + "=" * 80)
    print("30-DAG STATISTICAL GENERALIZATION RESULTS SUMMARY")
    print("=" * 80)
    print(tabulate(table_rows, headers=headers, tablefmt="grid"))
    
    # Generate 4-Panel Publication Chart: synthetic_statistical_rigor.png
    plot_synthetic_rigor_chart(stats_summary, scales, modes, mode_labels)
    
    return stats_summary

def plot_synthetic_rigor_chart(stats_summary: dict, scales: list, modes: list, mode_labels: dict):
    """Generates a 4-panel publication plot detailing statistical rigor across DAG scales."""
    try:
        plt.style.use('dark_background')
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        scale_names = [s["name"] for s in scales]
        colors = {'deterministic_topo': '#8B5CF6', 'baseline': '#EF4444', 'lattica': '#3B82F6', 'federated_hybrid': '#10B981'}
        
        # Subplot A: Success Rate (%) vs Graph Scale
        ax_a = axes[0, 0]
        x = np.arange(len(scale_names))
        width = 0.2
        for idx, m in enumerate(modes):
            rates = [stats_summary[sn][m]["success_rate"] for sn in scale_names]
            ax_a.bar(x + (idx - 1.5) * width, rates, width, label=mode_labels[m].split('.')[1].strip(), color=colors[m], edgecolor='white', linewidth=0.5)
        ax_a.set_ylabel('Success Rate (%)', fontweight='bold', color='white')
        ax_a.set_title('A. Success Rate across Graph Scales (Higher is Better)', fontweight='bold', color='white')
        ax_a.set_xticks(x)
        ax_a.set_xticklabels(scale_names, fontweight='bold', color='white')
        ax_a.set_ylim(0, 115)
        ax_a.legend(fontsize=8, facecolor='#1E293B')

        # Subplot B: Mean Conflicts with 95% Confidence Intervals
        ax_b = axes[0, 1]
        for idx, m in enumerate(modes):
            means = [stats_summary[sn][m]["conflict_stats"]["mean"] for sn in scale_names]
            cis = [stats_summary[sn][m]["conflict_stats"]["ci_95"] for sn in scale_names]
            ax_b.errorbar(x + (idx - 1.5) * width, means, yerr=cis, fmt='o-', color=colors[m], label=mode_labels[m].split('.')[1].strip(), capsize=4, linewidth=2)
        ax_b.set_ylabel('Mean Conflicts (95% CI)', fontweight='bold', color='white')
        ax_b.set_title('B. Conflict Spreads & 95% CI (Lower is Better)', fontweight='bold', color='white')
        ax_b.set_xticks(x)
        ax_b.set_xticklabels(scale_names, fontweight='bold', color='white')
        ax_b.legend(fontsize=8, facecolor='#1E293B')
        ax_b.grid(True, linestyle=':', alpha=0.3)

        # Subplot C: Mean Latency Scaling (Log Scale)
        ax_c = axes[1, 0]
        for idx, m in enumerate(modes):
            latencies = [max(stats_summary[sn][m]["latency_stats"]["mean"], 0.0001) for sn in scale_names]
            ax_c.plot(scale_names, latencies, 'o-', color=colors[m], label=mode_labels[m].split('.')[1].strip(), linewidth=2)
        ax_c.set_yscale('log')
        ax_c.set_ylabel('Avg Latency (seconds, Log Scale)', fontweight='bold', color='white')
        ax_c.set_title('C. Latency Scaling vs Graph Size (Lower is Better)', fontweight='bold', color='white')
        ax_c.legend(fontsize=8, facecolor='#1E293B')
        ax_c.grid(True, linestyle=':', alpha=0.3)

        # Subplot D: Conflict Variance (σ²) Stability
        ax_d = axes[1, 1]
        for idx, m in enumerate(modes):
            vars_list = [stats_summary[sn][m]["conflict_stats"]["var"] for sn in scale_names]
            ax_d.bar(x + (idx - 1.5) * width, vars_list, width, label=mode_labels[m].split('.')[1].strip(), color=colors[m], edgecolor='white', linewidth=0.5)
        ax_d.set_ylabel('Conflict Variance (σ²)', fontweight='bold', color='white')
        ax_d.set_title('D. Variance & Stability Index (Lower is Better)', fontweight='bold', color='white')
        ax_d.set_xticks(x)
        ax_d.set_xticklabels(scale_names, fontweight='bold', color='white')
        ax_d.legend(fontsize=8, facecolor='#1E293B')

        plt.suptitle('Lattica 30-DAG Statistical Generalization Benchmark Suite (N=10, 25, 50)', fontsize=15, fontweight='bold', color='white', y=0.98)
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        plot_local_path = "synthetic_statistical_rigor.png"
        plt.savefig(plot_local_path, dpi=150)
        plt.close(fig)
        print(f"Chart saved locally as '{plot_local_path}'")
        
        if os.path.exists(ARTIFACT_DIR):
            import shutil
            shutil.copy(plot_local_path, os.path.join(ARTIFACT_DIR, plot_local_path))
            print(f"Chart copied to artifact directory at: {os.path.join(ARTIFACT_DIR, plot_local_path)}")
            
    except Exception as e:
        print(f"Failed to generate synthetic plot: {e}")

if __name__ == "__main__":
    run_synthetic_benchmark(total_dags=30)
