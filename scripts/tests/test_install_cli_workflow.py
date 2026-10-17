"""Exercise real global-entry installation in isolated configuration directories."""
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts/install-cli-workflow.py"
CONTRACT = ROOT / "skills/workflow/execution-contract.md"


class InstallCliWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.home = Path(self.scratch.name)
        self.codex = self.home / "codex config"
        self.claude = self.home / "claude config"

    def run_installer(self, *args, clients=("codex", "claude")):
        command = [sys.executable, str(INSTALLER), "--codex-home", str(self.codex),
                   "--claude-home", str(self.claude)]
        for client in clients:
            command.extend(("--client", client))
        return subprocess.run(command + list(args), text=True, capture_output=True)

    def test_installs_loadable_reference_and_preserves_user_text_and_mode(self):
        self.codex.mkdir()
        file = self.codex / "AGENTS.md"
        original = "# Personal agreements\nKeep responses concise.\n"
        file.write_text(original)
        file.chmod(0o640)
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        content = file.read_text()
        self.assertTrue(content.startswith(original))
        self.assertIn(str(CONTRACT), content)
        self.assertTrue(CONTRACT.is_file())
        self.assertEqual(stat.S_IMODE(file.stat().st_mode), 0o640)
        self.assertEqual(stat.S_IMODE((self.claude / "CLAUDE.md").stat().st_mode), 0o600)
        self.assertEqual(self.run_installer("--check").returncode, 0)
        before = file.read_bytes(), file.stat().st_mtime_ns
        self.assertEqual(self.run_installer().returncode, 0)
        self.assertEqual((file.read_bytes(), file.stat().st_mtime_ns), before)

    def test_nonempty_codex_override_is_the_effective_destination(self):
        self.codex.mkdir()
        ordinary = self.codex / "AGENTS.md"
        ordinary.write_text("Keep ordinary guidance.\n")
        override = self.codex / "AGENTS.override.md"
        override.write_text("Temporary guidance.\n")
        result = self.run_installer(clients=("codex",))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(CONTRACT), override.read_text())
        self.assertEqual(ordinary.read_text(), "Keep ordinary guidance.\n")
        self.assertFalse(self.claude.exists())

    def test_empty_override_does_not_hide_normal_global_instructions(self):
        self.codex.mkdir()
        (self.codex / "AGENTS.override.md").write_text(" \n")
        self.assertEqual(self.run_installer(clients=("codex",)).returncode, 0)
        self.assertIn(str(CONTRACT), (self.codex / "AGENTS.md").read_text())

    def test_check_has_no_filesystem_side_effects(self):
        result = self.run_installer("--check")
        self.assertEqual(result.returncode, 1)
        self.assertFalse(self.codex.exists())
        self.assertFalse(self.claude.exists())

    def test_refresh_updates_only_the_managed_reference(self):
        self.codex.mkdir()
        file = self.codex / "AGENTS.md"
        file.write_text("Before\n<!-- agent-skills:workflow:begin -->\nOld reference\n"
                        "<!-- agent-skills:workflow:end -->\nAfter\n")
        self.assertEqual(self.run_installer(clients=("codex",)).returncode, 0)
        content = file.read_text()
        self.assertTrue(content.startswith("Before\n"))
        self.assertTrue(content.endswith("\nAfter\n"))
        self.assertNotIn("Old reference", content)
        self.assertEqual(content.count("<!-- agent-skills:workflow:begin -->"), 1)

    def test_bad_second_destination_does_not_mutate_first(self):
        self.claude.mkdir()
        malformed = self.claude / "CLAUDE.md"
        original = "Personal text\n<!-- agent-skills:workflow:begin -->\n"
        malformed.write_text(original)
        result = self.run_installer()
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.codex.exists())
        self.assertEqual(malformed.read_text(), original)

    def test_symlink_instruction_file_is_preserved(self):
        self.codex.mkdir()
        target = self.home / "personal.md"
        target.write_text("Original instructions\n")
        (self.codex / "AGENTS.md").symlink_to(target)
        result = self.run_installer()
        self.assertEqual(result.returncode, 2)
        self.assertTrue((self.codex / "AGENTS.md").is_symlink())
        self.assertEqual(target.read_text(), "Original instructions\n")
        self.assertFalse(self.claude.exists())

    def test_invalid_second_parent_preserves_first_file_bytes_and_mtime(self):
        self.codex.mkdir()
        first = self.codex / "AGENTS.md"
        first.write_text("Personal text\n<!-- agent-skills:workflow:begin -->\nOld reference\n"
                         "<!-- agent-skills:workflow:end -->\n")
        before = first.read_bytes(), first.stat().st_mtime_ns
        invalid = self.home / "regular-file"
        invalid.write_text("Preserve this file too.\n")
        dangling = self.home / "dangling-link"
        dangling.symlink_to(self.home / "missing-directory")
        for second_home in (invalid, invalid / "nested", dangling / "nested"):
            with self.subTest(second_home=second_home):
                result = self.run_installer("--claude-home", str(second_home))
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual((first.read_bytes(), first.stat().st_mtime_ns), before)
                self.assertEqual(invalid.read_text(), "Preserve this file too.\n")
                self.assertTrue(dangling.is_symlink())


if __name__ == "__main__":
    unittest.main()
