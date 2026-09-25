"""Recipe guards, not agent evaluation. Optional real-provider CLI probes.

Set SHARED_CI_SOURCE to a trusted checkout of the exact provider version being
evaluated. These tests only call resolve/field against disposable caller maps;
they never execute registry fixtures or declared gates.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills/repo/layered-ci-autofix"
PROVIDER = os.environ.get("SHARED_CI_SOURCE")


class RecipeGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = (SKILL / "SKILL.md").read_text()
        cls.contract = (SKILL / "references/signal-contract.md").read_text()
        cls.evals = (SKILL / "references/eval-cases.md").read_text()

    def test_directory_not_embedded_heading_probe(self):
        self.assertNotIn("grep -q 'Layer", self.recipe)
        self.assertIn("AGENTS.md", self.contract)
        self.assertIn("目录", self.contract)

    def test_no_directory_ownership_guess_or_widening(self):
        for stale in ("best_len", "<layer-glob>", "__toplevel__",
                      "顶层代码没有 layer", "整仓库级修复"):
            self.assertNotIn(stale, self.recipe + self.contract)
        self.assertIn("owns", self.contract)
        self.assertIn("test_paths", self.contract)

    def test_provider_schema_and_version_are_explicit(self):
        for term in ("classification", "excluded", "context", "chain", "reason",
                     "CONTEXT.md", "选定版本", "support"):
            self.assertIn(term, self.contract)

    def test_signal_cannot_grant_owner_or_relax_constraints(self):
        self.assertIn("不能覆盖", self.contract)
        self.assertIn("停止自动写入", self.contract)
        self.assertIn("required", self.contract)

    def test_evaluations_cover_route_edges_and_limits(self):
        for term in ("N5", "N6", "N7", "N8", "CLI", "不等于真实 agent"):
            self.assertIn(term, self.evals)
        self.assertNotIn("verify 命令 == 该 layer", self.evals)
        self.assertNotIn("修完只跑", self.recipe)


@unittest.skipUnless(PROVIDER, "set SHARED_CI_SOURCE for exact-provider CLI evidence")
class ProviderRoutes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="layer-routing-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                        PYTHONDONTWRITEBYTECODE="1")
        subprocess.run(["git", "init", "-q", "--template="], cwd=self.root,
                       env=self.env, check=True, timeout=10)
        self.write("AGENTS.md", "# Directory\n\n- Ownership → [map](docs/architecture/tech-context.md) — when locating failures.\n")
        self.simplified()

    def write(self, path, content):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    def document(self, path, metadata, body=""):
        self.write(path, "---\n" + json.dumps(metadata) + "\n---\n" + body)

    def simplified(self, owns=None):
        self.document("docs/architecture/tech-context.md",
                      {"support": [{"patterns": ["README.md"], "reason": "repository prose"}]},
                      "| Layer | tech-context | depends_on |\n| --- | --- | --- |\n"
                      "| Service | docs/service/tech-context.md | - |\n")
        self.document("docs/service/tech-context.md", {
            "layer": "Service", "owns": owns if owns is not None else
            ["src/service/**", "tests/service/**", "app.py"],
            "depends_on": [], "red_lines": ["Never log secrets"],
            "gate": {"test": ["python3", "-m", "unittest"]}})

    def cli(self, entry, *args):
        result = subprocess.run(["/bin/sh", str(Path(PROVIDER) / "scripts/context" / entry), *args],
                                cwd=self.root, env=self.env, capture_output=True,
                                text=True, timeout=10)
        print(json.dumps({"entry": entry, "args": args, "status": result.returncode,
                          "stdout": result.stdout, "stderr": result.stderr}))
        return result

    def resolved(self, path):
        result = self.cli("resolve", path)
        self.assertEqual(0, result.returncode, result.stderr)
        row = json.loads(result.stdout)
        self.assertEqual({"path", "classification", "layer", "context", "chain", "reason"}, set(row))
        return row

    def test_implementation_external_tests_and_top_level_have_declared_owner(self):
        for path in ("src/service/api.py", "tests/service/test_api.py", "app.py"):
            with self.subTest(path=path):
                row = self.resolved(path)
                self.assertEqual(("leaf", "Service", "docs/service/tech-context.md"),
                                 (row["classification"], row["layer"], row["context"]))
        result = self.cli("field", "Service", "red_lines")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["Never log secrets"], json.loads(result.stdout))
        gates = self.cli("field", "Service", "gates")
        self.assertEqual(0, gates.returncode, gates.stderr)
        self.assertEqual([{"id": "test", "kind": "test", "mode": "both",
                           "command": ["python3", "-m", "unittest"]}],
                         json.loads(gates.stdout))

    def test_support_is_excluded_not_an_automatic_repair_layer(self):
        row = self.resolved("README.md")
        self.assertEqual(("excluded", "", "repository prose"),
                         (row["classification"], row["layer"], row["reason"]))

    def test_missing_and_overlapping_ownership_fail(self):
        self.assertNotEqual(0, self.cli("resolve", "orphan.py").returncode)
        self.simplified(["README.md", "src/service/**"])
        self.assertNotEqual(0, self.cli("resolve", "README.md").returncode)

    def test_mixed_results_do_not_mean_batch_success(self):
        result = self.cli("resolve", "app.py", "orphan.py")
        self.assertNotEqual(0, result.returncode)
        self.assertEqual("Service", json.loads(result.stdout)["layer"])
        self.assertEqual("resolve_failed", json.loads(result.stderr)["kind"])

    def test_two_leaf_owners_do_not_use_longest_prefix(self):
        root_map = self.root / "docs/architecture/tech-context.md"
        root_map.write_text(root_map.read_text() +
                            "| Nested | docs/nested/tech-context.md | - |\n")
        self.document("docs/nested/tech-context.md", {
            "layer": "Nested", "owns": ["src/service/nested/**"], "depends_on": []})
        result = self.cli("resolve", "src/service/nested/api.py")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("overlap", result.stderr)

    def test_invalid_and_missing_authority_fail(self):
        self.simplified("src/service/**")  # owns must be a list
        self.assertNotEqual(0, self.cli("resolve", "src/service/api.py").returncode)
        (self.root / "docs/service/tech-context.md").unlink()
        self.assertNotEqual(0, self.cli("resolve", "src/service/api.py").returncode)

    def test_legacy_context_test_paths_remain_authoritative(self):
        self.document("CONTEXT.md", {"schema": 1, "kind": "index", "routes": [{
            "patterns": ["src/**"], "test_paths": ["tests/**"], "context": "src/CONTEXT.md"}]})
        self.document("src/CONTEXT.md", {"schema": 1, "kind": "leaf", "layer": "Legacy",
                      "parent": "CONTEXT.md", "scope": ["src/**"], "test_paths": ["tests/**"]})
        self.assertEqual("Legacy", self.resolved("tests/test_api.py")["layer"])


if __name__ == "__main__":
    unittest.main()
