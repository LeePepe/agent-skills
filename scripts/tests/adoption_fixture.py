"""Offline catalog fixtures; execute only the admitted published provider tree."""
import os
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
PIN = "9b411bc8c523c536efc65a01fbe204d75c5fc869"
TREE = "d7f74010b31ec85cb457c499d5eaaddb92451fc2"


def environment():
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "PYTHON"))}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
               GIT_NO_REPLACE_OBJECTS="1", PYTHONDONTWRITEBYTECODE="1",
               GIT_TERMINAL_PROMPT="0", GIT_ALLOW_PROTOCOL="file")
    return env


def run(root, *args, env=None, check=True, timeout=60):
    return subprocess.run(args, cwd=root, env=environment() if env is None else env,
                          capture_output=True, text=True, check=check, timeout=timeout)


def git(root, *args):
    return run(root, "git", *args).stdout.strip()


def initialize(root):
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "maintenance.auto", "false")
    git(root, "config", "user.name", "Fixture")
    git(root, "config", "user.email", "fixture@example.invalid")


def workflow(provider, text):
    """Use the admitted provider parser, never a second YAML implementation."""
    spec = importlib.util.spec_from_file_location(
        "catalog_provider_yaml", provider / "scripts/context/_frontmatter.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.parse(text)


def materialize_provider(source, destination):
    """Fetch local approved objects only, then verify every checked-out byte/mode.

    Never copy the source worktree or substitute its current HEAD. Missing objects
    are a hard failure; no network, registry fixture, installer or fallback.
    """
    source = Path(source).resolve(strict=True)
    if git(source, "rev-parse", PIN + "^{tree}") != TREE:
        raise RuntimeError("published provider tree identity mismatch")
    if destination.exists():
        raise RuntimeError("fixture destination must be absent")
    initialize(destination)
    git(destination, "fetch", "-q", "--no-tags", "--depth=1", str(source), PIN)
    git(destination, "checkout", "-q", "--detach", PIN)
    if git(destination, "rev-parse", "HEAD") != PIN:
        raise RuntimeError("fixture checkout is not the admitted provider")
    expected = git(source, "ls-tree", "-r", PIN)
    if git(destination, "ls-tree", "-r", "HEAD") != expected:
        raise RuntimeError("fixture object inventory differs from published source")
    for row in expected.splitlines():
        metadata, relative = row.split("\t", 1)
        mode, kind, blob = metadata.split()
        path = destination / relative
        if kind != "blob" or mode not in ("100644", "100755") or path.is_symlink():
            raise RuntimeError("unsupported provider fixture entry: " + relative)
        if git(destination, "hash-object", "--no-filters", "--", relative) != blob:
            raise RuntimeError("provider fixture bytes differ: " + relative)
        if bool(path.stat().st_mode & 0o111) != (mode == "100755"):
            raise RuntimeError("provider fixture mode differs: " + relative)
    if git(destination, "status", "--porcelain", "--ignored"):
        raise RuntimeError("provider fixture is not clean")
    return destination


class ProviderFixture:
    def __init__(self):
        source = os.environ.get("SHARED_CI_SOURCE")
        if not source:
            raise RuntimeError("SHARED_CI_SOURCE must identify local approved provider objects; no skip/fallback")
        self.temp = tempfile.TemporaryDirectory(prefix="catalog-provider-")
        try:
            self.root = materialize_provider(source, Path(self.temp.name).resolve() / "provider")
        except Exception:
            self.temp.cleanup()
            raise

    def close(self):
        self.temp.cleanup()


class CatalogFixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory(prefix="catalog-adoption-")
        self.root = Path(self.temp.name).resolve() / "catalog"
        initialize(self.root)
        # The index defines the candidate inventory; use its worktree bytes so
        # pre-commit regression runs test the actual staged/new implementation.
        tracked = run(ROOT, "git", "ls-files", "-z").stdout.split("\0")
        for relative in filter(None, tracked):
            source = ROOT / relative
            if not source.exists():
                continue
            if source.is_symlink():
                raise RuntimeError("unexpected catalog fixture symlink: " + relative)
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        self.commit("catalog candidate")

    def close(self):
        self.temp.cleanup()

    def write(self, relative, content):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def commit(self, message="fixture"):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", message)
        return git(self.root, "rev-parse", "HEAD")

    def context(self, provider, *args):
        return run(self.root, sys.executable, "-I", "-B",
                   str(provider / "scripts/context/_context.py"), *args, check=False)


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] != "--materialize-provider":
        raise SystemExit("usage: adoption_fixture.py --materialize-provider SOURCE ABSENT_DESTINATION")
    result = materialize_provider(Path(sys.argv[2]), Path(sys.argv[3]))
    print("byte/mode-verified published provider:", PIN, TREE, result)
