#!/usr/bin/env python3
"""Run responsibility-owned deterministic tests; empty suites/skips fail."""
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parent.parent
RECIPE_TESTS = {"test_consumer_authority.py", "test_dispatch_safety.py",
                "test_entrypoint_recipe.py", "test_layer_routing_recipe.py"}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("Catalog", "Tooling"):
        raise SystemExit("usage: run_tests.py Catalog|Tooling")
    layer = sys.argv[1]
    suite = unittest.TestSuite()
    if layer == "Catalog":
        suite.addTests(unittest.TestLoader().discover(
            str(ROOT / "skills/repo/code-review/scripts"), pattern="test_discover_review_context.py"))
    for path in sorted((ROOT / "scripts/tests").glob("test_*.py")):
        if (path.name in RECIPE_TESTS) == (layer == "Catalog"):
            suite.addTests(unittest.TestLoader().discover(str(path.parent), pattern=path.name))
    if not suite.countTestCases():
        raise SystemExit("no tests selected for " + layer)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.skipped:
        print("selected tests skipped; verification is incomplete", file=sys.stderr)
    return 0 if result.wasSuccessful() and not result.skipped else 1


if __name__ == "__main__":
    raise SystemExit(main())
