import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent import compute_scc_condensation, compute_deterministic_topo_plan, create_provenance_edge

class TestSCCAndProvenance(unittest.TestCase):
    def test_edge_provenance_structure(self):
        edge = create_provenance_edge("service-a", "service-b", source="eBPF", confidence=1.0, namespace="production")
        self.assertEqual(edge["caller"], "service-a")
        self.assertEqual(edge["callee"], "service-b")
        self.assertEqual(edge["source"], "eBPF")
        self.assertEqual(edge["confidence"], 1.0)
        self.assertEqual(edge["namespace"], "production")
        self.assertIn("T", edge["observed_time"])

    def test_tarjan_scc_cyclic_condensation(self):
        # Cyclic service loop: A -> B -> C -> A
        # Plus downstream DB: C -> DB
        nodes = ["service-a", "service-b", "service-c", "database"]
        edges = [
            ("service-a", "service-b"),
            ("service-b", "service-c"),
            ("service-c", "service-a"),
            ("service-c", "database")
        ]

        sccs, condensed_edges = compute_scc_condensation(nodes, edges)

        # There should be 2 SCCs: [database] and [service-a, service-b, service-c]
        self.assertEqual(len(sccs), 2)
        
        # Test deterministic topological plan on cyclic graph
        plan = compute_deterministic_topo_plan(nodes, edges)

        # Database must be scheduled in Phase 1
        self.assertIn("database", plan["Phase 1"])

        # All 3 cyclic services (a, b, c) must be scheduled in the SAME phase (Phase 2)
        phase2_svcs = set(plan["Phase 2"])
        self.assertIn("service-a", phase2_svcs)
        self.assertIn("service-b", phase2_svcs)
        self.assertIn("service-c", phase2_svcs)

if __name__ == "__main__":
    unittest.main()
