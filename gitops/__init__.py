"""
Lattice GitOps Package
Contains Istio traffic-shadowing manifest generators, configuration updater, and GitHub REST API integration.
"""
from gitops_pipeline import (
    generate_destination_rule,
    generate_virtual_service,
    update_local_config_file,
    create_github_pull_request,
    generate_gitops_pipeline
)

# Backward-compatibility alias
update_service_config = update_local_config_file

__all__ = [
    "generate_destination_rule",
    "generate_virtual_service",
    "update_local_config_file",
    "update_service_config",
    "create_github_pull_request",
    "generate_gitops_pipeline"
]
