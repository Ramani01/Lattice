import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Test imports from clean package exports
import config
import exceptions
from graph import calculate_pagerank, calculate_betweenness_centrality, run_dynamic_discovery
from discovery import DiscoveryProvider, DockerComposeProvider
from planning import compute_scc_condensation, compute_deterministic_topo_plan, create_provenance_edge
from gitops import generate_destination_rule, generate_virtual_service
from utils import fetch_vault_secrets

class TestEnterpriseIntegrationPipeline(unittest.TestCase):

    def test_package_exports_and_aliases(self):
        """Verify all package facade __init__.py exports and backward compatibility aliases."""
        self.assertTrue(callable(calculate_pagerank))
        self.assertTrue(callable(calculate_betweenness_centrality))
        self.assertTrue(callable(run_dynamic_discovery))
        self.assertTrue(issubclass(exceptions.LatticeError, Exception))
        self.assertIsNotNone(config.config.neo4j_uri)

    def test_end_to_end_planning_pipeline(self):
        """Test full pipeline: graph metrics -> Tarjan SCC -> topo plan -> Istio manifest generation."""
        services = ["auth-service", "payment-service", "order-service", "user-db", "order-db", "payment-db"]
        raw_edges = [
            ("auth-service", "user-db"),
            ("order-service", "order-db"),
            ("order-service", "payment-service"),
            ("payment-service", "payment-db")
        ]

        # 1. Graph Centrality
        pr = calculate_pagerank(services, raw_edges)
        self.assertEqual(len(pr), len(services))
        bc = calculate_betweenness_centrality(services, raw_edges)
        self.assertEqual(len(bc), len(services))

        # 2. Tarjan SCC Condensation (verify 3-tuple return)
        sccs, condensed_edges, cycle_flags = compute_scc_condensation(services, raw_edges)
        self.assertIsInstance(sccs, list)
        self.assertIsInstance(condensed_edges, list)
        self.assertIsInstance(cycle_flags, dict)

        # 3. Deterministic Topological Plan
        plan = compute_deterministic_topo_plan(services, raw_edges)
        self.assertIn("Phase 1", plan)
        self.assertIn("user-db", plan["Phase 1"])

        # 4. Istio GitOps Manifest Generation
        dr = generate_destination_rule("auth-service", "Target", "default")
        self.assertIn("kind: DestinationRule", dr)
        self.assertIn("auth-service", dr)

        vs = generate_virtual_service("auth-service", "Target", "default")
        self.assertIn("kind: VirtualService", vs)
        self.assertIn("auth-service", vs)

if __name__ == "__main__":
    unittest.main()
