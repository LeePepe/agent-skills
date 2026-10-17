#!/usr/bin/env python3
"""Install a managed reference to the common workflow in local CLI instructions."""
import argparse
import os
from pathlib import Path
import stat
import sys
import tempfile


BEGIN = "<!-- agent-skills:workflow:begin -->"
END = "<!-- agent-skills:workflow:end -->"


def reference_block(contract):
    return f"""{BEGIN}
For development requirements, planning, implementation and delivery, read and follow
the [common CLI/subagent execution contract](<{contract}>).
Load it before substantive work unless this session already has the current version.
Use its Goal/Target/Task, reviewed-baseline, delegation and independent-acceptance rules.
Loading it grants no role: bind the role to invocation provenance and explicit assignment.
A planning worker defines or validates Goal/Targets; the coordinator only allocates,
supervises, routes decisions and reports evidence. Workers never self-promote.
When delegating, pass this contract, role/source binding, original intent, accepted
baseline, scope, ownership and expected evidence; do not assume skill inheritance.
Repository instructions, authorization boundaries and required checks remain in force.
{END}"""


def managed_content(original, block):
    begins, ends = original.count(BEGIN), original.count(END)
    if begins == ends == 0:
        return original + ("\n\n" if original else "") + block + "\n"
    if begins != 1 or ends != 1 or original.index(BEGIN) > original.index(END):
        raise ValueError("malformed or duplicate managed workflow markers; preserve and repair them first")
    start = original.index(BEGIN)
    end = original.index(END) + len(END)
    return original[:start] + block + original[end:]


def destinations(clients, codex_home, claude_home):
    paths = []
    for client in dict.fromkeys(clients):
        if client == "codex":
            override = codex_home / "AGENTS.override.md"
            active = override.exists() and bool(override.read_text(encoding="utf-8").strip())
            paths.append(override if active else codex_home / "AGENTS.md")
        else:
            paths.append(claude_home / "CLAUDE.md")
    return paths


def replace_file(path, content):
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".workflow-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
            os.fchmod(stream.fileno(), mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", choices=("codex", "claude"), action="append", required=True)
    parser.add_argument("--codex-home", type=Path,
                        default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")))
    parser.add_argument("--claude-home", type=Path,
                        default=Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")))
    parser.add_argument("--check", action="store_true", help="check references without writing")
    args = parser.parse_args(argv)
    contract = Path(__file__).resolve().parents[1] / "skills/workflow/execution-contract.md"
    try:
        if not contract.is_file():
            raise ValueError("common execution contract is missing from this checkout")
        block = reference_block(contract)
        updates = []
        # Validate every destination before changing any file.
        for path in destinations(args.client, args.codex_home.expanduser(), args.claude_home.expanduser()):
            for parent in path.parents:
                if (parent.exists() or parent.is_symlink()) and not parent.is_dir():
                    raise ValueError(f"instruction parent is not a directory: {parent}")
            if path.is_symlink():
                raise ValueError(f"refusing to replace symlink instruction file: {path}")
            original = path.read_bytes().decode("utf-8") if path.exists() else ""
            updates.append((path, original, managed_content(original, block)))
        stale = False
        for path, original, desired in updates:
            if original == desired:
                print(f"current: {path}")
            elif args.check:
                stale = True
                print(f"missing or stale reference: {path}")
            else:
                replace_file(path, desired)
                print(f"installed: {path}")
        return 1 if stale else 0
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"workflow installation failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
