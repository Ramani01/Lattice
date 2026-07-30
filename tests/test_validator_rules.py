import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from planning import validate_plan

class TestValidatorRules(unittest.TestCase):
    def setUp(self):
        self.inventory = [
            {"name": "gateway"},
            {"name": "api"},
            {"name": "db"}
        ]
        self.dependencies = [
            ("gateway", "api"),
            ("api", "db")
        ]

    def test_valid_plan_passes(self):
        valid_plan = {
            "Phase 1": ["db"],
            "Phase 2": ["api"],
            "Phase 3": ["gateway"]
        }
        is_valid, conflicts = validate_plan(valid_plan, self.dependencies, self.inventory)
        self.assertTrue(is_valid)
        self.assertEqual(len(conflicts), 0)

    def test_inverted_dependency_fails(self):
        invalid_plan = {
            "Phase 1": ["gateway"],
            "Phase 2": ["api"],
            "Phase 3": ["db"]
        }
        is_valid, conflicts = validate_plan(invalid_plan, self.dependencies, self.inventory)
        self.assertFalse(is_valid)
        self.assertGreater(len(conflicts), 0)
        self.assertTrue(any("Dependency Conflict" in c for c in conflicts))

    def test_missing_service_fails(self):
        incomplete_plan = {
            "Phase 1": ["db"],
            "Phase 2": ["api"]
        }
        is_valid, conflicts = validate_plan(incomplete_plan, self.dependencies, self.inventory)
        self.assertFalse(is_valid)
        self.assertTrue(any("Missing service 'gateway'" in c for c in conflicts))

if __name__ == "__main__":
    unittest.main()
