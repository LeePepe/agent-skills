#!/usr/bin/env python3
"""Read the maintained CI pin and validate entrypoint routes, not policy prose.

This caller-side consistency check does not replace the pinned provider audit.
"""
import argparse
import os
import re
import stat
import subprocess
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit

USES = re.compile(r"^\s*(?:-\s*)?uses:\s*['\"]?LeePepe/shared-ci/([^@\s'\"]+)@([^\s'\"#]+)", re.M | re.I)
LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
PROVIDER_DOC = re.compile(r"https://github\.com/LeePepe/shared-ci/(?:blob|tree)/([^/]+)/ai(?:/|\b)")


def tracked_modes(root):
    names = subprocess.check_output(["git", "rev-parse", "--local-env-vars"], text=True).splitlines()
    env = {key: value for key, value in os.environ.items() if key not in names}
    try:
        actual = subprocess.check_output(["git", "-C", str(root), "rev-parse", "--show-toplevel"],
                                         env=env, text=True, stderr=subprocess.PIPE).strip()
        if Path(actual).resolve() != root.resolve():
            raise ValueError("entrypoint root must be the Git worktree root")
        output = subprocess.check_output(["git", "-C", str(root), "ls-files", "--stage", "-z"], env=env)
    except subprocess.CalledProcessError as error:
        raise ValueError("cannot read the target repository index") from error
    modes = {}
    for record in filter(None, output.decode("utf-8").split("\0")):
        metadata, path = record.split("\t", 1)
        mode, _, stage = metadata.split()
        if stage != "0":
            raise ValueError(f"unmerged tracked path: {path}")
        modes[path] = mode
    return modes


def safe_target(root, relative):
    path = Path(relative)
    if (path.is_absolute() or ".." in path.parts or "\\" in relative
            or any(ord(char) < 32 for char in relative)):
        raise ValueError(f"unsupported or escaping local route: {relative}")
    target = root
    for part in path.parts:
        target = target / part
        if target.is_symlink():
            raise ValueError(f"symlink route is unsupported: {relative}")
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"escaping local route: {relative}")
    return target


def read_tracked(root, relative, modes):
    path = safe_target(root, relative)
    if modes.get(Path(relative).as_posix()) not in ("100644", "100755"):
        raise ValueError(f"route must be a tracked regular file: {relative}")
    if not path.is_file() or not stat.S_ISREG(path.stat().st_mode) or not path.stat().st_mode & 0o444:
        raise ValueError(f"route is not a readable regular file: {relative}")
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ValueError(f"route must be readable UTF-8 text: {relative}") from error


def markdown_fragments(text):
    """Plain ATX headings only; code fences ignored, duplicate slugs numbered."""
    fragments, counts, fence = set(), {}, None
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if marker:
            token, tail = marker.groups()
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not tail.strip():
                fence = None
            continue
        if fence is not None:
            continue
        heading = re.match(r"^ {0,3}#{1,6}\s+(.+?)(?:\s+#+)?\s*$", line)
        if not heading or re.search(r"[\[\]<>\\`*&]", heading.group(1)):
            continue  # Rich/HTML headings are outside this checker's documented subset.
        base = "".join(char for char in heading.group(1).lower()
                       if char.isalnum() or unicodedata.category(char).startswith("M") or char in " _-").replace(" ", "-")
        if base:
            number = counts.get(base, 0)
            slug = base if number == 0 else f"{base}-{number}"
            while slug in fragments:
                number += 1
                slug = f"{base}-{number}"
            counts[base] = number + 1
            fragments.add(slug)
    return fragments


def shared_ci_pin(root):
    modes = tracked_modes(root)
    quality = [revision for path, revision in USES.findall(read_tracked(root, ".github/workflows/ci.yml", modes))
               if path == ".github/workflows/quality.yml"]
    if len(quality) != 1 or not re.fullmatch(r"[0-9a-f]{40}", quality[0]):
        raise ValueError("quality caller must contain one full-SHA shared-ci revision")
    pin = quality[0]
    for workflow in sorted((root / ".github/workflows").iterdir()):
        if workflow.suffix in (".yml", ".yaml"):
            text = read_tracked(root, workflow.relative_to(root).as_posix(), modes)
            if any(revision != pin for _, revision in USES.findall(text)):
                raise ValueError(f"{workflow.name}: shared-ci caller revisions differ")
    return pin


def validate_routes(root, text, pin):
    modes = tracked_modes(root)
    protocol = f"https://github.com/LeePepe/shared-ci/blob/{pin}/ai/agent-protocol.md"
    links = LINK.findall(text)
    remainder = LINK.sub("", text)
    if re.search(r"\[[^\]\n]+\]\s*(?:\[|:|\()|<(?:https?://|\./|\.\./)", remainder):
        raise ValueError("unsupported route syntax: use simple inline Markdown links")
    if protocol not in links:
        raise ValueError("entrypoint must link to the quality caller's exact protocol revision")
    if any(revision != pin for revision in PROVIDER_DOC.findall(text)):
        raise ValueError("provider documentation revision differs from the quality caller")
    for link in links:
        if re.search(r"\s|[<>\"\\]|%(?![0-9a-fA-F]{2})", link):
            raise ValueError(f"unsupported inline route syntax: {link}")
        parsed = urlsplit(link)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            continue
        if parsed.scheme or parsed.netloc or parsed.query:
            raise ValueError(f"unsupported local route: {link}")
        relative = unquote(parsed.path, errors="strict") or "AGENTS.md"
        if parsed.path.endswith("/"):
            target = safe_target(root, relative)
            children = [path for path in modes if path.startswith(Path(relative).as_posix().rstrip("/") + "/")]
            if parsed.fragment or not target.is_dir() or not children:
                raise ValueError(f"directory route requires tracked contents and no fragment: {link}")
            for child in children:
                read_tracked(root, child, modes)
            continue
        contents = read_tracked(root, relative, modes)
        if parsed.fragment:
            fragment = unquote(parsed.fragment, errors="strict")
            if Path(relative).suffix.lower() != ".md" or fragment not in markdown_fragments(contents):
                raise ValueError(f"missing or unsupported named fragment (plain Markdown ATX headings only): {link}")
    return len(links)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--pin", action="store_true", help="read the revision from CI for bootstrap")
    args = parser.parse_args()
    try:
        pin = shared_ci_pin(args.root)
        if args.pin:
            print(pin)
        else:
            count = validate_routes(args.root, read_tracked(args.root, "AGENTS.md", tracked_modes(args.root)), pin)
            print(f"entrypoint: {count} routes checked; caller/protocol/provider revisions agree")
    except (OSError, ValueError) as error:
        parser.exit(1, f"entrypoint: {error}\n")


if __name__ == "__main__":
    main()
