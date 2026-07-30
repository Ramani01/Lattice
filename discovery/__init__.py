"""
Lattice Discovery Package
Contains dynamic infrastructure and codebase discovery providers.
"""

from dynamic_discovery import (
    DiscoveryProvider,
    DockerComposeProvider,
    EbpfLogsProvider,
    KialiIstioProvider,
    DatadogApmProvider,
    run_ingestion_and_analysis
)

__all__ = [
    "DiscoveryProvider",
    "DockerComposeProvider",
    "EbpfLogsProvider",
    "KialiIstioProvider",
    "DatadogApmProvider",
    "run_ingestion_and_analysis"
]
