#!/usr/bin/env python3
"""Parse tracked Python/shell sources without running installers or consumer code."""
import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    count = 0
    for relative in filter(None, tracked):
        path = ROOT / relative
        if not path.is_file() or path.is_symlink():
            continue
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        elif path.suffix == ".sh" or path.read_bytes().startswith((b"#!/usr/bin/env bash", b"#!/bin/bash")):
            subprocess.run(["bash", "-n", str(path)], check=True, cwd=ROOT)
        else:
            continue
        count += 1
    print(f"syntax: {count} tracked Python/shell sources passed")


if __name__ == "__main__":
    main()
