"""
Lattice Enterprise Custom Exception Hierarchy
Provides structured domain exceptions for operational failures.
"""

class LatticeError(Exception):
    """Base exception for all Lattice domain errors."""
    pass

class ConfigurationError(LatticeError):
    """Raised when configuration parameters or secrets are invalid or missing."""
    pass

class DiscoveryError(LatticeError):
    """Raised when dynamic infrastructure discovery fails."""
    pass

class GraphAnalysisError(LatticeError):
    """Raised when graph analytics or Neo4j execution fails."""
    pass

class PlanningError(LatticeError):
    """Raised during topological planning, SCC condensation, or reconciliation failures."""
    pass

class GitOpsError(LatticeError):
    """Raised during Istio manifest generation or GitOps integration failures."""
    pass
