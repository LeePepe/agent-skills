"""Exercise documented entry/loader/role boundaries without an agent or host install."""
import os
import json
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


TEAMWORK = Path(__file__).resolve().parents[1]
CI_AUTOFIX = TEAMWORK.parent / "layered-ci-autofix"
LEGACY = json.loads((Path(__file__).parent / "fixtures/legacy-roles.json").read_text())


def bash_block(document, section):
    body = document.split(section, 1)[1]
    return re.search(r"```bash\n(.*?)\n```", body, re.S).group(1)


class ContractHandoffTests(unittest.TestCase):
    def test_legacy_fixtures_are_the_actual_preserved_git_blobs(self):
        expected = {
            "team_lead": "e0224985aebb2b7fa06463ad9603ec5359196f82",
            "git_monitor": "9869b20ee329c6015e11f857de4dc1b29ff5d89b",
        }
        for role, oid in expected.items():
            raw = LEGACY[role].encode()
            self.assertEqual(hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest(), oid)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="teamwork-contract-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.consumer = self.root / "consumer"
        self.bundle = self.root / "bundle with spaces"
        self.source = self.bundle / "skills/repo/teamwork"
        self.ci_source = self.bundle / "skills/repo/layered-ci-autofix"
        self.canonical = self.bundle / "skills/workflow/README.md"
        self.home.mkdir()
        self.consumer.mkdir()
        shutil.copytree(TEAMWORK, self.source, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(CI_AUTOFIX, self.ci_source)
        self.canonical.parent.mkdir(parents=True)
        self.canonical.write_text("# Canonical workflow\n\nUnique fixture policy, never copy me.\n")
        self.env = {"HOME": str(self.home), "PATH": os.environ["PATH"], "TMPDIR": str(self.root)}
        self.run_shell("git init -q")
        self.installed_skill = self.consumer / ".claude/skills/teamwork"
        self.installed_skill.parent.mkdir(parents=True)
        self.installed_skill.symlink_to(self.source, target_is_directory=True)

    def run_shell(self, script, check=True, bindings=None):
        return subprocess.run(
            ["/bin/bash", "-eu", "-c", script], cwd=self.consumer,
            env={**self.env, **(bindings or {})}, text=True, capture_output=True, timeout=10, check=check,
        )

    def copy_role(self):
        lead = (self.source / "agents/team-lead.md").read_text()
        loader = bash_block(lead, "## Progressive Loading")
        self.run_shell(loader.replace("<stage_roles>", "git-monitor"),
                       bindings={"TEAMWORK_SOURCE_DIR": str(self.source)})
        return self.consumer / ".claude/agents/git-monitor.md"

    def contract_read(self, role):
        text = role.read_text()
        legacy_link = re.search(r"\[workflow delivery boundary\]\(([^)]+)\)", text)
        if legacy_link:
            # Exercise the original public instruction literally to expose the copied-role failure.
            target = role.parent / legacy_link.group(1).split("#", 1)[0]
            return target.read_text(), target.resolve()
        entry = (self.source / "SKILL.md").read_text()
        resolver = bash_block(entry, "### 3. Delegate to `team-lead`")
        result = self.run_shell(resolver, bindings={
            "TEAMWORK_SKILL_DIR": str(self.installed_skill),
            "TEAM_LEAD_ROLE_FILE": str(self.source / "agents/team-lead.md"),
        })
        target = Path(result.stdout.strip())
        # Pass the entry's real result through the documented role input, not a copied contract.
        preflight = bash_block(text, "## Required workflow contract")
        return self.run_shell(preflight, bindings={"WORKFLOW_CONTRACT_PATH": str(target)}).stdout, target

    def test_copied_role_reads_the_original_contract(self):
        role = self.copy_role()
        self.assertTrue(role.is_file())
        self.assertFalse(role.is_symlink())
        content, target = self.contract_read(role)
        self.assertEqual(content, "# Canonical workflow\n\nUnique fixture policy, never copy me.\n")
        self.assertTrue(target.samefile(self.canonical))
        self.assertEqual(list((self.consumer / ".claude/agents").iterdir()), [role])

    def test_actual_base_team_lead_override_stops_entry(self):
        selected = self.consumer / ".claude/agents/team-lead.md"
        selected.parent.mkdir(parents=True)
        selected.write_text(LEGACY["team_lead"])
        before = selected.read_bytes()
        entry = bash_block((self.source / "SKILL.md").read_text(), "### 3. Delegate to `team-lead`")
        result = self.run_shell(entry, check=False, bindings={
            "TEAMWORK_SKILL_DIR": str(self.installed_skill),
            "TEAM_LEAD_ROLE_FILE": str(selected),
        })
        self.assertNotEqual(result.returncode, 0, "legacy selected team-lead was admitted without the mandatory handoff")
        self.assertEqual(selected.read_bytes(), before)

    def test_actual_v1_git_monitor_override_stops_loader(self):
        role = self.consumer / ".claude/agents/git-monitor.md"
        role.parent.mkdir(parents=True)
        role.write_text(LEGACY["git_monitor"])
        before = role.read_bytes()
        loader = bash_block((self.source / "agents/team-lead.md").read_text(), "## Progressive Loading")
        result = self.run_shell(loader.replace("<stage_roles>", "git-monitor"), check=False,
                                bindings={"TEAMWORK_SOURCE_DIR": str(self.source)})
        self.assertNotEqual(result.returncode, 0, "legacy selected git-monitor was retained and admitted")
        self.assertEqual(role.read_bytes(), before)

    def test_actual_selected_monitor_is_checked_before_spawn(self):
        self.copy_role()  # A compatible loader destination cannot vouch for another selected role.
        selected = self.home / ".claude/agents/git-monitor.md"
        selected.parent.mkdir(parents=True)
        selected.write_text(LEGACY["git_monitor"])
        before = selected.read_bytes()
        check = bash_block((self.source / "agents/team-lead.md").read_text(),
                           "## Required workflow contract handoff")
        result = self.run_shell(check, check=False, bindings={
            "TEAMWORK_SOURCE_DIR": str(self.source), "GIT_MONITOR_ROLE_FILE": str(selected),
        })
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(selected.read_bytes(), before)

    def test_changed_role_is_rechecked_at_spawn(self):
        selected = self.copy_role()
        selected.write_text(LEGACY["git_monitor"])
        check = bash_block((self.source / "agents/team-lead.md").read_text(),
                           "## Required workflow contract handoff")
        result = self.run_shell(check, check=False, bindings={
            "TEAMWORK_SOURCE_DIR": str(self.source), "GIT_MONITOR_ROLE_FILE": str(selected),
        })
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(selected.read_text(), LEGACY["git_monitor"])

    def test_compatible_selected_team_lead_override_is_retained(self):
        selected = self.consumer / ".claude/agents/team-lead.md"
        selected.parent.mkdir(parents=True)
        selected.write_text((self.source / "agents/team-lead.md").read_text() + "\nLocal notes.\n")
        before = selected.read_bytes()
        entry = bash_block((self.source / "SKILL.md").read_text(), "### 3. Delegate to `team-lead`")
        result = self.run_shell(entry, bindings={
            "TEAMWORK_SKILL_DIR": str(self.installed_skill), "TEAM_LEAD_ROLE_FILE": str(selected),
        })
        self.assertTrue(Path(result.stdout.strip()).samefile(self.canonical))
        self.assertEqual(selected.read_bytes(), before)

    def test_unknown_role_selection_stops_before_delegation(self):
        entry = bash_block((self.source / "SKILL.md").read_text(), "### 3. Delegate to `team-lead`")
        result = self.run_shell(entry, check=False,
                                bindings={"TEAMWORK_SKILL_DIR": str(self.installed_skill)})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_preinstalled_role_still_uses_current_handoff(self):
        role = self.copy_role()
        role.write_text(role.read_text() + "\nConsumer override preserved.\n")
        before = role.read_bytes()
        self.copy_role()
        self.assertEqual(role.read_bytes(), before)
        content, target = self.contract_read(role)
        self.assertEqual(content, self.canonical.read_text())
        self.assertTrue(target.samefile(self.canonical))

    def test_home_skill_symlink_survives_copy_to_consumer(self):
        self.installed_skill.unlink()
        self.installed_skill = self.home / ".claude/skills/teamwork"
        self.installed_skill.parent.mkdir(parents=True)
        self.installed_skill.symlink_to(self.source, target_is_directory=True)
        role = self.copy_role()
        content, target = self.contract_read(role)
        self.assertEqual(content, self.canonical.read_text())
        self.assertTrue(target.samefile(self.canonical))

    def test_missing_bundle_contract_stops_resolution(self):
        self.canonical.unlink()
        resolver = bash_block((self.source / "SKILL.md").read_text(), "### 3. Delegate to `team-lead`")
        result = self.run_shell(resolver, check=False, bindings={
            "TEAMWORK_SKILL_DIR": str(self.installed_skill),
            "TEAM_LEAD_ROLE_FILE": str(self.source / "agents/team-lead.md"),
        })
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_missing_or_invalid_handoff_cannot_pass_role_preflight(self):
        role = self.copy_role()
        preflight = bash_block(role.read_text(), "## Required workflow contract")
        for bindings in ({}, {"WORKFLOW_CONTRACT_PATH": ""},
                         {"WORKFLOW_CONTRACT_PATH": str(self.root / "absent.md")},
                         {"WORKFLOW_CONTRACT_PATH": str(self.canonical.parent)}):
            with self.subTest(bindings=bindings):
                result = self.run_shell(preflight, check=False, bindings=bindings)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")

    def test_contract_removed_after_resolution_stops_role_preflight(self):
        role = self.copy_role()
        _, target = self.contract_read(role)
        self.canonical.unlink()
        preflight = bash_block(role.read_text(), "## Required workflow contract")
        result = self.run_shell(preflight, check=False, bindings={"WORKFLOW_CONTRACT_PATH": str(target)})
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_legacy_copied_role_is_a_sensitive_negative_control(self):
        role = self.copy_role()
        role.write_text("Read [workflow delivery boundary](../../../workflow/README.md).\n")
        with self.assertRaises(FileNotFoundError):
            self.contract_read(role)

    def direct_handoff(self, bindings, check=False):
        preflight = bash_block((self.ci_source / "SKILL.md").read_text(),
                               "### 可选 git-monitor 交接")
        return self.run_shell(preflight, check=check, bindings=bindings)

    def test_direct_caller_passes_original_contract_to_copied_override(self):
        # The direct helper path has no team-lead or full teamwork pipeline.
        selected = self.consumer / ".claude/agents/git-monitor.md"
        selected.parent.mkdir(parents=True)
        shutil.copyfile(self.source / "agents/git-monitor.md", selected)
        selected.write_text(selected.read_text() + "\nConsumer override preserved.\n")
        before = selected.read_bytes()
        for parent in (self.consumer, self.home):
            with self.subTest(parent=parent):
                installed = parent / ".claude/skills/layered-ci-autofix"
                installed.parent.mkdir(parents=True, exist_ok=True)
                installed.symlink_to(self.ci_source, target_is_directory=True)
                result = self.direct_handoff({
                    "CI_AUTOFIX_SKILL_DIR": str(installed),
                    "GIT_MONITOR_ROLE_FILE": str(selected),
                }, check=True)
                target = Path(result.stdout.strip())
                self.assertTrue(target.samefile(self.canonical))
                preflight = bash_block(selected.read_text(), "## Required workflow contract")
                read = self.run_shell(preflight, bindings={"WORKFLOW_CONTRACT_PATH": str(target)})
                self.assertEqual(read.stdout, self.canonical.read_text())
                self.assertEqual(selected.read_bytes(), before)
                self.assertEqual(list(selected.parent.iterdir()), [selected])

    def test_direct_caller_rejects_actual_selected_legacy_override(self):
        self.copy_role()  # A valid repo copy cannot vouch for a different runtime selection.
        selected = self.home / ".claude/agents/git-monitor.md"
        selected.parent.mkdir(parents=True)
        selected.write_text(LEGACY["git_monitor"])
        before = selected.read_bytes()
        result = self.direct_handoff({
            "CI_AUTOFIX_SKILL_DIR": str(self.ci_source),
            "GIT_MONITOR_ROLE_FILE": str(selected),
        })
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(selected.read_bytes(), before)

    def test_direct_caller_rechecks_changed_selection_on_resume(self):
        selected = self.copy_role()
        bindings = {"CI_AUTOFIX_SKILL_DIR": str(self.ci_source),
                    "GIT_MONITOR_ROLE_FILE": str(selected)}
        self.direct_handoff(bindings, check=True)
        selected.write_text(LEGACY["git_monitor"])
        result = self.direct_handoff(bindings)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(selected.read_text(), LEGACY["git_monitor"])

    def test_direct_caller_requires_loaded_bundle_and_actual_selection(self):
        selected = self.copy_role()
        for bindings in ({}, {"CI_AUTOFIX_SKILL_DIR": str(self.ci_source)},
                         {"GIT_MONITOR_ROLE_FILE": str(selected)},
                         {"CI_AUTOFIX_SKILL_DIR": str(self.root / "absent"),
                          "GIT_MONITOR_ROLE_FILE": str(selected)},
                         {"CI_AUTOFIX_SKILL_DIR": str(self.ci_source),
                          "GIT_MONITOR_ROLE_FILE": str(self.root / "absent.md")}):
            with self.subTest(bindings=bindings):
                result = self.direct_handoff(bindings)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")

    def test_direct_caller_requires_contract_and_compatibility_checker(self):
        selected = self.copy_role()
        for required in (self.canonical, self.source / "scripts/check_contract_handoff.py"):
            with self.subTest(required=required):
                original = required.read_bytes()
                required.unlink()
                try:
                    result = self.direct_handoff({
                        "CI_AUTOFIX_SKILL_DIR": str(self.ci_source),
                        "GIT_MONITOR_ROLE_FILE": str(selected),
                    })
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(result.stdout, "")
                finally:
                    required.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
