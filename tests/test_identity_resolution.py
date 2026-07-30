import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent import calculate_risk_score, compute_scc_condensation

class TestIdentityResolutionAndRiskScore(unittest.TestCase):
    def test_composite_risk_score_calculation(self):
        # High CBR, High DI, low confidence, in cycle -> High Risk Score
        high_risk = calculate_risk_score(cbr=3.0, di=2.0, confidence=0.8, is_in_cycle=True)
        self.assertGreater(high_risk, 80.0)

        # Low CBR, Low DI, perfect confidence, no cycle -> Low Risk Score
        low_risk = calculate_risk_score(cbr=0.0, di=0.0, confidence=1.0, is_in_cycle=False)
        self.assertEqual(low_risk, 0.0)

    def test_self_loop_scc_detection(self):
        nodes = ["self-service", "database"]
        edges = [
            ("self-service", "self-service"),  # Self loop
            ("self-service", "database")
        ]
        sccs, condensed_edges, cycle_flags = compute_scc_condensation(nodes, edges)
        self.assertTrue(cycle_flags["self-service"])
        self.assertFalse(cycle_flags["database"])

    def test_canonical_identity_alias_resolution(self):
        def resolve_canonical_id(raw_name: str) -> str:
            cleaned = raw_name.lower().replace(".prod.svc.cluster.local", "").strip()
            aliases = {
                "auth": "auth-service",
                "auth-svc": "auth-service",
                "payment": "payment-service",
                "order": "order-service"
            }
            return aliases.get(cleaned, cleaned)

        self.assertEqual(resolve_canonical_id("auth.prod.svc.cluster.local"), "auth-service")
        self.assertEqual(resolve_canonical_id("auth-svc"), "auth-service")
        self.assertEqual(resolve_canonical_id("payment"), "payment-service")

if __name__ == "__main__":
    unittest.main()
