"""Integration negatives run the unmodified published checker against scratch trees."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTEXT = ROOT / ".shared-ci/scripts/context/_context.py"


def fixture_environment():
    names = subprocess.check_output(["git", "rev-parse", "--local-env-vars"], text=True).splitlines()
    return {**{key: value for key, value in os.environ.items() if key not in names},
            "PYTHONDONTWRITEBYTECODE": "1"}


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.env = fixture_environment()
        self.assertTrue(CONTEXT.is_file(), "scripts/verify must fetch the pinned checker first")
        self.scratch = tempfile.TemporaryDirectory(prefix="repo-contract-")
        self.addCleanup(self.scratch.cleanup)
        self.repo = Path(self.scratch.name)
        tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT, env=self.env).decode().split("\0")
        for relative in filter(None, tracked):
            source = ROOT / relative
            if source.is_file():
                target = self.repo / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True, env=self.env)
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True, env=self.env)

    def audit(self):
        return subprocess.run(["python3", str(CONTEXT), "audit"], cwd=self.repo,
                              text=True, capture_output=True, env=self.env)

    def test_valid_repository_has_no_findings(self):
        result = self.audit()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_non_sha_protocol_pointer_fails(self):
        agents = self.repo / "AGENTS.md"
        original = agents.read_text()
        text = original.replace("/blob/761fe6b0b3ca5e2c57d244182d495ab8041851fa/ai/agent-protocol.md", "/blob/main/ai/agent-protocol.md")
        self.assertNotEqual(text, original, "the protocol link must actually be mutated")
        agents.write_text(text)
        result = self.audit()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("contract_agents", result.stdout + result.stderr)
        self.assertIn("not a full 40-char SHA", result.stdout + result.stderr)

    def test_non_executable_hook_fails(self):
        hook = self.repo / ".githooks/pre-push"
        hook.chmod(0o644)
        subprocess.run(["git", "add", ".githooks/pre-push"], cwd=self.repo, check=True, env=self.env)
        result = self.audit()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("contract_verify", result.stdout + result.stderr)

    def test_identity_scanner_covers_support_docs(self):
        bad = self.repo / "docs/synthetic-private.md"
        bad.write_text("/User" + "s/example/private\n")
        subprocess.run(["git", "add", "docs/synthetic-private.md"], cwd=self.repo, check=True, env=self.env)
        result = self.audit()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("contract_identity", result.stdout + result.stderr)

    def test_unmapped_executable_fails(self):
        (self.repo / "unmapped.py").write_text("print('synthetic')\n")
        subprocess.run(["git", "add", "unmapped.py"], cwd=self.repo, check=True, env=self.env)
        result = self.audit()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unmapped_path", result.stdout + result.stderr)

    def test_actual_lockfile_observation_still_requires_dependency_metadata(self):
        lockfile = self.repo / "docs/fixture/Package.resolved"
        lockfile.parent.mkdir(parents=True)
        lockfile.write_text(json.dumps({"version": 2, "pins": [{"identity": "shared-telemetry",
                            "state": {"version": "1.0.0", "revision": "a" * 40}}]}))
        subprocess.run(["git", "add", "docs/fixture/Package.resolved"], cwd=self.repo, check=True, env=self.env)
        result = self.audit()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("contract_dependencies", result.stdout + result.stderr)
        self.assertIn("shared-telemetry is pinned", result.stdout + result.stderr)

    def test_proposal_preserves_existing_requirement_and_has_no_bypass(self):
        proposal = json.loads((self.repo / "policy/main-protection.proposed.json").read_text())
        self.assertEqual(proposal["bypass_actors"], [])
        rules = {rule["type"]: rule.get("parameters", {}) for rule in proposal["rules"]}
        self.assertIn("deletion", rules)
        self.assertIn("non_fast_forward", rules)
        for field in ("require_code_owner_review", "dismiss_stale_reviews_on_push",
                      "require_extra_approval_for_unattributed_changes"):
            self.assertTrue(rules["pull_request"][field])
        self.assertEqual({item["context"] for item in rules["required_status_checks"]["required_status_checks"]},
                         {"quality / aggregate", "codex-review-target / codex-review", "validate"})


class VerifyEntryTests(unittest.TestCase):
    def setUp(self):
        self.env = fixture_environment()
        self.scratch = tempfile.TemporaryDirectory(prefix="verify-entry-")
        self.addCleanup(self.scratch.cleanup)
        self.repo = Path(self.scratch.name)
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True, env=self.env)
        (self.repo / "AGENTS.md").write_text((ROOT / "AGENTS.md").read_text())
        for relative in ("scripts/check_entrypoint.py", ".github/workflows/ci.yml"):
            target = self.repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True, env=self.env)

    def verify(self, *args):
        return subprocess.run(["bash", str(ROOT / "scripts/verify"), *args], cwd=self.repo,
                              text=True, capture_output=True, env=self.env)

    def test_unknown_argument_fails_before_network_or_cache(self):
        result = self.verify("--skip-audit")
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.repo / ".shared-ci").exists())

    def test_invalid_cache_is_preserved(self):
        cache = self.repo / ".shared-ci"
        cache.mkdir()
        marker = cache / "unsaved.txt"
        marker.write_text("keep me\n")
        result = self.verify("--all")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("preserved", result.stderr)
        self.assertEqual(marker.read_text(), "keep me\n")

    def test_dangling_cache_symlink_is_not_followed(self):
        target = self.repo / "must-not-create"
        (self.repo / ".shared-ci").symlink_to(target, target_is_directory=True)
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
