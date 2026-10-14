"""Exercise teamwork contract, authority links, and boundaries without external hosts."""
from pathlib import Path
import re
import shutil
import tempfile
import unittest


TEAMWORK = Path(__file__).resolve().parents[1]
SKILL_MD = TEAMWORK / "SKILL.md"


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
            ("../../workflow/dev-team-roles/dev-team-pr-manager/SKILL.md#clear-small-issue-owner-2026-10-13", "clear-small-issue-owner-2026-10-13"),
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

    def test_missing_source_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="teamwork-isolated-") as tmp:
            isolated_teamwork = Path(tmp) / "isolated-teamwork"
            shutil.copytree(TEAMWORK, isolated_teamwork)

            expected_roles = [
                isolated_teamwork / "../../workflow/dev-team-roles/dev-team-team-lead/SKILL.md",
                isolated_teamwork / "../../workflow/dev-team-roles/dev-team-planner/SKILL.md",
                isolated_teamwork / "../../workflow/dev-team-roles/dev-team-fullstack-engineer/SKILL.md",
                isolated_teamwork / "../../workflow/dev-team-roles/dev-team-ai-reviewer/SKILL.md",
                isolated_teamwork / "../../workflow/dev-team-roles/dev-team-squad/SKILL.md",
            ]
            for role_path in expected_roles:
                self.assertFalse(role_path.resolve().exists(), f"Isolated role path should not exist: {role_path}")

    def test_no_business_repo_fallback(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        self.assertIn("Never search target repositories or fall back to copied role files", text)
        self.assertIn("Fail-Closed", text)

    def test_exact_sha_and_original_fullstack_publication_boundary(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        self.assertIn("Original Fullstack Engineer", text)
        self.assertIn("push reviewed SHA + non-Draft PR", text)
        self.assertIn("External workflow 03 PR Manager handoff", text)
        self.assertIn("exact-SHA pre-push review", text)

    def test_backend_priority_order(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        self.assertIn("Codex CLI → Claude native → Copilot", text)


if __name__ == "__main__":
    unittest.main()
