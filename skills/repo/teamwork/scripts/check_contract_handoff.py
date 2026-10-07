"""Read-only compatibility check for the actual selected role, never a role selector."""
import argparse
from pathlib import Path
import re
import sys


SECTIONS = {
    "team-lead": "Required workflow contract handoff",
    "git-monitor": "Required workflow contract",
}


def required_section(text, heading):
    match = re.search(r"^## " + re.escape(heading) + r"\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return match.group(1).strip() if match else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", choices=SECTIONS)
    parser.add_argument("selected_role", type=Path)
    args = parser.parse_args()
    canonical = Path(__file__).resolve().parents[1] / "agents" / f"{args.role}.md"
    try:
        expected = required_section(canonical.read_text(), SECTIONS[args.role])
        selected = args.selected_role.read_text()
        actual = required_section(selected, SECTIONS[args.role])
    except (OSError, UnicodeError):
        print(f"setup blocked: {args.role} contract interface is unreadable", file=sys.stderr)
        return 1
    if not expected or actual != expected:
        print(f"setup blocked: selected {args.role} lacks the loaded bundle's required handoff interface; preserve the override", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
