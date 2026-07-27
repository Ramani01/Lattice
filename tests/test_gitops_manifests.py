import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gitops_pipeline import generate_destination_rule, generate_virtual_service

class TestGitOpsManifests(unittest.TestCase):
    def test_destination_rule_generation(self):
        yaml_output = generate_destination_rule("auth-service", "Transition", "production")
        self.assertIn("kind: DestinationRule", yaml_output)
        self.assertIn("name: auth-service", yaml_output)
        self.assertIn("namespace: production", yaml_output)

    def test_virtual_service_traffic_mirroring(self):
        yaml_output = generate_virtual_service("payment-service", "Transition", "production")
        self.assertIn("kind: VirtualService", yaml_output)
        self.assertIn("mirror:", yaml_output)
        self.assertIn("host: payment-service", yaml_output)

if __name__ == "__main__":
    unittest.main()
