"""GT14-B1 authority routing, membership, seven-field handoffs and F6/F11 safeguards."""

from pathlib import Path
import re
import unittest

ROLES = Path(__file__).resolve().parents[1]
CONTRACT = ("https://github.com/LeePepe/user-skills/blob/"
            "cb5ec84961d05a937a3a5196e02a8eeac224fd4f/skills/goal-target-task/SKILL.md")


def text(role):
    return (ROLES / f"dev-team-{role}" / "SKILL.md").read_text()


class GT14B1PolicyTests(unittest.TestCase):
    def test_contract_rules_reference_the_frozen_authority(self):
        for role in ("squad", "team-lead", "planner", "fullstack-engineer", "ai-reviewer", "pr-manager"):
            with self.subTest(role=role):
                source = text(role)
                self.assertIn(CONTRACT, source)
                self.assertNotIn("same problem × same Task", source)
                self.assertNotIn("Target-wide acceptance has its own two-round budget", source)
                self.assertNotIn("for one level only", source)

    def test_shared_runtime_procedures_have_one_authority(self):
        squad = text("squad")
        owners = {
            "`GIT_CONFIG_GLOBAL`": "github-identity",
            "`created_at == updated_at`": "owner-decisions",
            "at most 2 reruns": "retry-budgets",
            "No Owner approval, approving review or CODEOWNERS review is a merge prerequisite": "merge-rules-all-repos",
        }
        for clause, anchor in owners.items():
            with self.subTest(clause=clause):
                self.assertEqual(squad.count(clause), 1)
                for role in ("team-lead", "fullstack-engineer", "pr-manager"):
                    source = text(role)
                    self.assertNotIn(clause, source)
                    self.assertIn("../dev-team-squad/SKILL.md", source)
        for role in ("fullstack-engineer", "pr-manager"):
            self.assertIn("../dev-team-squad/SKILL.md#github-identity", text(role))
        for role in ("team-lead", "pr-manager"):
            self.assertIn("../dev-team-squad/SKILL.md#owner-decisions", text(role))

    def test_member_tables_match_exactly_and_exclude_supervisor(self):
        expected = [
            ("TL (Team Lead)", "leader"), ("FS (Fullstack Engineer)", "engineer"),
            ("AI Reviewer", "reviewer"), ("PRM (PR Manager)", "ops"),
            ("Planner (Planner Lead)", "planner"),
        ]
        for source in (text("squad"), (ROLES / "README.md").read_text(),
                       (ROLES.parent / "README.md").read_text()):
            with self.subTest(source=source[:50]):
                table = source.split("| Member | Squad role |", 1)[1].split("\n\n", 1)[0]
                rows = re.findall(r"^\| ([^|]+) \| ([^|]+) \|$", table, re.M)
                self.assertEqual(rows, expected)
                self.assertNotIn("Designer", table)
                self.assertNotIn("Flow Supervisor", table)
                self.assertTrue("own Multica Autopilot" in source or "自己的 Multica Autopilot" in source)
        self.assertIn("outside the Dev Team squad", text("flow-supervisor"))

    def test_all_roles_use_squad_seven_field_handoff(self):
        section = text("squad").split("## Handoffs\n", 1)[1].split("\n## ", 1)[0]
        fields = re.findall(r"^\| ([a-z]+) \|", section, re.M)
        self.assertEqual(fields, ["target", "intent", "baseline", "scope", "owner", "evidence", "next"])
        for role in ("team-lead", "planner", "fullstack-engineer", "ai-reviewer", "pr-manager", "flow-supervisor"):
            with self.subTest(role=role):
                source = text(role)
                self.assertIn("squad's seven fields", source)
                self.assertIn("../dev-team-squad/SKILL.md#handoffs", source)
                self.assertNotRegex(source, r"six (?:index )?fields")
        self.assertIn("dev-team-squad/SKILL.md#handoffs", (ROLES.parent / "README.md").read_text())

    def test_planner_cannot_change_implementation_issue_status(self):
        red_lines = text("planner").split("## Red lines", 1)[1]
        self.assertIn("Never change an implementation issue's status", red_lines)
        self.assertIn("`blocked` or `in_review`; TL alone", red_lines)
        self.assertIn("Only you change implementation issue status", text("team-lead"))

    def test_prm_unblocks_on_evidence_without_a_silence_timer(self):
        source = text("pr-manager")
        normalized = " ".join(source.split())
        self.assertIn("not rerun or redispatched until concrete unblock evidence appears", normalized)
        self.assertIn("An eligible revisit resumes the existing flow", normalized)
        self.assertIn("Human pause** outranks elapsed silence and any automatic action until its resume condition", normalized)
        self.assertIn("every 30 minutes", source)  # Autopilot cadence, never a silence gate.
        self.assertNotRegex(source.lower(), r"(?:30.minute|30 minutes).*silence|silence.*(?:30.minute|30 minutes)")

    def test_relative_section_references_resolve(self):
        files = list(ROLES.glob("*/SKILL.md")) + [ROLES / "README.md", ROLES.parent / "README.md"]
        for path in files:
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
                if "://" in target or "#" not in target:
                    continue
                name, anchor = target.split("#", 1)
                destination = path.parent / name if name else path
                headings = re.findall(r"^#{1,6} (.+)$", destination.read_text(), re.M)
                slugs = [re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-") for heading in headings]
                with self.subTest(path=path.name, target=target):
                    self.assertIn(anchor, slugs)


if __name__ == "__main__":
    unittest.main()
