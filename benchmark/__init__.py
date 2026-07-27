"""
Lattice Benchmark Package
Contains 30-DAG statistical generalization suite and visualization plot generators.
"""
from synthetic_benchmark import (
    generate_synthetic_dag,
    compute_stats,
    run_synthetic_benchmark,
    plot_synthetic_rigor_chart
)

__all__ = [
    "generate_synthetic_dag",
    "compute_stats",
    "run_synthetic_benchmark",
    "plot_synthetic_rigor_chart"
]
