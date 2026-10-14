"""Exercise teamwork contract, authority links, preflight fail-closed, and publication boundaries."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Dict, List, Tuple
import unittest


TEAMWORK = Path(__file__).resolve().parents[1]
SKILL_MD = TEAMWORK / "SKILL.md"
WORKFLOW_ROLES_DIR = (TEAMWORK / "../../workflow/dev-team-roles").resolve()


def parse_workflow_role_links(skill_md_path: Path) -> List[str]:
    """Extracts relative workflow role paths linked in SKILL.md."""
    if not skill_md_path.is_file():
        return []
    text = skill_md_path.read_text(encoding="utf-8")
    links = re.findall(r"\[.*?\]\((../../workflow/dev-team-roles/[^)#]+)(?:#[^)]+)?\)", text)
    return links


def check_teamwork_preflight(bundle_teamwork_dir: Path, subagent_available: bool = True) -> Tuple[bool, str]:
    """Preflight check: verifies all required workflow sources in SKILL.md and subagent capability exist."""
    if not subagent_available:
        return False, "setup blocked: subagent capability is unavailable in current runtime"

    skill_file = bundle_teamwork_dir / "SKILL.md"
    if not skill_file.is_file():
        return False, f"setup blocked: teamwork skill entry missing: {skill_file}"

    # Preflight resolves source roles directly from the bundle links defined in SKILL.md
    role_links = parse_workflow_role_links(skill_file)
    if not role_links:
        role_links = [
            "../../workflow/dev-team-roles/dev-team-team-lead/SKILL.md",
            "../../workflow/dev-team-roles/dev-team-planner/SKILL.md",
            "../../workflow/dev-team-roles/dev-team-fullstack-engineer/SKILL.md",
            "../../workflow/dev-team-roles/dev-team-ai-reviewer/SKILL.md",
            "../../workflow/dev-team-roles/dev-team-squad/SKILL.md",
        ]

    for rel_link in role_links:
        target = (bundle_teamwork_dir / rel_link).resolve()
        if not target.is_file():
            return False, f"setup blocked: required workflow role source missing: {target}"
    return True, "ok"


def extract_workflow_publication_requirements(
    skill_md_path: Path = SKILL_MD,
    bundle_roles_dir: Path = WORKFLOW_ROLES_DIR,
) -> Dict[str, bool]:
    """Extracts and verifies publication and handoff requirements from shipped workflow files."""
    if not skill_md_path.is_file():
        raise FileNotFoundError(f"Missing teamwork SKILL.md at {skill_md_path}")

    skill_text = skill_md_path.read_text(encoding="utf-8")

    fullstack_file = bundle_roles_dir / "dev-team-fullstack-engineer/SKILL.md"
    ai_reviewer_file = bundle_roles_dir / "dev-team-ai-reviewer/SKILL.md"
    squad_file = bundle_roles_dir / "dev-team-squad/SKILL.md"

    for f in [fullstack_file, ai_reviewer_file, squad_file]:
        if not f.is_file():
            raise FileNotFoundError(f"Missing single-source role file at {f}")

    fs_text = fullstack_file.read_text(encoding="utf-8")
    ai_text = ai_reviewer_file.read_text(encoding="utf-8")
    squad_text = squad_file.read_text(encoding="utf-8")

    # Verify AI Reviewer enforces exact SHA and clean worktree preflight
    clean_tree_rule = bool(re.search(r"tree\s+must\s+be\s+clean", ai_text, re.I))
    exact_sha_rule = bool(re.search(r"submitted\s+SHA\s+must\s+equal\s+local\s+`?HEAD`?", ai_text, re.I))
    unpinned_reject_rule = bool(re.search(r"`?NEEDS_WORK`?\s+with\s+reason\s+`?unpinned`?", ai_text, re.I))
    exact_diff_rule = bool(re.search(r"git\s+diff\s+<merge-base>\.\.<SHA>", ai_text, re.I))

    # Verify Fullstack Engineer enforces sole writer, reviewed SHA unchanged, alignment check, and non-Draft PR
    fs_writer_rule = bool(re.search(r"One\s+writer:\s+work\s+only\s+in\s+the\s+registered\s+`?delivery_work_dir`?", fs_text, re.I))
    fs_unchanged_rule = bool(re.search(r"push\s+the\s+reviewed\s+SHA\s+unchanged", fs_text, re.I))
    fs_alignment_rule = bool(re.search(r"Confirm\s+local\s+HEAD\s*=\s*remote\s+branch\s*=\s*PR\s+`?headRefOid`?\s*=\s*reviewed\s+SHA", fs_text, re.I))
    fs_non_draft_rule = bool(re.search(r"PR\s+is\s+\*\*never\s+Draft\*\*", fs_text, re.I))
    fs_prm_handoff_rule = bool(re.search(r"End\s+with\s+`?\[@PR\s+Manager\]", fs_text, re.I))

    # Verify Squad shared rules enforce reviewed SHA and non-Draft PR
    squad_push_rule = bool(re.search(r"only\s+the\s+reviewed\s+SHA\s+is\s+pushed", squad_text, re.I))
    squad_non_draft_rule = bool(re.search(r"PR\s+is\s+never\s+Draft", squad_text, re.I))

    # Verify Teamwork SKILL.md enforces sole writer, exact-SHA verdict, and external PRM handoff
    tw_writer_rule = bool(re.search(r"Spawn\s+Fullstack\s+Engineer\s+\(sole\s+writer\)", skill_text, re.I))
    tw_exact_verdict_rule = bool(re.search(r"await\s+exact-SHA\s+verdict", skill_text, re.I))
    tw_resume_writer_rule = bool(re.search(r"never\s+spawn\s+a\s+replacement\s+writer", skill_text, re.I))
    tw_prm_rule = bool(re.search(r"PR\s+Manager\s+is\s+an?\s+external\s+workflow\s+03\s+role", skill_text, re.I))

    return {
        "clean_tree": clean_tree_rule and unpinned_reject_rule,
        "exact_sha_candidate": exact_sha_rule and exact_diff_rule and tw_exact_verdict_rule,
        "sole_writer": fs_writer_rule and tw_writer_rule and tw_resume_writer_rule,
        "reviewed_sha_unchanged": fs_unchanged_rule and fs_alignment_rule and squad_push_rule,
        "non_draft_pr": fs_non_draft_rule and squad_non_draft_rule,
        "external_prm_handoff": fs_prm_handoff_rule and tw_prm_rule,
    }


def validate_candidate_publication_against_shipped_workflow(
    repo_path: Path,
    candidate_sha: str,
    reviewed_sha: str,
    tested_sha: str,
    writer: str = "original_fullstack",
    is_draft: bool = False,
    handoff_target: str = "workflow_03_prm",
    skill_md_path: Path = SKILL_MD,
    bundle_roles_dir: Path = WORKFLOW_ROLES_DIR,
) -> Tuple[bool, str]:
    """Validates candidate publication against rules extracted from the shipped single-source workflow."""
    # 1. First ensure the shipped workflow itself enforces all required invariants
    reqs = extract_workflow_publication_requirements(skill_md_path, bundle_roles_dir)
    if not reqs["clean_tree"]:
        return False, "workflow contract weakened: AI Reviewer does not enforce clean working tree"
    if not reqs["exact_sha_candidate"]:
        return False, "workflow contract weakened: exact-SHA review requirement missing from workflow"
    if not reqs["sole_writer"]:
        return False, "workflow contract weakened: sole writer constraint missing from workflow"
    if not reqs["reviewed_sha_unchanged"]:
        return False, "workflow contract weakened: reviewed SHA unchanged requirement missing from workflow"
    if not reqs["non_draft_pr"]:
        return False, "workflow contract weakened: non-Draft PR requirement missing from workflow"
    if not reqs["external_prm_handoff"]:
        return False, "workflow contract weakened: external PR Manager handoff boundary missing from workflow"

    # 2. Enforce SHA equality and full 40-char length per workflow specification
    if not candidate_sha or not reviewed_sha or not tested_sha:
        return False, "rejected: missing required SHA parameter"
    if len(candidate_sha) != 40 or len(reviewed_sha) != 40 or len(tested_sha) != 40:
        return False, "rejected: SHA must be full 40-character hex string"
    if candidate_sha != reviewed_sha or candidate_sha != tested_sha:
        return False, "rejected: candidate_sha, reviewed_sha, and tested_sha must be identical"

    # 3. Verify git repository state against workflow exact-SHA and clean-tree invariants
    try:
        head_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_path, text=True
        ).strip()
        status_out = subprocess.check_output(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=repo_path,
            text=True,
        ).strip()
    except subprocess.CalledProcessError as e:
        return False, f"rejected: git command failed: {e}"

    if head_sha != candidate_sha:
        return False, f"rejected: HEAD ({head_sha}) does not match candidate_sha ({candidate_sha})"
    if status_out:
        return False, f"rejected: working tree is not clean:\n{status_out}"

    # 4. Enforce writer, non-draft, and handoff boundaries from shipped workflow
    if writer != "original_fullstack":
        return False, f"rejected: only original fullstack engineer may publish candidate (got {writer})"
    if is_draft:
        return False, "rejected: Dev Team PR must be non-Draft"
    if handoff_target != "workflow_03_prm":
        return False, f"rejected: handoff must be external workflow 03 PR Manager (got {handoff_target})"

    return True, candidate_sha


class TeamworkContractTests(unittest.TestCase):
    def test_skill_file_under_100_lines(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        line_count = len(text.splitlines())
        self.assertLess(line_count, 100, f"SKILL.md is {line_count} lines, must be < 100")

    def test_no_copied_agents_directory(self):
        agents_dir = TEAMWORK / "agents"
        self.assertFalse(agents_dir.exists(), "agents directory must be removed")

    def test_all_six_authority_links_exist_and_readable(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        expected_links = [
            ("../../workflow/dev-team-roles/dev-team-team-lead/SKILL.md", None),
            ("../../workflow/dev-team-roles/dev-team-planner/SKILL.md", None),
            ("../../workflow/dev-team-roles/dev-team-fullstack-engineer/SKILL.md", None),
            ("../../workflow/dev-team-roles/dev-team-ai-reviewer/SKILL.md", None),
            ("../../workflow/dev-team-roles/dev-team-squad/SKILL.md", None),
            (
                "../../workflow/dev-team-roles/dev-team-pr-manager/SKILL.md#clear-small-issue-owner-2026-10-13",
                "clear-small-issue-owner-2026-10-13",
            ),
        ]
        for link, anchor in expected_links:
            with self.subTest(link=link):
                self.assertIn(link, text, f"Link {link} must be in SKILL.md")
                rel_path = link.split("#", 1)[0]
                target = (TEAMWORK / rel_path).resolve()
                self.assertTrue(target.is_file(), f"Target {target} must exist")
                content = target.read_text(encoding="utf-8")
                self.assertTrue(len(content) > 0, f"Target {target} must not be empty")
                if anchor:
                    heading_pattern = rf"^#+\s+.*{re.escape('Clear small issue')}"
                    self.assertTrue(
                        bool(re.search(heading_pattern, content, re.M | re.IGNORECASE)),
                        f"Heading for anchor {anchor} not found in {target}",
                    )

    def test_prm_is_not_a_local_subagent(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        self.assertIn("PR Manager is not a local subagent", text)
        self.assertIn("No Local PRM", text)
        executing_roles = ["Team Lead", "Planner", "Fullstack Engineer", "AI Reviewer"]
        for role in executing_roles:
            self.assertIn(role, text)

    def test_symlink_and_space_paths_resolution(self):
        with tempfile.TemporaryDirectory(prefix="teamwork bundle with spaces ") as tmp:
            tmp_path = Path(tmp)
            bundle_dir = tmp_path / "bundle with spaces"
            skills_dir = bundle_dir / "skills"
            repo_dir = skills_dir / "repo"
            teamwork_copy = repo_dir / "teamwork"
            workflow_roles = bundle_dir / "skills/workflow/dev-team-roles"

            workflow_roles.mkdir(parents=True)
            repo_dir.mkdir(parents=True)
            shutil.copytree(TEAMWORK, teamwork_copy)

            real_roles = (TEAMWORK / "../../workflow/dev-team-roles").resolve()
            for child in real_roles.iterdir():
                if child.is_dir():
                    shutil.copytree(child, workflow_roles / child.name)

            skill_text = (teamwork_copy / "SKILL.md").read_text(encoding="utf-8")
            for link in [
                "../../workflow/dev-team-roles/dev-team-team-lead/SKILL.md",
                "../../workflow/dev-team-roles/dev-team-planner/SKILL.md",
                "../../workflow/dev-team-roles/dev-team-fullstack-engineer/SKILL.md",
                "../../workflow/dev-team-roles/dev-team-ai-reviewer/SKILL.md",
                "../../workflow/dev-team-roles/dev-team-squad/SKILL.md",
                "../../workflow/dev-team-roles/dev-team-pr-manager/SKILL.md#clear-small-issue-owner-2026-10-13",
            ]:
                rel_path = link.split("#", 1)[0]
                target = (teamwork_copy / rel_path).resolve()
                self.assertTrue(target.is_file(), f"Path with spaces failed to resolve: {target}")

            consumer_dir = tmp_path / "consumer"
            consumer_skill = consumer_dir / ".claude/skills/teamwork"
            consumer_skill.parent.mkdir(parents=True)
            consumer_skill.symlink_to(teamwork_copy, target_is_directory=True)

            for link in [
                "../../workflow/dev-team-roles/dev-team-team-lead/SKILL.md",
                "../../workflow/dev-team-roles/dev-team-planner/SKILL.md",
                "../../workflow/dev-team-roles/dev-team-fullstack-engineer/SKILL.md",
                "../../workflow/dev-team-roles/dev-team-ai-reviewer/SKILL.md",
                "../../workflow/dev-team-roles/dev-team-squad/SKILL.md",
            ]:
                rel_path = link.split("#", 1)[0]
                target = (consumer_skill.resolve() / rel_path).resolve()
                self.assertTrue(target.is_file(), f"Symlinked bundle failed to resolve: {target}")

    def test_missing_source_fails_closed_with_setup_blocker(self):
        with tempfile.TemporaryDirectory(prefix="teamwork-isolated-") as tmp:
            isolated_teamwork = Path(tmp) / "isolated-teamwork"
            shutil.copytree(TEAMWORK, isolated_teamwork)

            # Preflight must fail closed with setup blocker before running any role
            ok, msg = check_teamwork_preflight(isolated_teamwork, subagent_available=True)
            self.assertFalse(ok, "Preflight must fail when role sources are missing")
            self.assertIn("setup blocked", msg)
            self.assertIn("required workflow role source missing", msg)

    def test_missing_subagent_capability_fails_closed_with_setup_blocker(self):
        # Preflight must fail closed when subagent capability is unavailable
        ok, msg = check_teamwork_preflight(TEAMWORK, subagent_available=False)
        self.assertFalse(ok, "Preflight must fail when subagents are unavailable")
        self.assertIn("setup blocked", msg)
        self.assertIn("subagent capability is unavailable", msg)

    def test_no_business_repo_fallback(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        self.assertIn("Never search target repositories or fall back to copied role files", text)
        self.assertIn("Fail-Closed", text)

        # In an isolated environment with a business repo containing copied legacy agents,
        # preflight must not fall back to business repo and must fail closed.
        with tempfile.TemporaryDirectory(prefix="teamwork-fallback-test-") as tmp:
            tmp_path = Path(tmp)
            consumer_repo = tmp_path / "business-repo"
            legacy_agents = consumer_repo / ".claude/agents"
            legacy_agents.mkdir(parents=True)
            (legacy_agents / "team-lead.md").write_text("# Legacy Role\n")

            isolated_teamwork = consumer_repo / ".claude/skills/teamwork"
            isolated_teamwork.parent.mkdir(parents=True)
            shutil.copytree(TEAMWORK, isolated_teamwork)

            ok, msg = check_teamwork_preflight(isolated_teamwork, subagent_available=True)
            self.assertFalse(ok)
            self.assertIn("setup blocked", msg)

    def test_publication_requires_the_clean_reviewed_commit(self):
        # 1. Shipped workflow documents directly declare exact-SHA and clean-worktree requirements
        reqs = extract_workflow_publication_requirements(SKILL_MD, WORKFLOW_ROLES_DIR)
        self.assertTrue(reqs["clean_tree"], "Workflow must mandate clean working tree")
        self.assertTrue(reqs["exact_sha_candidate"], "Workflow must mandate exact-SHA candidate verification")
        self.assertTrue(reqs["reviewed_sha_unchanged"], "Workflow must mandate pushing reviewed SHA unchanged")

        # 2. Candidate publication evaluation against synthetic git repositories
        with tempfile.TemporaryDirectory(prefix="teamwork-pub-") as tmp:
            repo = Path(tmp) / "candidate"
            repo.mkdir()
            env = {**os.environ, "GIT_AUTHOR_NAME": "Bot", "GIT_AUTHOR_EMAIL": "bot@example.invalid",
                   "GIT_COMMITTER_NAME": "Bot", "GIT_COMMITTER_EMAIL": "bot@example.invalid"}

            def git(*args, input=None):
                return subprocess.check_output(
                    ["git", *args], cwd=repo, env=env, input=input, text=True
                ).strip()

            git("init", "-q")
            git(
                "fast-import",
                "--quiet",
                input="""commit refs/heads/task
committer Fixture <fixture@example.invalid> 1 +0000
data 4
one
M 100644 inline file.txt
data 4
one

commit refs/heads/replacement
committer Fixture <fixture@example.invalid> 2 +0000
data 4
two
from refs/heads/task

done
""",
            )
            git("symbolic-ref", "HEAD", "refs/heads/task")
            git("read-tree", "--reset", "-u", "HEAD")
            sha = git("rev-parse", "HEAD")
            replacement = git("rev-parse", "replacement")
            self.assertEqual(
                git("rev-parse", "HEAD^{tree}"), git("rev-parse", "replacement^{tree}")
            )

            # Clean tree and matching SHAs pass publication check
            ok, res = validate_candidate_publication_against_shipped_workflow(repo, sha, sha, sha)
            self.assertTrue(ok, f"Clean matching candidate must pass: {res}")
            self.assertEqual(res, sha)

            # Mismatched or invalid SHAs are rejected
            for param_set in [
                ("", sha, sha),
                (sha, "", sha),
                (sha, sha, ""),
                (sha[:8], sha, sha),
                (sha, sha[:8], sha),
                (sha, sha, sha[:8]),
                (sha, replacement, sha),
                (sha, sha, replacement),
            ]:
                with self.subTest(param_set=param_set):
                    bad_ok, _ = validate_candidate_publication_against_shipped_workflow(repo, *param_set)
                    self.assertFalse(bad_ok, f"Mismatched SHA must be rejected: {param_set}")

            # Unstaged modifications fail
            (repo / "file.txt").write_text("unreviewed\n")
            dirty_ok, _ = validate_candidate_publication_against_shipped_workflow(repo, sha, sha, sha)
            self.assertFalse(dirty_ok, "Unstaged modification must be rejected")

            # Reset and staged deletion fails
            git("read-tree", "--reset", "-u", "HEAD")
            git("update-index", "--force-remove", "file.txt")
            (repo / "file.txt").unlink()
            staged_ok, _ = validate_candidate_publication_against_shipped_workflow(repo, sha, sha, sha)
            self.assertFalse(staged_ok, "Staged deletion must be rejected")

            # Reset and untracked file fails
            git("read-tree", "--reset", "-u", "HEAD")
            (repo / "new.txt").touch()
            untracked_ok, _ = validate_candidate_publication_against_shipped_workflow(repo, sha, sha, sha)
            self.assertFalse(untracked_ok, "Untracked file must be rejected")
            (repo / "new.txt").unlink()

            # Different commit on same tree fails (old evidence cannot authorize replacement)
            git("update-ref", "refs/heads/task", replacement)
            rep_ok, _ = validate_candidate_publication_against_shipped_workflow(repo, sha, sha, sha)
            self.assertFalse(
                rep_ok,
                "Replacement commit must be rejected even with identical tree",
            )

        # 3. Negative control: weakening workflow rules causes publication validator to fail
        with tempfile.TemporaryDirectory(prefix="teamwork-weakened-") as tmp:
            weakened_roles = Path(tmp) / "roles"
            shutil.copytree(WORKFLOW_ROLES_DIR, weakened_roles)
            ai_file = weakened_roles / "dev-team-ai-reviewer/SKILL.md"
            # Remove clean tree requirement from AI Reviewer role
            ai_file.write_text(re.sub(r"tree\s+must\s+be\s+clean", "tree may be dirty", ai_file.read_text()))
            reqs_weak = extract_workflow_publication_requirements(SKILL_MD, weakened_roles)
            self.assertFalse(reqs_weak["clean_tree"], "Weakened AI Reviewer role must fail clean_tree requirement")

    def test_publication_boundary_enforces_original_fullstack_and_non_draft_prm_handoff(self):
        # 1. Shipped workflow documents directly declare sole-writer, non-draft, and external PRM handoff
        reqs = extract_workflow_publication_requirements(SKILL_MD, WORKFLOW_ROLES_DIR)
        self.assertTrue(reqs["sole_writer"], "Workflow must mandate sole writer")
        self.assertTrue(reqs["non_draft_pr"], "Workflow must mandate non-Draft PR")
        self.assertTrue(reqs["external_prm_handoff"], "Workflow must mandate external PR Manager handoff")

        with tempfile.TemporaryDirectory(prefix="teamwork-boundary-") as tmp:
            repo = Path(tmp) / "candidate"
            repo.mkdir()
            env = {**os.environ, "GIT_AUTHOR_NAME": "Bot", "GIT_AUTHOR_EMAIL": "bot@example.invalid",
                   "GIT_COMMITTER_NAME": "Bot", "GIT_COMMITTER_EMAIL": "bot@example.invalid"}

            def git(*args, input=None):
                return subprocess.check_output(
                    ["git", *args], cwd=repo, env=env, input=input, text=True
                ).strip()

            git("init", "-q")
            git(
                "fast-import",
                "--quiet",
                input="""commit refs/heads/task
committer Fixture <fixture@example.invalid> 1 +0000
data 4
one
M 100644 inline file.txt
data 4
one

done
""",
            )
            git("symbolic-ref", "HEAD", "refs/heads/task")
            git("read-tree", "--reset", "-u", "HEAD")
            sha = git("rev-parse", "HEAD")

            # Must be original Fullstack Engineer writer
            non_fs_ok, msg = validate_candidate_publication_against_shipped_workflow(
                repo, sha, sha, sha, writer="team_lead"
            )
            self.assertFalse(non_fs_ok)
            self.assertIn("only original fullstack engineer may publish", msg)

            # Must be non-Draft PR
            draft_ok, msg = validate_candidate_publication_against_shipped_workflow(
                repo, sha, sha, sha, is_draft=True
            )
            self.assertFalse(draft_ok)
            self.assertIn("must be non-Draft", msg)

            # Must hand off to external workflow 03 PRM, not local subagent
            local_prm_ok, msg = validate_candidate_publication_against_shipped_workflow(
                repo, sha, sha, sha, handoff_target="local_subagent_prm"
            )
            self.assertFalse(local_prm_ok)
            self.assertIn("must be external workflow 03 PR Manager", msg)

            # Valid parameters pass
            valid_ok, valid_res = validate_candidate_publication_against_shipped_workflow(
                repo, sha, sha, sha, writer="original_fullstack", is_draft=False, handoff_target="workflow_03_prm"
            )
            self.assertTrue(valid_ok)
            self.assertEqual(valid_res, sha)

        # 2. Negative control: removing non-draft rule from SKILL.md or role fails validation
        with tempfile.TemporaryDirectory(prefix="teamwork-weakened-pr-") as tmp:
            weakened_skill = Path(tmp) / "SKILL.md"
            weakened_skill.write_text(SKILL_MD.read_text().replace("opening a non-Draft PR", "opening a Draft PR"))
            weakened_roles = Path(tmp) / "roles"
            shutil.copytree(WORKFLOW_ROLES_DIR, weakened_roles)
            fs_file = weakened_roles / "dev-team-fullstack-engineer/SKILL.md"
            fs_file.write_text(fs_file.read_text().replace("The PR is **never Draft**", "The PR may be Draft"))
            reqs_weak = extract_workflow_publication_requirements(weakened_skill, weakened_roles)
            self.assertFalse(reqs_weak["non_draft_pr"], "Weakened non-Draft rule must fail non_draft_pr requirement")

    def test_backend_priority_order(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        self.assertIn("Codex CLI → Claude native → Copilot", text)


if __name__ == "__main__":
    unittest.main()
