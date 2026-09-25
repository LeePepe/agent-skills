"""Published review transport and completion behavior, entirely offline."""
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

from adoption_fixture import CatalogFixture, PIN, ProviderFixture, environment, git, run, workflow


GH_STUB = """#!/bin/sh
case "$*" in
  *--paginate*) exit 0 ;;
esac
body=""
for arg in "$@"; do case "$arg" in body=*) body="${arg#body=}";; esac; done
printf '%s' "$body" > "$STUB_OUT/comment"
"""
CODEX_STUB = """#!/bin/sh
out=""; prev=""; last=""
for arg in "$@"; do [ "$prev" = -o ] && out="$arg"; prev="$arg"; last="$arg"; done
printf '%s' "$last" > "$STUB_OUT/prompt"
printf '%s' "$STUB_VERDICT" > "$out"
"""
KIMI_STUB = """#!/bin/sh
prev=""
for arg in "$@"; do [ "$prev" = -p ] && printf '%s' "$arg" > "$STUB_OUT/prompt"; prev="$arg"; done
printf '%s' "$STUB_VERDICT"
"""


class ReviewContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.provider = ProviderFixture()
        cls.addClassCleanup(cls.provider.close)

    def setUp(self):
        self.repo = CatalogFixture()
        self.addCleanup(self.repo.close)
        self.tools = self.repo.root.parent / "offline-tools"
        self.tools.mkdir()
        for name, body in (("gh", GH_STUB), ("offline-codex", CODEX_STUB), ("offline-kimi", KIMI_STUB)):
            path = self.tools / name
            path.write_text(body)
            path.chmod(0o755)
        self.guide = self.repo.root / "docs/repository-gates.md"
        self.expected = self.guide.read_bytes()
        self.base = git(self.repo.root, "rev-parse", "HEAD")
        git(self.repo.root, "remote", "add", "origin", str(self.repo.root))

    def head_change(self):
        self.repo.write("README.md", (self.repo.root / "README.md").read_text() + "\nHead-only fixture\n")
        self.head = self.repo.commit("head fixture")
        git(self.repo.root, "checkout", "-q", "--detach", self.base)

    def wrapper(self, tool, rules="docs/repository-gates.md"):
        for name in ("prompt", "comment"):
            (self.tools / name).unlink(missing_ok=True)
        env = dict(environment(), PATH=str(self.tools) + os.pathsep + os.environ["PATH"],
                   PR_NUMBER="1", BASE_SHA=self.base, HEAD_SHA=self.head, BASE_REPO="fixture/catalog",
                   GH_TOKEN="offline-fixture", SHARED_CI_DIR=str(self.provider.root),
                   CODEX_BIN=str(self.tools / "offline-codex"), KIMI_BIN=str(self.tools / "offline-kimi"),
                   CODEX_REVIEW_HOME=str(self.tools / "review-home"), REVIEW_RULES_FILE=rules,
                   STUB_OUT=str(self.tools), GIT_ALLOW_PROTOCOL="file",
                   STUB_VERDICT=json.dumps({"verdict": "pass", "summary": "offline transport fixture",
                                            "blockers": [], "notes": []}))
        result = run(self.repo.root, "bash", str(self.provider.root / "scripts/review" / (tool + "-review.sh")),
                     env=env, check=False)
        prompt = (self.tools / "prompt").read_bytes() if (self.tools / "prompt").exists() else None
        comment = (self.tools / "comment").read_text() if (self.tools / "comment").exists() else ""
        return result, prompt, comment

    def rejected(self, rules="docs/repository-gates.md"):
        for tool in ("codex", "kimi"):
            with self.subTest(tool=tool, rules=rules):
                result, prompt, comment = self.wrapper(tool, rules)
                self.assertEqual(result.returncode, 1 if tool == "codex" else 0, result.stdout + result.stderr)
                self.assertIsNone(prompt, "invalid policy must not invoke a model")
                self.assertIn("unavailable", comment)

    def test_both_wrappers_transport_complete_exact_base_bytes_not_head_or_worktree(self):
        # Extra final newlines distinguish full byte transport from shell trimming.
        self.guide.write_bytes(self.expected + b"\n\n")
        self.expected = self.guide.read_bytes()
        self.base = self.repo.commit("complete guide with trailing newlines")
        self.guide.write_text("HOSTILE HEAD RULES\n")
        self.head_change()
        self.guide.write_text("MUTABLE WORKTREE RULES\n")
        for _ in range(2):
            for tool in ("codex", "kimi"):
                result, prompt, comment = self.wrapper(tool)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn("unavailable", comment)
                rules = prompt.split(b"## Trusted repository rules\n\n", 1)[1].split(
                    b"\n\n## Trusted architecture facts (base tree)", 1)[0]
                self.assertEqual(rules, self.expected)
                self.assertNotIn(b"HOSTILE HEAD RULES", rules)
                self.assertNotIn(b"MUTABLE WORKTREE RULES", rules)
        self.assertEqual(git(self.repo.root, "rev-parse", "HEAD"), self.base)
        self.assertEqual(self.guide.read_text(), "MUTABLE WORKTREE RULES\n")
        self.assertEqual(git(self.provider.root, "status", "--porcelain", "--ignored"), "")

    def test_missing_base_guide_cannot_be_supplied_by_head_or_worktree(self):
        git(self.repo.root, "rm", "docs/repository-gates.md")
        self.base = self.repo.commit("base without guide")
        self.guide.write_text("HEAD ONLY RULES\n")
        self.head_change()
        self.guide.write_text("UNTRACKED WORKTREE RULES\n")
        self.rejected()

    def test_oversized_invalid_and_symlink_base_rules_make_review_unavailable(self):
        for content in (b"x" * 24001, b"", b" \n\t", b"bad\xff", b"bad\0text", b"bad\x01text"):
            with self.subTest(content_length=len(content)):
                self.guide.write_bytes(content)
                self.base = self.repo.commit("invalid base rules")
                self.head_change()
                self.rejected()
        self.guide.unlink()
        self.guide.symlink_to("../README.md")
        self.base = self.repo.commit("symlink base rules")
        self.head_change()
        self.rejected()

    def test_unsafe_rules_paths_and_no_diff_do_not_bypass_admission(self):
        self.head_change()
        for path in ("../README.md", "/README.md", "docs//repository-gates.md", "missing.md"):
            self.rejected(path)
        self.head = self.base
        self.rejected("missing.md")

    def test_codex_only_completion_gate_executes_exact_success_rule(self):
        review = workflow(self.provider.root, (self.repo.root / ".github/workflows/review.yml").read_text())
        jobs = review["jobs"]
        self.assertEqual(set(jobs), {"codex-review-target", "codex-review-gate", "kimi-review"})
        self.assertIn("pull_request_target", review["on"])
        for job_id, filename in (("codex-review-target", "codex-review.yml"), ("kimi-review", "kimi-review.yml")):
            job = jobs[job_id]
            self.assertEqual(set(job), {"if", "uses", "with"})
            self.assertTrue(job["uses"].endswith(filename + "@" + PIN))
            self.assertEqual(job["with"], {"rules-file": "docs/repository-gates.md"})
            self.assertEqual(job["if"], "vars.SHARED_CI_REVIEW_RUNNER == 'true'")
        gate = jobs["codex-review-gate"]
        self.assertEqual(set(gate), {"if", "needs", "runs-on", "permissions", "timeout-minutes", "steps"})
        self.assertEqual(gate["if"], "${{ always() }}")
        self.assertEqual(gate["needs"], ["codex-review-target"])
        self.assertEqual(gate["runs-on"], "ubuntu-latest")
        self.assertEqual(gate["permissions"], {})
        self.assertEqual(len(gate["steps"]), 1)
        step = gate["steps"][0]
        self.assertEqual(set(step), {"name", "shell", "env", "run"})
        self.assertEqual(step["env"], {"CODEX_RESULT": "${{ needs.codex-review-target.result }}"})
        self.assertNotIn("${{", step["run"])
        for value in ("success", "skipped", "failure", "cancelled", "", None, "unknown",
                      "neutral", "Success", "success ", "success\nfailure", "$(exit 0)"):
            env = environment()
            env.pop("CODEX_RESULT", None)
            if value is not None:
                env["CODEX_RESULT"] = value
            result = run(self.repo.root, step["shell"], "-eu", "-c", step["run"], env=env, check=False)
            self.assertEqual(result.returncode, 0 if value == "success" else 1, result.stdout + result.stderr)

    def test_published_aggregate_rejects_missing_skipped_and_stale_lane_evidence(self):
        data = {"lanes": {"verify": {"selected": True, "result": "success", "tested_sha": self.base}},
                "expected_lanes": ["verify"], "expected_sha": self.base,
                "event": "push", "check_pr_body": False}
        def evaluate(payload):
            return subprocess.run([sys.executable, "-I", "-B", str(self.provider.root / "scripts/quality/gate.py")],
                                  input=json.dumps(payload), cwd=self.repo.root, env=environment(),
                                  text=True, capture_output=True, timeout=30)
        self.assertEqual(evaluate(data).returncode, 0)
        for change in ({"result": "skipped"}, {"tested_sha": "1" * 40}, {"tested_sha": ""}):
            candidate = json.loads(json.dumps(data))
            candidate["lanes"]["verify"].update(change)
            self.assertEqual(evaluate(candidate).returncode, 1)
        data["lanes"] = {}
        self.assertEqual(evaluate(data).returncode, 1)

    def test_published_integrity_requires_rationale_and_current_live_head_and_base(self):
        path = "scripts/tests/test_integrity_fixture.py"
        self.repo.write(path, "import unittest\nclass Example(unittest.TestCase):\n"
                             "    def test_kept(self):\n        self.assertEqual(1, 1)\n")
        self.base = self.repo.commit("integrity base")
        self.repo.write(path, "import unittest\nclass Example(unittest.TestCase):\n"
                             "    def test_kept(self):\n        pass\n")
        self.head = self.repo.commit("integrity loss")
        spec = importlib.util.spec_from_file_location(
            "admitted_integrity", self.provider.root / "scripts/quality/test_integrity.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        body = "## Removed or weakened tests or policy\n`" + path + "`: deliberate fixture loss\n"
        response = {"head": {"sha": self.head}, "base": {"sha": self.base}, "body": body}

        def evaluate(payload):
            output = io.StringIO()
            previous = os.getcwd()
            try:
                os.chdir(self.repo.root)
                env = dict(environment(), REPO="fixture/catalog", PR_NUMBER="1", GH_TOKEN="offline-fixture")
                # The HTTP boundary is the only stub; execute the admitted CLI's
                # normal live-body identity/rationale path, never contact GitHub.
                with patch.dict(os.environ, env, clear=True), patch.object(
                        module.urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(payload).encode())):
                    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
                        rc = module.main(["--base", self.base, "--head", self.head, "--live-body"])
                return rc, json.loads(output.getvalue())
            finally:
                os.chdir(previous)

        rc, result = evaluate(response)
        self.assertEqual(rc, 0, result)
        self.assertTrue(result["body_checked"])
        self.assertTrue(result["losses"])
        for text in ("", "## Removed or weakened tests or policy\nnone\n"):
            self.assertEqual(evaluate(dict(response, body=text))[0], 1)
        for key in ("head", "base"):
            candidate = dict(response)
            candidate[key] = {"sha": "1" * 40}
            self.assertEqual(evaluate(candidate)[0], 1)
        candidate = dict(response)
        del candidate["body"]
        self.assertEqual(evaluate(candidate)[0], 1)


if __name__ == "__main__":
    unittest.main()
