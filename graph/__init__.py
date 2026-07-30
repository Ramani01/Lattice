"""
Lattice Graph Package
Contains graph analytics, PageRank, Betweenness Centrality, and Neo4j connection utilities.
"""

from dynamic_discovery import (
    calculate_pagerank,
    calculate_betweenness_centrality,
    run_ingestion_and_analysis
)

# Backward-compatibility alias for package export
run_dynamic_discovery = run_ingestion_and_analysis

__all__ = [
    "calculate_pagerank",
    "calculate_betweenness_centrality",
    "run_ingestion_and_analysis",
    "run_dynamic_discovery"
]
