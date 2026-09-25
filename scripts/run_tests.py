#!/usr/bin/env python3
"""Admit tracked responsibility-owned modules before loading any test code."""
import importlib.util
import os
from pathlib import Path
import stat
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
# Execution seams, not a second ownership policy: keep these explicit suites
# aligned with the native leaf declarations. Absent future recipe modules are
# not imported; a present module must first be staged and admitted.
SUITES = {
    "Catalog": (
        "skills/repo/code-review/scripts/test_discover_review_context.py",
        "scripts/tests/test_consumer_authority.py",
        "scripts/tests/test_dispatch_safety.py",
        "scripts/tests/test_entrypoint_recipe.py",
        "scripts/tests/test_layer_routing_recipe.py",
    ),
    "Tooling": (
        "scripts/tests/test_git_hook_isolation.py",
        "scripts/tests/test_repository_adoption.py",
        "scripts/tests/test_review_context.py",
        "scripts/tests/test_tooling.py",
        "scripts/tests/test_verify.py",
    ),
}
TEST_DIRS = ("scripts/tests", "skills/repo/code-review/scripts")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8", "surrogateescape")


def candidate(path):
    name = Path(path).name
    return name == "__init__.py" or (name.startswith("test_") and name.endswith(".py"))


def admit_tests():
    """Inspect both test locations without imports or recursive discovery."""
    def scan_error(error):
        raise error  # os.walk otherwise silently hides unreadable candidates

    if Path(git("rev-parse", "--show-toplevel").strip()).resolve() != ROOT:
        raise ValueError("Git selects a different repository")
    entries = {}
    for row in git("ls-files", "--stage", "-v", "-z", "--", *TEST_DIRS).split("\0"):
        if row:
            metadata, path = row.split("\t", 1)
            entries.setdefault(path, []).append(metadata.split())
    paths = {path for path in entries if candidate(path)}
    for relative in TEST_DIRS:
        parent = ROOT
        for part in Path(relative).parts:
            parent = parent / part
            if parent.is_symlink():
                raise ValueError(f"symlink test directory: {relative!r}")
        for directory, dirs, files in os.walk(parent, followlinks=False, onerror=scan_error):
            for name in dirs + files:
                path = Path(directory) / name
                relative_path = path.relative_to(ROOT).as_posix()
                if path.is_symlink() and (name in dirs or candidate(path)):
                    raise ValueError(f"symlink test candidate: {relative_path!r}")
                if candidate(path):
                    paths.add(relative_path)
    allowed = {path for suite in SUITES.values() for path in suite}
    for path in sorted(paths):
        if path not in allowed:
            raise ValueError(f"unexpected test candidate: {path!r}; declare its suite and responsibility")
        rows = entries.get(path, [])
        if (len(rows) != 1 or len(rows[0]) != 4 or rows[0][0] != "H"
                or rows[0][1] not in ("100644", "100755") or rows[0][3] != "0"):
            raise ValueError(f"test must have one regular, unflagged stage-0 index entry: {path!r}")
        if not stat.S_ISREG((ROOT / path).lstat().st_mode):
            raise ValueError(f"test must be a regular worktree file: {path!r}")
    # Git reports intent-to-add as a working-tree addition, not an admitted
    # staged file. Ordinary unstaged edits to tracked modules remain testable.
    pending = set(git("diff", "--no-ext-diff", "--no-textconv", "--no-renames", "--name-only",
                      "--diff-filter=A", "-z", "--", *TEST_DIRS).split("\0"))
    if paths & pending:
        raise ValueError(f"stage intent-to-add tests before execution: {sorted(paths & pending)!r}")
    return paths


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in SUITES:
        raise SystemExit("usage: run_tests.py Catalog|Tooling")
    layer = sys.argv[1]
    try:
        admitted = admit_tests()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise SystemExit(f"test admission failed: {error}") from error
    # All candidates are admitted before any module (including load_tests) can
    # execute. Load exact source paths, not packages or cached bytecode, and do
    # not let unittest recurse into sibling/nested packages as discover() does.
    import unittest
    suite = unittest.TestSuite()
    for relative in SUITES[layer]:
        if relative in admitted:
            path = ROOT / relative
            sys.path.insert(0, str(path.parent))
            spec = importlib.util.spec_from_file_location(path.stem, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
            suite.addTests(unittest.TestLoader().loadTestsFromModule(module))
    if not suite.countTestCases():
        raise SystemExit("no tests selected for " + layer)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.skipped:
        print("selected tests skipped; verification is incomplete", file=sys.stderr)
    return 0 if result.wasSuccessful() and not result.skipped else 1


if __name__ == "__main__":
    raise SystemExit(main())
