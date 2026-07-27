import unittest
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dynamic_discovery import EbpfLogsProvider, DockerComposeProvider

class TestDiscoveryParsers(unittest.TestCase):
    def setUp(self):
        self.ebpf_log_path = "test_ebpf_temp.jsonl"
        with open(self.ebpf_log_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"src_service": "service-a", "dst_service": "service-b"}) + "\n")
            f.write(json.dumps({"caller": "service-b", "callee": "service-c"}) + "\n")

    def tearDown(self):
        if os.path.exists(self.ebpf_log_path):
            os.remove(self.ebpf_log_path)

    def test_ebpf_parser(self):
        provider = EbpfLogsProvider(self.ebpf_log_path)
        nodes, edges = provider.fetch_nodes_and_edges()
        self.assertIn("service-a", nodes)
        self.assertIn("service-b", nodes)
        self.assertIn("service-c", nodes)
        self.assertIn(("service-a", "service-b"), edges)
        self.assertIn(("service-b", "service-c"), edges)

    def test_docker_compose_parser(self):
        dc_path = "docker-compose.yml"
        if os.path.exists(dc_path):
            provider = DockerComposeProvider(dc_path)
            nodes, edges = provider.fetch_nodes_and_edges()
            self.assertIsInstance(nodes, list)
            self.assertIsInstance(edges, list)

if __name__ == "__main__":
    unittest.main()
