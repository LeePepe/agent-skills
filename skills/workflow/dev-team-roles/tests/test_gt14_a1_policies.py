"""Regression assertions for GT14-A's gap routing and verdict recipient."""

from pathlib import Path
import re
import unittest


ROLES_DIR = Path(__file__).resolve().parents[1]


def role_text(role):
    return (ROLES_DIR / f"dev-team-{role}" / "SKILL.md").read_text(encoding="utf-8")


class GT14A1PolicyTests(unittest.TestCase):
    def test_prm_returns_omitted_adaptation_and_tests_to_definer_with_evidence(self):
        text = role_text("pr-manager")
        repair = " ".join(text.split("## Repair routing and budgets", 1)[1]
                          .split("\n## ", 1)[0].split())
        for clause in (
            "Current-version repairs within the frozen Task return to the original FS with unchanged acceptance",
            "For omitted adaptation/tests or planning/dependency gaps",
            "attach the failing command, affected acceptance and proposal",
            "return them through TL to the definer under contract R3/R5",
            "do not authorize adding them to the frozen Task",
        ):
            with self.subTest(clause=clause):
                self.assertIn(clause, repair)
        self.assertNotRegex(text.lower(), r"stay in that version|在当前版本(内)?补")

    def test_reviewer_verdict_template_mentions_only_actual_requester(self):
        handoff = role_text("ai-reviewer").split("## Handoff", 1)[1].split("\n## ", 1)[0]
        normalized = " ".join(handoff.split())
        for clause in (
            "End with exactly one mention: the actual requester only",
            "Planner Lead for job (a), Fullstack Engineer for job (b), or Team Lead for job (c)",
            "Do not mention any non-requester role in a verdict comment",
        ):
            with self.subTest(clause=clause):
                self.assertIn(clause, normalized)

        templates = re.findall(r"```text\n(.*?)\n```", handoff, re.S)
        self.assertEqual(len(templates), 1)
        template = templates[0]
        self.assertEqual(len(template.splitlines()), 2)
        marker, mention = template.splitlines()
        self.assertTrue(marker.startswith("<!-- review: "))
        self.assertTrue(marker.endswith(" -->"))
        self.assertEqual(mention, "[@<requester role>](mention://agent/<requester agent ID>)")
        for gate, requester in (("spec", "Planner Lead"), ("impl", "Fullstack Engineer"),
                                ("target", "Team Lead")):
            with self.subTest(gate=gate, requester=requester):
                rendered = (template.replace("<spec|impl|target>", gate)
                            .replace("<requester role>", requester)
                            .replace("<requester agent ID>", "synthetic-requester"))
                self.assertEqual(
                    re.findall(r"\[@([^\]]+)\]\(mention://agent/([^)]+)\)", rendered),
                    [(requester, "synthetic-requester")],
                )
                self.assertIn(f"gate={gate}", rendered)


if __name__ == "__main__":
    unittest.main()
