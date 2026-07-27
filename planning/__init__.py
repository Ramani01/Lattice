"""
Lattice Planning Package
Contains deterministic DAG planner, Tarjan SCC cycle condensation, LLM enricher, and master reconciler.
"""
from agent import (
    compute_deterministic_topo_plan,
    compute_scc_condensation,
    enrich_plan_with_llm,
    create_provenance_edge,
    run_agent,
    label_propagation_partition
)

__all__ = [
    "compute_deterministic_topo_plan",
    "compute_scc_condensation",
    "enrich_plan_with_llm",
    "create_provenance_edge",
    "run_agent",
    "label_propagation_partition"
]
