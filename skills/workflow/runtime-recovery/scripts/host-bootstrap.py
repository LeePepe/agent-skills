#!/usr/bin/env python3
"""Owner-operated, local-only Raven bootstrap. Default action is a read-only plan.

Host settings come from non-secret ~/.config/raven-actions/host.json; --config
selects another file and --owner overrides its runner-label owner. Required JSON:
version (1), owner (unless --owner is given). Optional: default_runners, legacy_labels,
known_prior_launcher_sha256, daily_config (home-relative), python (absolute).
Never sources shell files, accesses auth stores, contacts a provider or controls a
service. Python 3.11+ is required. All error messages deliberately omit input.
"""
from __future__ import annotations

import argparse
import contextlib
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import stat
import sys
import tempfile
import tomllib
from types import MappingProxyType
from typing import Mapping
import uuid

LEGACY_REVIEW_HOME = ".codex-review-raven-actions"
LABEL_PATTERN = r"actions\.runner\.{owner}-[A-Za-z0-9][A-Za-z0-9_-]*\.[A-Za-z0-9][A-Za-z0-9_-]*"
ALLOWED_KEYS = {"OPENAI_API_KEY", "RAVEN_API_KEY"}
CONNECTION_KEYS = {"name", "base_url", "wire_api", "env_key", "requires_openai_auth"}
LAUNCHER = ".local/lib/raven-actions/host-bootstrap.py"
PRIVATE = ".config/raven-actions/client.env"
ALLOWLIST = ".config/raven-actions/runners.json"
STATE = ".local/state/raven-actions"
REVIEW_SOURCE = ".codex-review/config.toml"
HOST_CONFIG = ".config/raven-actions/host.json"
MAX_BYTES = 1024 * 1024


@dataclass(frozen=True)
class HostConfig:
    owner: str
    default_runners: Mapping[str, tuple[str, str]]
    legacy_labels: frozenset[str]
    known_prior_launcher_sha256: frozenset[str]
    daily_config: str
    python: str


class Refusal(Exception):
    pass


def require(ok, message="Validation failed; no input contents shown"):
    if not ok:
        raise Refusal(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def home_path(value):
    p = Path(value).absolute()
    require(p != Path("/") and ".." not in p.parts, "Invalid home path")
    directory(p)
    return p


def directory(path, private=False):
    """Reject symlinks in every ancestor; root-owned ancestors are permitted."""
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts, "Unsafe directory path")
    for current in list(reversed(path.parents)) + [path]:
        s = current.lstat()
        require(stat.S_ISDIR(s.st_mode), "Non-directory or symlink ancestor")
        require(s.st_uid in {0, os.getuid()}, "Unexpected directory owner")
        # macOS /private/tmp and Linux /tmp are acceptable ancestors of test homes.
        writable = s.st_mode & 0o022
        require(not writable or (s.st_uid == 0 and s.st_mode & stat.S_ISVTX),
                "Writable directory ancestor")
    s = path.lstat()
    require(s.st_uid == os.getuid(), "Wrong directory owner")
    if private:
        require(stat.S_IMODE(s.st_mode) == 0o700, "Private directory must be mode 0700")


def ensure_dir(path):
    path = Path(path)
    if not os.path.lexists(path):
        ensure_dir(path.parent)
        path.mkdir(mode=0o700)
    directory(path)


def read_file(path, *, secret=False, optional=False):
    path = Path(path)
    if optional and not os.path.lexists(path):
        # Check existing ancestors even when the leaf does not yet exist.
        parent = path.parent
        while not os.path.lexists(parent):
            parent = parent.parent
        directory(parent, private=secret and parent == path.parent)
        return None
    directory(path.parent, private=secret)
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    fd = os.open(path, flags)
    try:
        s = os.fstat(fd)
        require(stat.S_ISREG(s.st_mode) and s.st_uid == os.getuid(),
                "Unsafe file type or owner")
        mode = stat.S_IMODE(s.st_mode)
        require(mode == 0o600 if secret else not mode & 0o022, "Unsafe file mode")
        require(s.st_nlink == 1, "Hard-linked files are not accepted")
        require(s.st_size <= MAX_BYTES, "File too large")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            data = stream.read(MAX_BYTES + 1)
        require(len(data) <= MAX_BYTES, "File too large")
        after = os.fstat(fd)
        require((s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns) ==
                (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns),
                "File changed during read")
        return {"bytes": data, "mode": mode, "identity":
                (s.st_dev, s.st_ino, s.st_mtime_ns, s.st_ctime_ns)}
    finally:
        os.close(fd)


def same(actual, expected, identity=True):
    if actual is None or expected is None:
        return actual is expected
    return (actual["bytes"] == expected["bytes"] and actual["mode"] == expected["mode"]
            and (not identity or actual["identity"] == expected["identity"]))


def exclusive(path, data, mode=0o600):
    """Publish complete contents without replacing any existing leaf."""
    directory(path.parent)
    fd, name = tempfile.mkstemp(prefix=".raven-new-", dir=path.parent)
    temp = Path(name)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temp, path, follow_symlinks=False)  # Atomic, fails if leaf exists.
    finally:
        temp.unlink()


def replace_checked(path, expected, data, mode):
    """Optimistic compare-and-replace; Owner must quiesce other config writers."""
    require(same(read_file(path, optional=True), expected), "Concurrent change; refused")
    if expected is None:
        exclusive(path, data, mode)
        return
    fd, name = tempfile.mkstemp(prefix=".raven-replace-", dir=path.parent)
    temp = Path(name)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        require(same(read_file(path), expected), "Concurrent change; refused")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def parse_env(data):
    require(len(data) <= 4096, "Private environment is oversized")
    try:
        value = data.decode("ascii")
    except UnicodeError:
        raise Refusal("Invalid private environment encoding") from None
    # One assignment, one optional terminal LF. No export, comments, quoting or eval.
    match = re.fullmatch(r"(OPENAI_API_KEY|RAVEN_API_KEY)=([!-~]+)\n?", value)
    require(match is not None, "Invalid private environment format")
    return {match[1]: match[2]}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate allowlist key")
        result[key] = value
    return result


def valid_label(label, owner):
    return isinstance(label, str) and re.fullmatch(
        LABEL_PATTERN.format(owner=re.escape(owner)), label) is not None


def parse_allowlist(data, owner):
    require(len(data) <= 64 * 1024, "Allowlist is oversized")
    try:
        doc = json.loads(data.decode("utf-8"), object_pairs_hook=unique_object)
    except (UnicodeError, ValueError, RecursionError):
        raise Refusal("Invalid allowlist JSON") from None
    require(isinstance(doc, dict) and set(doc) == {"version", "runners"}, "Invalid allowlist fields")
    require(type(doc["version"]) is int and doc["version"] == 1, "Unsupported allowlist version")
    require(isinstance(doc["runners"], dict) and doc["runners"], "Invalid allowlist runners")
    result, directories = {}, set()
    for label, entry in doc["runners"].items():
        require(valid_label(label, owner), "Invalid runner label")
        require(isinstance(entry, dict) and set(entry) == {"runner_dir", "review_home"},
                "Invalid runner fields")
        runner, review = entry["runner_dir"], entry["review_home"]
        require(isinstance(runner, str) and re.fullmatch(r"actions-runner(-[a-z0-9][a-z0-9-]*)?", runner),
                "Invalid runner directory")
        require(isinstance(review, str) and re.fullmatch(r"\.codex-review-[a-z0-9][a-z0-9-]*", review),
                "Invalid review home")
        require(runner not in directories, "Duplicate runner directory")
        directories.add(runner)
        result[label] = (runner, review)
    return result


def allowlist_document(runners):
    return {"version": 1, "runners": {label: {"runner_dir": runner, "review_home": review}
                                     for label, (runner, review) in runners.items()}}


def load_config(home, path=None, owner=None):
    """Read validated non-secret settings without exposing rejected input."""
    try:
        data = read_file(Path(path).absolute() if path is not None else home / HOST_CONFIG)["bytes"]
        doc = json.loads(data.decode("utf-8"), object_pairs_hook=unique_object)
        require(isinstance(doc, dict) and set(doc) <= {
            "version", "owner", "default_runners", "legacy_labels",
            "known_prior_launcher_sha256", "daily_config", "python"})
        require(type(doc.get("version")) is int and doc["version"] == 1)
        if "owner" in doc:
            require(isinstance(doc["owner"], str) and
                    re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", doc["owner"]))
        owner = doc.get("owner") if owner is None else owner
        require(isinstance(owner, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*", owner))
        defaults = doc.get("default_runners", {})
        require(isinstance(defaults, dict))
        runners = parse_allowlist(json.dumps({"version": 1, "runners": defaults}).encode(), owner) if defaults else {}
        legacy = doc.get("legacy_labels", [])
        require(isinstance(legacy, list) and all(valid_label(label, owner) for label in legacy))
        hashes = doc.get("known_prior_launcher_sha256", [])
        require(isinstance(hashes, list) and all(isinstance(value, str) and
                re.fullmatch(r"[0-9a-fA-F]{64}", value) for value in hashes))
        daily = doc.get("daily_config", ".codex/config.toml")
        require(isinstance(daily, str) and "\x00" not in daily and
                all(part not in {"", ".", ".."} for part in daily.split("/")))
        python = doc.get("python", "/opt/homebrew/bin/python3")
        require(isinstance(python, str) and "\x00" not in python and Path(python).is_absolute())
        return HostConfig(owner, MappingProxyType(runners), frozenset(legacy),
                          frozenset(value.lower() for value in hashes), daily, python)
    except (Refusal, OSError, ValueError, TypeError, RecursionError):
        raise Refusal("Invalid host config") from None


def store_secret(home, key, data):
    require(key in ALLOWED_KEYS, "Unsupported client key name")
    require(b"\n" not in data and b"\r" not in data, "Multiline key rejected")
    payload = key.encode() + b"=" + data + b"\n"
    parse_env(payload)
    parent = home / PRIVATE
    # A .git file/symlink denotes a worktree; a repository directory needs HEAD.
    # Some homes have a non-repository .git directory containing only ignore rules.
    def repository_marker(p):
        marker = p / ".git"
        return os.path.lexists(marker) and (not marker.is_dir() or marker.is_symlink() or
                                           os.path.lexists(marker / "HEAD"))
    require(not any(repository_marker(p) for p in [parent.parent, *parent.parent.parents]),
            "Private environment must be outside Git")
    ensure_dir(parent.parent)
    directory(parent.parent, private=True)
    # Deliberately no update/rotation path and no read of any existing secret.
    exclusive(parent, payload)


def connection(home, config=None):
    config = config or load_config(home)
    # The inspected daily-home alias is known, read-only metadata. Never follow it
    # when opening files: validate its text, then open the canonical physical path.
    alias = home / ".codex"
    if Path(config.daily_config).parent != Path(".codex"):
        require(alias.is_symlink() and os.readlink(alias) == str((home / config.daily_config).parent),
                "Daily-home alias differs from the inspected host layout")
    daily = read_file(home / config.daily_config)
    doc = tomllib.loads(daily["bytes"].decode())
    require(doc.get("model_provider") == "raven", "Daily provider must be raven")
    provider = doc.get("model_providers", {}).get("raven", {})
    require(isinstance(provider, dict), "Invalid daily provider table")
    # Reject auth/header overrides, but do not copy other harmless daily options.
    require(not any(k in provider for k in ("http_headers", "env_http_headers", "experimental_bearer_token")),
            "Unsupported provider authentication override")
    require(provider.get("requires_openai_auth", False) is False,
            "OpenAI auth fallback is not permitted")
    selected = {k: provider[k] for k in CONNECTION_KEYS if k in provider}
    # Explicit local-provider policy, including when the daily config omits it.
    selected["requires_openai_auth"] = False
    validate_connection(selected)
    return selected, daily


def validate_connection(selected):
    require(set(selected) == CONNECTION_KEYS, "Unexpected connection fields")
    require(selected.get("requires_openai_auth") is False, "OpenAI auth fallback is not permitted")
    require(selected.get("name") == "raven", "Unexpected provider name")
    require(selected.get("base_url") in {"http://localhost:7024/v1", "http://127.0.0.1:7024/v1"},
            "Provider endpoint must be the validated local Raven service")
    require(selected.get("wire_api") == "responses", "Responses API required")
    require(selected.get("env_key") in ALLOWED_KEYS, "Unsupported provider environment key")


def review_bytes(before, selected):
    raw = before["bytes"]
    text = raw.decode()
    doc = tomllib.loads(text)
    require(doc.get("sandbox_mode") == "read-only" and doc.get("approval_policy") == "never"
            and doc.get("features", {}).get("hooks") is False and doc.get("mcp_servers", {}) == {},
            "Review isolation contract mismatch")
    require("auth" not in doc and "api_key" not in doc, "Unexpected review authentication data")
    if "model_provider" in doc or "model_providers" in doc:
        require(doc.get("model_provider") == "raven" and
                doc.get("model_providers") == {"raven": selected},
                "Existing review provider differs; refusing overwrite")
        return raw
    suffix = "\n\n[model_providers.raven]\n" + "".join(
        f"{key} = {json.dumps(selected[key])}\n" for key in sorted(selected))
    result = ('model_provider = "raven"\n' + text + suffix).encode()
    parsed = tomllib.loads(result.decode())
    parsed.pop("model_provider")
    parsed.pop("model_providers")
    require(parsed == doc, "Review fields would change")
    return result


def launcher_prefix(home, python, label):
    return [python, str(home / LAUNCHER), "run", "--label", label, "--"]


def validate_plist(home, label, runner_dir, raw, python):
    doc = plistlib.loads(raw)
    require(doc.get("Label") == label, "Runner label mismatch")
    require(doc.get("WorkingDirectory") == str(home / runner_dir), "Runner directory mismatch")
    require("Program" not in doc, "Unexpected Program override")
    env = doc.get("EnvironmentVariables", {})
    require(isinstance(env, dict) and set(env) <= {"ACTIONS_RUNNER_SVC"},
            "Unexpected plist environment names; do not copy credential stores")
    args = doc.get("ProgramArguments")
    require(isinstance(args, list) and all(isinstance(a, str) and "\x00" not in a for a in args),
            "Invalid runner arguments")
    prefix = launcher_prefix(home, python, label)
    installed = args[:len(prefix)] == prefix
    original = args[len(prefix):] if installed else args
    require(original and original[0] == str(home / runner_dir / "runsvc.sh"),
            "Unexpected runner executable")
    # Preserve all properties and original arguments, including unrelated flags.
    if not installed:
        doc["ProgramArguments"] = prefix + original
    result = raw if installed else plistlib.dumps(doc, fmt=plistlib.FMT_XML, sort_keys=False)
    return result


def source_snapshot():
    return read_file(Path(__file__).absolute())


def change(rel, new, mode, before, kind):
    action = "create" if before is None else (
        "unchanged" if before["bytes"] == new and before["mode"] == mode else "replace")
    return {"path": rel, "before": before, "new": new, "mode": mode, "kind": kind, "action": action}


def review_changes(home, runners, new):
    changes = []
    for review_home in sorted({review for _, review in runners.values()}):
        rel = f"{review_home}/config.toml"
        before = read_file(home / rel, secret=True, optional=True)
        if before is not None:
            require(before["bytes"] == new and before["mode"] == 0o600,
                    "Unknown dedicated profile; refusing overwrite")
        changes.append(change(rel, new, 0o600, before, "review_home"))
    return changes


def launcher_change(home, source, config):
    before = read_file(home / LAUNCHER, optional=True)
    if before is not None:
        require(before["mode"] == 0o700 and (before["bytes"] == source["bytes"] or
                digest(before["bytes"]) in config.known_prior_launcher_sha256),
                "Unknown stable launcher; refusing overwrite")
    return change(LAUNCHER, source["bytes"], 0o700, before, "launcher")


def plan(home, python, add_runners=(), config=None):
    config = config or load_config(home)
    require(Path(python).is_absolute() and os.access(python, os.X_OK), "Invalid Python executable")
    selected, daily = connection(home, config)
    source = source_snapshot()
    review_source = read_file(home / REVIEW_SOURCE)
    source_doc = tomllib.loads(review_source["bytes"].decode())
    require(set(source_doc) <= {"model", "model_reasoning_effort", "approval_policy", "sandbox_mode",
                                "features", "mcp_servers"} and source_doc.get("features") == {"hooks": False},
            "Unexpected shared review settings; refusing to copy")
    allowlist = read_file(home / ALLOWLIST, secret=True, optional=True)
    new = allowlist["bytes"] if allowlist else (
        json.dumps(allowlist_document(config.default_runners), indent=2, sort_keys=True) + "\n").encode()
    runners = parse_allowlist(new, config.owner) if allowlist or config.default_runners or not add_runners else {}
    added = []
    for spec in add_runners:
        label, equals, paths = spec.partition("=")
        runner_dir, colon, review_home = paths.partition(":")
        require(equals and colon, "Invalid add-runner specification")
        entry = (runner_dir, review_home)
        if label in runners:
            require(runners[label] == entry, "Runner label already has different values")
        else:
            require(review_home != LEGACY_REVIEW_HOME and
                    review_home not in {review for _, review in runners.values()},
                    "New runner requires an independent review home")
            runners[label] = entry
            added.append(label)
    if added:
        new = (json.dumps(allowlist_document(runners), indent=2, sort_keys=True) + "\n").encode()
        runners = parse_allowlist(new, config.owner)
    changes = [change(ALLOWLIST, new, 0o600, allowlist, "allowlist")]
    changes.extend(review_changes(home, runners, review_bytes(review_source, selected)))
    changes.append(launcher_change(home, source, config))
    for label, (runner_dir, _) in sorted(runners.items()):
        rel = f"Library/LaunchAgents/{label}.plist"
        before = read_file(home / rel)
        new = validate_plist(home, label, runner_dir, before["bytes"], python)
        changes.append(change(rel, new, before["mode"], before, "plist"))
    public = {"home": str(home), "python": python, "connection": selected,
              "daily_source": str(home / config.daily_config),
              "source_sha256": digest(source["bytes"]), "daily_sha256": digest(daily["bytes"]),
              "review_source": str(home / REVIEW_SOURCE),
              "review_source_sha256": digest(review_source["bytes"]),
              "review_source_mode": review_source["mode"],
              "review_source_identity": review_source["identity"],
              "allowlist": {"path": str(home / ALLOWLIST),
                            "source": "existing" if allowlist else "seed-default",
                            "runners": allowlist_document(runners)["runners"]},
              "rollback_manifest": str(home / STATE / "txn-<random>" / "manifest.json") +
                                   " (created only by --apply)",
              "changes": [{"path": c["path"], "before_sha256":
                           digest(c["before"]["bytes"]) if c["before"] else None,
                           "after_sha256": digest(c["new"]), "mode": c["mode"],
                           "action": c["action"], "kind": c["kind"]} for c in changes]}
    if add_runners:
        public["allowlist"]["added_labels"] = sorted(added)
        if added:
            public["allowlist"]["source"] += "+added"
    plan_id = digest(json.dumps(public, sort_keys=True).encode())
    return {"id": plan_id, "public": public, "changes": changes, "daily": daily,
            "review_source": review_source}


@contextlib.contextmanager
def lock(home):
    state = home / STATE
    ensure_dir(state)
    directory(state, private=True)
    path = state / "operation.lock"
    # Never auto-delete another operation's lock; stale locks need Owner review.
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    os.close(fd)
    identity = path.lstat().st_ino
    try:
        yield
    finally:
        if path.lstat().st_ino == identity:
            path.unlink()


def write_manifest(path, doc):
    before = read_file(path, optional=True)
    replace_checked(path, before, (json.dumps(doc, indent=2, sort_keys=True) + "\n").encode(), 0o600)


def apply(home, python, approved, add_runners=(), config=None):
    config = config or load_config(home)
    # First validate without creating directories or locks.
    current = plan(home, python, add_runners, config)
    require(approved == current["id"], "Plan approval missing or stale")
    secret = parse_env(read_file(home / PRIVATE, secret=True)["bytes"])
    require(current["public"]["connection"]["env_key"] in secret, "Required client key name missing")
    del secret
    with lock(home):
        current = plan(home, python, add_runners, config)
        require(approved == current["id"], "Plan changed after approval")
        changes = [c for c in current["changes"] if c["action"] != "unchanged"]
        if not changes:
            return None
        transaction = home / STATE / ("txn-" + uuid.uuid4().hex)
        transaction.mkdir(mode=0o700)
        manifest_path = transaction / "manifest.json"
        manifest = {"version": 1, "home": str(home), "plan": approved,
                    "status": "prepared", "records": []}
        for i, c in enumerate(changes):
            before = c["before"]
            backup = f"before-{i}.bin" if before else None
            if before:
                exclusive(transaction / backup, before["bytes"])
            manifest["records"].append({"path": c["path"], "backup": backup,
                                         "before_sha256": digest(before["bytes"]) if before else None,
                                         "before_mode": before["mode"] if before else None,
                                         "after_sha256": digest(c["new"]), "after_mode": c["mode"]})
        write_manifest(manifest_path, manifest)
        # Preflight the entire set again before any target writes.
        require(same(read_file(home / config.daily_config), current["daily"]), "Daily config changed")
        require(same(read_file(home / REVIEW_SOURCE), current["review_source"]), "Shared review source changed")
        for c in current["changes"]:
            require(same(read_file(home / c["path"], optional=True,
                                   secret=c["kind"] in {"allowlist", "review_home"}), c["before"]),
                    "Target changed")
        try:
            for c in changes:
                require(same(read_file(home / REVIEW_SOURCE), current["review_source"]), "Shared review source changed")
                ensure_dir((home / c["path"]).parent)
                if c["kind"] in {"allowlist", "review_home"}:
                    directory((home / c["path"]).parent, private=True)
                replace_checked(home / c["path"], c["before"], c["new"], c["mode"])
            manifest["status"] = "installed"
            write_manifest(manifest_path, manifest)
        except Exception:
            # The prewritten journal supports guarded manual rollback after interruption.
            print("Installation interrupted; use guarded rollback manifest: " + str(manifest_path), file=sys.stderr)
            raise
        return manifest_path


def rollback_paths(home, config=None):
    config = config or load_config(home)
    allowlist = read_file(home / ALLOWLIST, secret=True, optional=True)
    runners = parse_allowlist(allowlist["bytes"], config.owner) if allowlist else {}
    labels = set(runners) | set(config.default_runners) | config.legacy_labels
    reviews = {review for _, review in [*runners.values(), *config.default_runners.values()]}
    reviews.add(LEGACY_REVIEW_HOME)
    private = {ALLOWLIST} | {f"{review}/config.toml" for review in reviews}
    created = private | {LAUNCHER}
    allowed = created | {f"Library/LaunchAgents/{label}.plist" for label in labels}
    return allowed, created, private


def rollback(home, manifest_path, do_apply=False, config=None):
    config = config or load_config(home)
    manifest_path = Path(manifest_path).absolute()
    require(manifest_path.parent.parent == home / STATE and
            re.fullmatch(r"txn-[0-9a-f]{32}", manifest_path.parent.name) and
            manifest_path.name == "manifest.json", "Unrecognized rollback manifest path")
    manifest = json.loads(read_file(manifest_path)["bytes"])
    require(manifest.get("version") == 1 and manifest.get("home") == str(home), "Manifest mismatch")
    require(manifest.get("status") in {"prepared", "installed", "rolled_back"}, "Invalid manifest status")
    allowed, created, private = rollback_paths(home, config)
    work = []
    seen = set()
    for i, r in enumerate(manifest["records"]):
        rel = r["path"]
        require(rel in allowed and rel not in seen, "Invalid rollback target")
        seen.add(rel)
        before = None
        if r["backup"] is not None:
            require(r["backup"] == f"before-{i}.bin", "Invalid backup path")
            backup = read_file(manifest_path.parent / r["backup"], secret=rel in private)
            require(digest(backup["bytes"]) == r["before_sha256"], "Backup changed")
            require(isinstance(r["before_mode"], int) and 0 <= r["before_mode"] <= 0o777 and
                    not r["before_mode"] & 0o022, "Invalid backup mode")
            before = {"bytes": backup["bytes"], "mode": r["before_mode"]}
        else:
            require(rel in created and r["before_sha256"] is None and r["before_mode"] is None,
                    "Invalid absent backup")
        actual = read_file(home / rel, secret=rel in private, optional=True)
        if same(actual, before, identity=False):
            continue
        require(actual is not None and digest(actual["bytes"]) == r["after_sha256"] and
                actual["mode"] == r["after_mode"], "Concurrent change blocks entire rollback")
        work.append((home / rel, actual, before))
    if not do_apply:
        return len(work)
    # Caller holds the operation lock. All targets were checked before the first write.
    for path, actual, before in reversed(work):
        require(same(read_file(path, secret=str(path.relative_to(home)) in private), actual),
                "Concurrent change blocks rollback")
        if before is None:
            path.unlink()
        else:
            replace_checked(path, actual, before["bytes"], before["mode"])
    manifest["status"] = "rolled_back"
    write_manifest(manifest_path, manifest)
    return len(work)


def runner_environment(home, label, args, inherited, config=None):
    config = config or load_config(home)
    require(valid_label(label, config.owner), "Invalid runner label")
    allowlist = read_file(home / ALLOWLIST, secret=True, optional=True)
    require(allowlist is not None, "Runner allowlist missing")
    runners = parse_allowlist(allowlist["bytes"], config.owner)
    require(label in runners, "Unknown runner label")
    runner_dir, review_home = runners[label]
    require(args and args[0] == str(home / runner_dir / "runsvc.sh"), "Unexpected runner entry")
    profile = read_file(home / review_home / "config.toml", secret=True)
    selected = tomllib.loads(profile["bytes"].decode())
    provider = selected.get("model_providers", {}).get("raven", {})
    validate_connection(provider)
    review_bytes(profile, provider)
    private = parse_env(read_file(home / PRIVATE, secret=True)["bytes"])
    require(provider["env_key"] in private, "Required client key name missing")
    result = dict(inherited)
    # Never fall back to an inherited client key or a GitHub/Copilot credential.
    for key in ALLOWED_KEYS:
        result.pop(key, None)
    result.update(private)
    # Trusted-base compatibility: legacy shells select CODEX_HOME, while new
    # callers select CODEX_REVIEW_HOME. Both must use the profile validated above.
    # Change only this copied subprocess environment, never the parent's mapping.
    result["CODEX_HOME"] = str(home / review_home)
    result["CODEX_REVIEW_HOME"] = str(home / review_home)
    return result


def print_summary(public):
    changes = public["changes"]
    if "added_labels" in public["allowlist"]:
        print("ALLOWLIST SOURCE: " + public["allowlist"]["source"])
        print("ADDED RUNNERS:")
        for label in public["allowlist"]["added_labels"] or ["(none)"]:
            print("  " + label)
    sections = {
        "FILES TO WRITE": [f"{c['action']}: {c['path']}" for c in changes if c["action"] != "unchanged"],
        "PLISTS REWRITTEN": [Path(c["path"]).stem for c in changes
                             if c["kind"] == "plist" and c["action"] == "replace"],
        "UNCHANGED": [c["path"] for c in changes if c["action"] == "unchanged"],
        "ROLLBACK MANIFEST": [public["rollback_manifest"]],
    }
    for title, lines in sections.items():
        print(title + ":")
        for line in lines or ["(none)"]:
            print("  " + line)


class SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise Refusal("Invalid command-line arguments")


def main():
    parser = SafeArgumentParser(description=__doc__)
    parser.add_argument("command", nargs="?", choices=["install", "rollback", "secret-write", "run"], default="install")
    parser.add_argument("--home", default=str(Path.home()), help="Synthetic test home override; normal Owner use omits this")
    parser.add_argument("--config", metavar="PATH", help="Non-secret host JSON (default: <home>/.config/raven-actions/host.json)")
    parser.add_argument("--owner", metavar="OWNER", help="Override the configured runner-label owner")
    parser.add_argument("--apply", action="store_true", help="Explicitly permit local writes (never services)")
    parser.add_argument("--dry-run", action="store_true", help="Default; no writes")
    parser.add_argument("--approve-plan", default="")
    parser.add_argument("--manifest")
    parser.add_argument("--key", choices=sorted(ALLOWED_KEYS), default="OPENAI_API_KEY")
    parser.add_argument("--label")
    parser.add_argument("--add-runner", action="append", default=[], metavar="LABEL=RUNNER_DIR:REVIEW_HOME",
                        help="Install only; repeat to add allowlisted runners without replacing entries")
    # Original runner arguments are separated before argparse so flags are never interpreted.
    argv = sys.argv[1:]
    runner_args = []
    if "--" in argv:
        index = argv.index("--")
        runner_args, argv = argv[index + 1:], argv[:index]
    args = parser.parse_args(argv)
    require(not (args.apply and args.dry_run), "Choose apply or dry-run")
    require(not runner_args or args.command == "run", "Unexpected trailing arguments")
    require(not args.add_runner or args.command == "install", "Add-runner requires install")
    home = home_path(args.home)
    config = load_config(home, args.config, args.owner)
    python = config.python
    if args.command == "install":
        if args.apply:
            manifest = apply(home, python, args.approve_plan, args.add_runner, config)
            print("Local files installed; services untouched. Manifest: " + str(manifest) if manifest else
                  "Already installed; no target changes. Services untouched.")
        else:
            current = plan(home, python, args.add_runner, config)
            if args.approve_plan:
                require(args.approve_plan == current["id"], "Plan approval missing or stale")
            print(json.dumps({"mode": "DRY-RUN", "plan_id": current["id"], **current["public"]}, indent=2))
            print_summary(current["public"])
            print("No files written; private key NOT read; no service or model requests.")
    elif args.command == "secret-write":
        require(args.apply and not args.dry_run, "Secret persistence requires explicit --apply")
        require(args.approve_plan == plan(home, python, config=config)["id"], "Plan approval missing or stale")
        store_secret(home, args.key, sys.stdin.buffer.read(4097))
        print("Existing client key persisted owner-only; value not displayed.")
    elif args.command == "rollback":
        require(args.manifest is not None, "Rollback manifest required")
        if args.apply:
            with lock(home):
                count = rollback(home, args.manifest, True, config)
        else:
            count = rollback(home, args.manifest, config=config)
        print(f"Rollback {'applied' if args.apply else 'DRY-RUN'}: {count} target(s); services untouched.")
    elif args.command == "run":
        require(not args.apply and not args.dry_run, "Invalid runner options")
        env = runner_environment(home, args.label, runner_args, os.environ, config)
        os.execve(runner_args[0], runner_args, env)


if __name__ == "__main__":
    try:
        main()
    except (Refusal, OSError, ValueError, KeyError, TypeError, plistlib.InvalidFileException):
        # Parser errors can embed source text: never print exception strings or tracebacks.
        print("REFUSED: unsafe, changed, missing or invalid setup input; no credential contents shown.", file=sys.stderr)
        sys.exit(2)
