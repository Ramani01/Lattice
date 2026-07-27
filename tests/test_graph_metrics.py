import unittest
import sys
import os

# Ensure workspace root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dynamic_discovery import calculate_pagerank, calculate_betweenness_centrality

class TestGraphMetrics(unittest.TestCase):
    def setUp(self):
        self.nodes = ["auth-service", "payment-service", "order-service", "edge-gateway", "user-db", "order-db", "payment-db"]
        self.edges = [
            ("edge-gateway", "auth-service"),
            ("edge-gateway", "order-service"),
            ("auth-service", "user-db"),
            ("order-service", "order-db"),
            ("order-service", "payment-service"),
            ("payment-service", "payment-db")
        ]

    def test_pagerank_sum_to_one(self):
        pr = calculate_pagerank(self.nodes, self.edges)
        self.assertEqual(len(pr), len(self.nodes))
        total_pr = sum(pr.values())
        self.assertAlmostEqual(total_pr, 1.0, places=4)

    def test_betweenness_centrality_keys(self):
        bc = calculate_betweenness_centrality(self.nodes, self.edges)
        self.assertEqual(len(bc), len(self.nodes))
        for node in self.nodes:
            self.assertIn(node, bc)
            self.assertGreaterEqual(bc[node], 0.0)

    def test_empty_graph(self):
        pr = calculate_pagerank([], [])
        self.assertEqual(pr, {})
        bc = calculate_betweenness_centrality([], [])
        self.assertEqual(bc, {})

if __name__ == "__main__":
    unittest.main()
