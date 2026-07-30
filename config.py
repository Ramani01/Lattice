"""
Lattice Enterprise Configuration System
Centralized, environment-aware configuration for Neo4j, default file locations, and logging.
"""

import os
from dataclasses import dataclass

@dataclass
class LatticeConfig:
    # Neo4j Settings
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password")

    # File Paths
    inventory_file: str = os.getenv("LATTICE_INVENTORY_FILE", "inventory.json")
    analyzed_inventory_file: str = os.getenv("LATTICE_ANALYZED_INVENTORY_FILE", "analyzed_inventory.json")
    evaluation_results_file: str = os.getenv("LATTICE_EVALUATION_RESULTS_FILE", "evaluation_results.json")

    # Logging & Runtime
    log_level: str = os.getenv("LATTICE_LOG_LEVEL", "INFO")
    timeout_seconds: int = int(os.getenv("LATTICE_TIMEOUT_SECONDS", "15"))

config = LatticeConfig()
