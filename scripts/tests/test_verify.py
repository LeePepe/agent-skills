"""Real catalog entry/cache/hook behavior in disposable offline repositories."""
import hashlib
import os
import subprocess
import unittest

from adoption_fixture import (CatalogFixture, PIN, ProviderFixture, environment,
                              git, materialize_provider, run)


def snapshot(root):
    return {str(p.relative_to(root)): (p.lstat().st_mode,
            os.readlink(p) if p.is_symlink() else hashlib.sha256(p.read_bytes()).hexdigest())
            for p in root.rglob("*") if p.is_file() or p.is_symlink()}


class VerifyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provider = ProviderFixture()
        cls.addClassCleanup(cls.provider.close)

    def setUp(self):
        self.repo = CatalogFixture()
        self.addCleanup(self.repo.close)
        self.env = dict(environment(), SHARED_CI=str(self.provider.root), GIT_ALLOW_PROTOCOL="file")
        # Exercise actual audit/native commands and configured gate dispatch,
        # without recursively invoking this test through its own verify fixture.
        for path, layer in (("skills/tech-context.md", "Catalog"), ("scripts/tech-context.md", "Tooling")):
            text = (self.repo.root / path).read_text()
            self.repo.write(path, text.replace("python3 scripts/run_tests.py " + layer,
                                              'python3 -c "print(\'' + layer + ' gate reached\')"'))
        self.repo.commit("nonrecursive test gate witnesses")

    def verify(self, *args):
        return run(self.repo.root, "bash", "scripts/verify", *args, env=self.env, check=False)

    def test_both_forms_run_all_gates_on_empty_diff_and_empty_ci_selection(self):
        self.env.update(CI_SELECTION_FULL="false", CI_SELECTED_LAYERS="", VERIFY_BASE="HEAD",
                        SHARED_CI_SOURCE="not-an-admitted-fixture")
        for args in ((), ("--all",), ()):
            with self.subTest(args=args):
                result = self.verify(*args)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                for marker in ("17 个 SKILL.md", "registry / plugin.json / README", "Catalog gate reached",
                               "Tooling gate reached", "syntax:", '"files": 3', "full Catalog/Tooling"):
                    self.assertIn(marker, result.stdout)
        self.assertEqual(git(self.provider.root, "status", "--porcelain", "--ignored"), "")

    def test_unsupported_arguments_fail_before_bootstrap(self):
        self.env["SHARED_CI"] = str(self.repo.root / "absent")
        for args in (("--selected",), ("--help",), ("--all", "extra"), ("",)):
            result = self.verify(*args)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("usage:", result.stderr)
        self.assertFalse((self.repo.root / ".shared-ci").exists())

    def test_caller_gate_failure_and_whitespace_fail(self):
        path = "scripts/tech-context.md"
        original = (self.repo.root / path).read_text()
        self.repo.write(path, original.replace("print('Tooling gate reached')", "raise SystemExit(7)"))
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("gate_failed", result.stderr)
        self.repo.write(path, original)
        readme = (self.repo.root / "README.md").read_text()
        self.repo.write("README.md", readme + "\ntrailing whitespace   \n")
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("trailing whitespace", result.stdout + result.stderr)
        git(self.repo.root, "add", "README.md")
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("trailing whitespace", result.stdout + result.stderr)

    def test_invalid_metadata_fails_before_provider_access_without_fallback(self):
        path = self.repo.root / ".github/repo-contract.json"
        original = path.read_text()
        self.env["SHARED_CI"] = str(self.repo.root / "absent")
        for content in ("{}", original.replace('"schema": 1', '"schema": 1, "schema": 1'),
                        original.replace(PIN, "main")):
            path.write_text(content)
            result = self.verify()
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("supplied SHARED_CI", result.stderr)
        path.write_text(original)
        git(self.repo.root, "rm", "--cached", ".github/repo-contract.json")
        self.assertIn("tracked and unconflicted", self.verify().stderr)
        git(self.repo.root, "add", ".github/repo-contract.json")
        path.unlink()
        path.symlink_to("../README.md")
        self.assertIn("must not traverse a symlink", self.verify().stderr)

    def test_wrong_dirty_ignored_dirty_and_flagged_caches_are_preserved(self):
        for mutation in ("wrong", "tracked", "untracked", "ignored", "assume", "skip"):
            with self.subTest(mutation=mutation):
                cache = self.repo.root.parent / ("cache-" + mutation)
                materialize_provider(self.provider.root, cache)
                code = cache / "scripts/context/_context.py"
                if mutation == "wrong":
                    git(cache, "commit", "--allow-empty", "-qm", "wrong revision")
                elif mutation in ("tracked", "assume", "skip"):
                    code.write_text(code.read_text() + "\nraise RuntimeError('must not execute')\n")
                    if mutation != "tracked":
                        flag = "--assume-unchanged" if mutation == "assume" else "--skip-worktree"
                        git(cache, "update-index", flag, "scripts/context/_context.py")
                else:
                    path = cache / ("__pycache__/untrusted.pyc" if mutation == "ignored" else "untrusted")
                    path.parent.mkdir(exist_ok=True)
                    path.write_text("preserve me")
                before = snapshot(cache)
                self.env["SHARED_CI"] = str(cache)
                result = self.verify()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("preserve", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(snapshot(cache), before)

    def test_fixed_fixture_ignores_source_head_and_worktree_decoys(self):
        source = self.repo.root.parent / "decoy-source"
        materialize_provider(self.provider.root, source)
        code = source / "scripts/context/_context.py"
        code.write_text("raise RuntimeError('unapproved head must not execute')\n")
        git(source, "add", "scripts/context/_context.py")
        git(source, "commit", "-qm", "unapproved fixture head")
        code.write_text("raise RuntimeError('dirty worktree must not execute')\n")
        target = self.repo.root.parent / "fixed-destination"
        materialize_provider(source, target)
        self.assertEqual(git(target, "rev-parse", "HEAD"), PIN)
        self.assertEqual((target / "scripts/context/_context.py").read_bytes(),
                         (self.provider.root / "scripts/context/_context.py").read_bytes())
        self.assertIn("dirty worktree", code.read_text())

    def test_missing_fixed_objects_fail_without_network_or_candidate_substitution(self):
        with self.assertRaises(subprocess.CalledProcessError):
            materialize_provider(self.repo.root, self.repo.root.parent / "no-fallback")
        self.assertFalse((self.repo.root.parent / "no-fallback").exists())

    def test_files_nonrepositories_nested_and_symlink_caches_are_preserved(self):
        parent = self.repo.root.parent
        ordinary = parent / "ordinary"
        ordinary.mkdir()
        (ordinary / "keep").write_text("not a Git repository")
        file = parent / "file"
        file.write_text("keep file")
        link = parent / "link"
        link.symlink_to(self.provider.root, target_is_directory=True)
        broken = parent / "broken"
        broken.symlink_to(parent / "missing")
        for path in (ordinary, file, link, broken, self.provider.root / "scripts"):
            self.env["SHARED_CI"] = str(path)
            result = self.verify()
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(path.exists() or path.is_symlink())
        self.assertEqual((ordinary / "keep").read_text(), "not a Git repository")
        self.assertEqual(file.read_text(), "keep file")
        self.assertEqual(link.readlink(), self.provider.root)

    def test_default_cold_cache_uses_only_offline_selected_git_objects(self):
        # A Git URL rewrite is configured ONLY in this fixture's external test
        # config; the actual bootstrap still performs its normal fetch/admission.
        config = self.repo.root.parent / "offline.gitconfig"
        run(self.repo.root, "git", "config", "--file", str(config),
            "url." + str(self.provider.root) + ".insteadOf", "https://github.com/LeePepe/shared-ci.git")
        self.env.update(GIT_CONFIG_GLOBAL=str(config), GIT_ALLOW_PROTOCOL="file")
        self.env.pop("SHARED_CI")
        for _ in range(2):
            result = self.verify()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        cache = self.repo.root / ".shared-ci"
        self.assertEqual(git(cache, "rev-parse", "HEAD"), PIN)
        self.assertEqual(git(cache, "status", "--porcelain", "--ignored"), "")

    def test_failed_cold_fetch_is_preserved_and_not_retried_destructively(self):
        self.env.pop("SHARED_CI")
        self.env["GIT_ALLOW_PROTOCOL"] = "file"  # network attempts are prohibited
        first = self.verify()
        self.assertNotEqual(first.returncode, 0)
        cache = self.repo.root / ".shared-ci"
        self.assertTrue((cache / ".git").is_dir())
        (cache / "keep").write_text("failed bootstrap evidence")
        before = snapshot(cache)
        second = self.verify()
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("preserve existing provider path", second.stderr)
        self.assertEqual(snapshot(cache), before)

    def test_real_pre_push_with_git_hook_environment_preserves_caller(self):
        # Actual native tests plus the nested-Git regression, without recursively
        # re-entering this pre-push test from its fixture.
        for path, layer in (("skills/tech-context.md", "Catalog"), ("scripts/tech-context.md", "Tooling")):
            text = (self.repo.root / path).read_text()
            command = ("python3 scripts/run_tests.py Catalog" if layer == "Catalog" else
                       "python3 -m unittest discover -s scripts/tests -p test_git_hook_isolation.py -v")
            self.repo.write(path, text.replace('python3 -c "print(\'' + layer + ' gate reached\')"', command))
        self.repo.commit("real hook fixture")
        bare = self.repo.root.parent / "push-target.git"
        run(self.repo.root, "git", "init", "-q", "--bare", str(bare))
        git(self.repo.root, "remote", "add", "fixture", str(bare))
        gitdir = self.repo.root / ".git"
        self.env.update(GIT_DIR=str(gitdir), GIT_WORK_TREE=str(self.repo.root),
                        GIT_INDEX_FILE=str(gitdir / "index"), GIT_OBJECT_DIRECTORY=str(gitdir / "objects"))
        before = {name: (gitdir / name).read_bytes() for name in ("index", "config", "HEAD")}
        refs = git(self.repo.root, "show-ref", "--heads")
        result = run(self.repo.root, "git", "-c", "core.hooksPath=.githooks", "push",
                     "fixture", "HEAD:refs/heads/verified", env=self.env, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Ran 4 tests", result.stderr)
        self.assertIn("preserve_outer_repository", result.stderr)
        self.assertIn("full Catalog/Tooling", result.stdout)
        self.assertEqual({name: (gitdir / name).read_bytes() for name in before}, before)
        self.assertEqual(git(self.repo.root, "show-ref", "--heads"), refs)
        self.assertEqual(git(self.repo.root, "status", "--porcelain"), "")


if __name__ == "__main__":
    unittest.main()
