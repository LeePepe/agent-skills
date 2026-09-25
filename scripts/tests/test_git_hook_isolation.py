"""Discovery fixtures must not write through a caller's hook-local Git state."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
DISCOVERY_TESTS = ROOT / "skills/repo/code-review/scripts/test_discover_review_context.py"


class DiscoveryIsolationTests(unittest.TestCase):
    def test_existing_four_tests_preserve_outer_repository_under_hook_environment(self):
        with tempfile.TemporaryDirectory(prefix="catalog-hook-discovery-") as directory:
            root = Path(directory).resolve()
            outer = root / "outer"
            outer.mkdir()
            env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "PYTHON"))}
            env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
                       PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(root))

            def git(*args):
                return subprocess.check_output(["git", *args], cwd=outer, env=env)

            git("init", "-q", "-b", "main")
            git("config", "user.name", "Fixture")
            git("config", "user.email", "fixture@example.invalid")
            git("config", "maintenance.auto", "false")
            (outer / "sentinel").write_text("untouched\n")
            git("add", ".")
            git("commit", "-qm", "outer sentinel")

            def snapshot():
                return {"index": (outer / ".git/index").read_bytes(),
                        "config": (outer / ".git/config").read_bytes(),
                        "refs": git("show-ref"), "head": git("rev-parse", "HEAD"),
                        "status": git("status", "--porcelain"),
                        "sentinel": (outer / "sentinel").read_bytes()}

            before = snapshot()
            poisoned = dict(env, GIT_DIR=str(outer / ".git"), GIT_WORK_TREE=str(outer),
                            GIT_INDEX_FILE=str(outer / ".git/index"),
                            GIT_OBJECT_DIRECTORY=str(outer / ".git/objects"),
                            GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="core.worktree",
                            GIT_CONFIG_VALUE_0=str(outer))
            result = subprocess.run([sys.executable, "-B", str(DISCOVERY_TESTS), "-v"],
                                    cwd=outer, env=poisoned, capture_output=True,
                                    text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Ran 4 tests", result.stderr)
            self.assertEqual(snapshot(), before)


if __name__ == "__main__":
    unittest.main()
