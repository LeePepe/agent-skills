"""Exercise the real verification entry with a disposable outer Git repository."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# This gate uses real Git, including mutating index/config/ref operations. It runs
# only in the disposable caller and creates another disposable repository.
PROBE = '''import os
import subprocess
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory(prefix="nested-git-") as directory:
    repo = Path(directory).resolve()
    def git(*args, check=True):
        return subprocess.run(["git", *args], cwd=repo, check=check,
                              text=True, capture_output=True)
    git("init", "-q")
    assert git("rev-parse", "--show-toplevel").stdout.strip() == str(repo)
    assert git("config", "--get", "probe.inherited", check=False).returncode == 1
    assert git("-c", "probe.deliberate=kept", "config", "--get", "probe.deliberate").stdout.strip() == "kept"
    assert os.environ["VERIFY_MODE"] == "ci"
    git("config", "probe.fixture", "nested-only")
    (repo / "sample.txt").write_text("nested fixture\\n")
    git("add", "sample.txt")
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
    assert git("rev-parse", "--verify", "HEAD").returncode == 0
print("nested Git fixture verified")
'''


class HookIsolationTests(unittest.TestCase):
    def setUp(self):
        # Never let a real hook's repository environment contaminate setup or
        # teardown. All mutating commands below explicitly use this clean env.
        local_names = subprocess.check_output(
            ["git", "rev-parse", "--local-env-vars"], cwd=ROOT, text=True).splitlines()
        self.env = {key: value for key, value in os.environ.items() if key not in local_names}
        self.env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
                        GIT_ALLOW_PROTOCOL="file", PYTHONDONTWRITEBYTECODE="1", VERIFY_MODE="ci")
        self.scratch = tempfile.TemporaryDirectory(prefix="hook-isolation-")
        self.addCleanup(self.scratch.cleanup)
        self.repo = Path(self.scratch.name).resolve() / "outer"
        self.repo.mkdir()
        self.git("init", "-q")
        for name in ("AGENTS.md", "CLAUDE.md", "scripts/verify", ".githooks/pre-push",
                     ".github/workflows/ci.yml", ".github/pull_request_template.md", ".github/CODEOWNERS"):
            target = self.repo / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        self.write(".gitignore", ".shared-ci/\n")
        self.write("docs/architecture/tech-context.md", """---
layer: _root
support:
  - patterns: [AGENTS.md, CLAUDE.md, .gitignore, .github/**, .githooks/**, outer.txt]
    reason: disposable fixture support
---
| Layer | tech-context | depends_on |
|---|---|---|
| Fixture | scripts/tech-context.md | (none) |
""")
        self.write("scripts/tech-context.md", """---
layer: Fixture
owns: [scripts/**]
depends_on: []
gate:
  test: python3 scripts/nested_git_check.py
red_lines: [Keep the outer repository unchanged.]
---
""")
        self.write("scripts/nested_git_check.py", PROBE)
        self.write("outer.txt", "committed\n")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "-c", "commit.gpgsign=false", "commit", "-qm", "outer baseline")
        self.git("config", "probe.outer", "preserve")
        self.git("update-ref", "refs/heads/preserved", "HEAD")
        self.write("outer.txt", "staged\n")
        self.git("add", "outer.txt")
        self.write("outer.txt", "unstaged\n")
        self.git("clone", "-q", "--no-hardlinks", str(ROOT / ".shared-ci"), ".shared-ci")

    def write(self, relative, content):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, env=self.env,
                              check=True, text=True, capture_output=True)

    def snapshot(self):
        return {
            "index": (self.repo / ".git/index").read_bytes(),
            "config": (self.repo / ".git/config").read_bytes(),
            "refs": self.git("for-each-ref", "--format=%(refname) %(objectname)").stdout,
            "head": (self.repo / ".git/HEAD").read_bytes(),
            "worktree": (self.repo / "outer.txt").read_bytes(),
        }

    def hook_environment(self):
        gitdir = self.repo / ".git"
        return {**self.env, "GIT_DIR": str(gitdir), "GIT_WORK_TREE": str(self.repo),
                "GIT_COMMON_DIR": str(gitdir), "GIT_INDEX_FILE": str(gitdir / "index"),
                "GIT_OBJECT_DIRECTORY": str(gitdir / "objects"), "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "probe.inherited", "GIT_CONFIG_VALUE_0": "outer-only"}

    def test_pre_push_environment_cannot_retarget_cache_or_nested_fixtures(self):
        before = self.snapshot()
        result = subprocess.run([str(self.repo / ".githooks/pre-push"), "origin", "fixture"],
                                cwd=self.repo, env=self.hook_environment(), text=True, capture_output=True)
        self.assertEqual(self.snapshot(), before, "verification mutated outer index/config/refs/worktree")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("nested Git fixture verified", result.stdout)

    def test_real_pre_push_preserves_outer_state_and_explicit_nested_arguments(self):
        remote = self.repo.parent / "remote.git"
        self.git("init", "-q", "--bare", str(remote))
        before = self.snapshot()
        # Actual Git launches the real hook and exports command-line -c settings.
        # Dry-run exercises pre-push without updating either side's refs.
        result = self.git("-c", "core.hooksPath=.githooks", "-c", "probe.inherited=outer-only",
                          "push", "--dry-run", str(remote), "HEAD:refs/heads/main")
        self.assertEqual(self.snapshot(), before, "real pre-push mutated outer index/config/refs/worktree")
        self.assertIn("nested Git fixture verified", result.stdout + result.stderr)

    def test_cold_cache_initialization_cannot_write_outer_gitdir(self):
        source = self.repo.parent / "published-shared-ci"
        (self.repo / ".shared-ci").rename(source)
        # Redirect the fixed public fetch URL to the disposable published-pin
        # clone. This file is NOT the user's global Git config; network is off.
        config = self.repo.parent / "fixture.gitconfig"
        self.git("config", "--file", str(config), f"url.{source.as_uri()}.insteadOf",
                 "https://github.com/LeePepe/shared-ci.git")
        environment = {**self.hook_environment(), "GIT_CONFIG_GLOBAL": str(config)}
        before = self.snapshot()
        result = subprocess.run([str(self.repo / "scripts/verify"), "--all"], cwd=self.repo,
                                env=environment, text=True, capture_output=True)
        self.assertEqual(self.snapshot(), before, "cold-cache bootstrap mutated outer Git state")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("nested Git fixture verified", result.stdout)


if __name__ == "__main__":
    unittest.main()
