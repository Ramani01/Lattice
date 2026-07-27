import unittest
import sys
import os

# Discover and run all test modules in tests/
if __name__ == "__main__":
    test_dir = os.path.dirname(__file__)
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n==================================================")
        print("ALL TESTS PASSED SUCCESSFULLY! (100% SUITE VERIFIED)")
        print("==================================================")
        sys.exit(0)
    else:
        print("\n==================================================")
        print("SOME TESTS FAILED. PLEASE REVIEW LOG OUTPUT.")
        print("==================================================")
        sys.exit(1)
