import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent import compute_deterministic_topo_plan

class TestCycleDetection(unittest.TestCase):
    def test_acyclic_dag_ordering(self):
        nodes = ["gateway", "api", "db"]
        edges = [("gateway", "api"), ("api", "db")]
        plan = compute_deterministic_topo_plan(nodes, edges)
        
        # DB (leaf) must be in Phase 1, Gateway in Phase 3
        self.assertIn("db", plan["Phase 1"])
        self.assertIn("api", plan["Phase 2"])
        self.assertIn("gateway", plan["Phase 3"])

    def test_cycle_fallback(self):
        # Graph with cyclic dependency: A -> B -> C -> A
        nodes = ["service-a", "service-b", "service-c"]
        edges = [("service-a", "service-b"), ("service-b", "service-c"), ("service-c", "service-a")]
        
        # Should execute cleanly without recursion error or infinite loop
        plan = compute_deterministic_topo_plan(nodes, edges)
        all_planned = []
        for phase_nodes in plan.values():
            all_planned.extend(phase_nodes)
            
        self.assertEqual(set(all_planned), set(nodes))

if __name__ == "__main__":
    unittest.main()
