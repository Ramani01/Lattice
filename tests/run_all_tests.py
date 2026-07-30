import unittest
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Discover and run all test modules in tests/
if __name__ == "__main__":
    test_dir = os.path.dirname(__file__)
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n==================================================")
        print(f"ALL {result.testsRun} TESTS PASSED SUCCESSFULLY! (100% SUITE VERIFIED)")
        print("==================================================")
        sys.exit(0)
    else:
        print("\n==================================================")
        print(f"SOME TESTS FAILED ({len(result.failures)} failures, {len(result.errors)} errors). PLEASE REVIEW LOG OUTPUT.")
        print("==================================================")
        sys.exit(1)
