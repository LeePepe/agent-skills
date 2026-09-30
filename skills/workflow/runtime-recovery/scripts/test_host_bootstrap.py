"""Offline tests. Every write targets a disposable synthetic home under the system temporary directory."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import plistlib
import stat
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("bootstrap", ROOT / "host-bootstrap.py")
b = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = b
spec.loader.exec_module(b)
PYTHON = sys.executable
OWNER = "example-owner"
DAILY_PATH = "daily-config/config.toml"
LEGACY_LABELS = {
    "actions.runner.example-owner-alpha.alpha-mac",
    "actions.runner.example-owner-beta.beta-mac",
    "actions.runner.example-owner-gamma.gamma-mac",
}
DEFAULT_RUNNERS = {
    "actions.runner.example-owner-alpha.alpha-mac": ("actions-runner", b.LEGACY_REVIEW_HOME),
    "actions.runner.example-owner-beta.beta-mac": ("actions-runner-beta", b.LEGACY_REVIEW_HOME),
    "actions.runner.example-owner-gamma.gamma-mac": ("actions-runner-gamma-mac", b.LEGACY_REVIEW_HOME),
    "actions.runner.example-owner-shared-ci.shared-ci-mac": ("actions-runner-shared-ci", ".codex-review-shared-ci"),
}
REVIEW = b.LEGACY_REVIEW_HOME + "/config.toml"
SHARED_LABEL = "actions.runner.example-owner-shared-ci.shared-ci-mac"
SHARED_REVIEW = ".codex-review-shared-ci/config.toml"
ADDED_LABEL = "actions.runner.example-owner-shared-telemetry.shared-telemetry-mac"
ADDED_RUNNER = "actions-runner-shared-telemetry"
ADDED_HOME = ".codex-review-shared-telemetry"
ADDED_SPEC = f"{ADDED_LABEL}={ADDED_RUNNER}:{ADDED_HOME}"
PROFILE = b'''# Keep this comment and all existing controls.
model = "fixture-review-model"
model_reasoning_effort = "medium"
approval_policy = "never"
sandbox_mode = "read-only"
[features]
hooks = false
[mcp_servers]
'''
DAILY = b'''model_provider = "raven"
model = "must-not-copy"
model_reasoning_effort = "high"
[features]
hooks = true
[model_providers.raven]
name = "raven"
base_url = "http://localhost:7024/v1"
wire_api = "responses"
env_key = "OPENAI_API_KEY"
'''


class AllowlistTests(unittest.TestCase):
    label = "actions.runner.example-owner-Fixture_1.mac-1"

    def document(self):
        return {"version": 1, "runners": {self.label: {
            "runner_dir": "actions-runner", "review_home": ".codex-review-fixture"}}}

    def assert_refused(self, data):
        raw = data if isinstance(data, bytes) else json.dumps(data).encode()
        with self.assertRaises(b.Refusal) as error:
            b.parse_allowlist(raw, OWNER)
        self.assertNotIn("INPUT_MARKER", str(error.exception))
        self.assertNotIn(self.label, str(error.exception))

    def test_good_document_and_shared_review_home(self):
        doc = self.document()
        doc["runners"][SHARED_LABEL] = {"runner_dir": "actions-runner-shared-ci",
                                        "review_home": ".codex-review-fixture"}
        self.assertEqual(b.parse_allowlist(json.dumps(doc).encode(), OWNER), {
            self.label: ("actions-runner", ".codex-review-fixture"),
            SHARED_LABEL: ("actions-runner-shared-ci", ".codex-review-fixture")})

    def test_bad_versions(self):
        for version in (0, 2, -1, True, False, 1.0, "1", None, {}, []):
            with self.subTest(version=version):
                doc = self.document()
                doc["version"] = version
                self.assert_refused(doc)

    def test_exact_top_level_and_entry_keys_and_types(self):
        for doc in ({}, [], None, {"version": 1}, {"runners": {}},
                    {**self.document(), "INPUT_MARKER": "extra"}):
            self.assert_refused(doc)
        for runners in ({}, [], None, "INPUT_MARKER"):
            self.assert_refused({"version": 1, "runners": runners})
        for entry in ({}, {"runner_dir": "actions-runner"}, {"review_home": ".codex-review-fixture"},
                      {**self.document()["runners"][self.label], "INPUT_MARKER": "extra"},
                      [], None, "INPUT_MARKER"):
            self.assert_refused({"version": 1, "runners": {self.label: entry}})
        for field in ("runner_dir", "review_home"):
            for value in (1, None, [], {}, True):
                doc = self.document()
                doc["runners"][self.label][field] = value
                self.assert_refused(doc)

    def test_bad_label_patterns(self):
        for label in ("actions.runner.Other-INPUT_MARKER.mac", "../INPUT_MARKER", "../",
                      "actions.runner.example-owner-../INPUT_MARKER.mac", "actions.runner.example-owner-A.mac/../x",
                      "actions.runner.example-owner-INPUT_MARKER.mac name", "actions.runner.example-owner-.mac",
                      "actions.runner.example-owner-A._mac", "actions.runner.example-owner-A.mac.extra",
                      "actions.runner.example-owner-A.mac\n", "", "INPUT_MARKER"):
            with self.subTest(label=label):
                self.assert_refused({"version": 1, "runners": {label: self.document()["runners"][self.label]}})

    def test_bad_runner_directories(self):
        for runner in ("../x", "/abs", "foo", "actions-runner-", "actions-runner-UPPER",
                       "actions-runner-x/y", "actions-runner-x\n", "INPUT_MARKER"):
            with self.subTest(runner=runner):
                doc = self.document()
                doc["runners"][self.label]["runner_dir"] = runner
                self.assert_refused(doc)

    def test_bad_review_homes(self):
        for review in (".codex-review", ".codex", "x/y", "..", ".codex-review-UPPER",
                       ".codex-review-", ".codex-review-x/../y", ".codex-review-x\n", "INPUT_MARKER"):
            with self.subTest(review=review):
                doc = self.document()
                doc["runners"][self.label]["review_home"] = review
                self.assert_refused(doc)

    def test_duplicate_runner_directory(self):
        doc = self.document()
        doc["runners"][SHARED_LABEL] = {"runner_dir": "actions-runner", "review_home": ".codex-review-other"}
        self.assert_refused(doc)

    def test_duplicate_json_keys_at_every_level(self):
        raw = json.dumps(self.document()).encode()
        for bad in (raw.replace(b'"version": 1', b'"version": 1, "version": 1'),
                    raw.replace(b'"runner_dir": "actions-runner"',
                                b'"runner_dir": "actions-runner", "runner_dir": "actions-runner"'),
                    b'{"version": 1, "runners": {' + b', '.join([
                        json.dumps(self.label).encode() + b': ' +
                        json.dumps(self.document()["runners"][self.label]).encode()] * 2) + b'}}',
                    b'{"INPUT_MARKER": 1, "INPUT_MARKER": 2}'):
            self.assert_refused(bad)

    def test_invalid_encoding_json_and_size_never_echo_input(self):
        for raw in (b'\xffINPUT_MARKER', b'{"INPUT_MARKER":', b'INPUT_MARKER',
                    b'INPUT_MARKER' + b' ' * (64 * 1024), b'[' * 2000 + b']' * 2000):
            self.assert_refused(raw)
        raw = json.dumps(self.document()).encode()
        at_limit = raw + b' ' * (64 * 1024 - len(raw))
        self.assertEqual(b.parse_allowlist(at_limit, OWNER)[self.label], ("actions-runner", ".codex-review-fixture"))
        self.assert_refused(at_limit + b' ')


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="synthetic-home-", dir=tempfile.gettempdir())
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name).resolve()
        self.host_config = {
            "version": 1, "owner": OWNER,
            "default_runners": b.allowlist_document(DEFAULT_RUNNERS)["runners"],
            "legacy_labels": sorted(LEGACY_LABELS),
            "known_prior_launcher_sha256": [],
            "daily_config": DAILY_PATH, "python": PYTHON,
        }
        self.write_config()
        self.write(b.REVIEW_SOURCE, PROFILE)
        self.write(DAILY_PATH, DAILY)
        (self.home / ".codex").symlink_to((self.home / DAILY_PATH).parent, target_is_directory=True)
        self.original = {}
        for label, (runner, _) in DEFAULT_RUNNERS.items():
            doc = {"Label": label, "WorkingDirectory": str(self.home / runner),
                   "ProgramArguments": [str(self.home / runner / "runsvc.sh"), "--fixture-flag", "space arg", "$(literal)"],
                   "EnvironmentVariables": {"ACTIONS_RUNNER_SVC": "1"},
                   "KeepAlive": True, "RunAtLoad": True, "ThrottleInterval": 17,
                   "StandardOutPath": str(self.home / "unchanged-output"), "FixtureProperty": {"x": [1, 2]}}
            data = plistlib.dumps(doc)
            rel = self.plist(label)
            self.write(rel, data, 0o644)
            self.original[rel] = data
        self.write("Library/LaunchAgents/actions.runner.unrelated.plist", b"leave-alone", 0o644)

    def write_config(self, **changes):
        self.host_config.update(changes)
        return self.write(b.HOST_CONFIG, json.dumps(self.host_config).encode(), 0o644)

    def assert_config_refused(self, doc):
        raw = doc if isinstance(doc, bytes) else json.dumps(doc).encode()
        self.write(b.HOST_CONFIG, raw, 0o644)
        before = self.snapshot()
        paths = sorted(self.home.rglob("*"))
        with self.assertRaisesRegex(b.Refusal, "^Invalid host config$"):
            b.load_config(self.home)
        result = self.cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"REFUSED", result.stderr)
        self.assertNotIn(b"INPUT_MARKER", result.stdout + result.stderr)
        self.assertNotIn(b"Traceback", result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(paths, sorted(self.home.rglob("*")))

    def test_config_defaults_and_immutable_values(self):
        self.host_config = {"version": 1, "owner": OWNER}
        self.write_config()
        config = b.load_config(self.home)
        self.assertEqual(config.owner, OWNER)
        self.assertEqual(config.default_runners, {})
        self.assertEqual(config.legacy_labels, frozenset())
        self.assertEqual(config.known_prior_launcher_sha256, frozenset())
        self.assertEqual(config.daily_config, ".codex/config.toml")
        self.assertTrue(Path(config.python).is_absolute())
        with self.assertRaises(AttributeError):
            config.owner = "other-owner"
        with self.assertRaises(TypeError):
            config.default_runners[SHARED_LABEL] = ("actions-runner", b.LEGACY_REVIEW_HOME)

    def test_config_missing_or_invalid_owner(self):
        self.assert_config_refused({"version": 1})
        for owner in ("", "-INPUT_MARKER", "INPUT_MARKER", "a.b", "../INPUT_MARKER", "a b", "a\n",
                      None, True, 1, [], {}):
            with self.subTest(owner=owner):
                self.assert_config_refused({"version": 1, "owner": owner})

    def test_config_bad_version_and_exact_top_level_keys(self):
        self.assert_config_refused({"owner": OWNER})
        for version in (None, True, False, 1.0, "1", 0, 2, [], {}):
            with self.subTest(version=version):
                self.assert_config_refused({"version": version, "owner": OWNER})
        for doc in ([], None, "INPUT_MARKER", 1,
                    {"version": 1, "owner": OWNER, "INPUT_MARKER": "extra"}):
            self.assert_config_refused(doc)

    def test_config_default_runner_fields_and_types(self):
        for defaults in (None, [], "INPUT_MARKER", True,
                         {SHARED_LABEL: {}}, {SHARED_LABEL: {"runner_dir": "actions-runner"}},
                         {SHARED_LABEL: {"runner_dir": "actions-runner", "review_home": ".codex-review-x",
                                         "INPUT_MARKER": 1}},
                         {SHARED_LABEL: {"runner_dir": "../INPUT_MARKER", "review_home": ".codex-review-x"}},
                         {SHARED_LABEL: {"runner_dir": "actions-runner", "review_home": None}}):
            with self.subTest(defaults=defaults):
                self.assert_config_refused({**self.host_config, "default_runners": defaults})
        # Legacy sharing is deliberately still accepted in configured defaults.
        self.write_config()
        self.assertEqual(b.load_config(self.home).default_runners, DEFAULT_RUNNERS)

    def test_config_labels_must_match_owner(self):
        other_label = "actions.runner.other-owner-shared-ci.shared-ci-mac"
        self.assertFalse(b.valid_label(other_label, OWNER))
        self.assertTrue(b.valid_label(SHARED_LABEL, OWNER))
        self.assert_config_refused({**self.host_config, "default_runners": {
            other_label: {"runner_dir": "actions-runner", "review_home": ".codex-review-other"}}})
        for legacy in (None, {}, "INPUT_MARKER", [other_label], [1], ["../INPUT_MARKER"]):
            self.assert_config_refused({**self.host_config, "legacy_labels": legacy})

    def test_config_prior_digest_validation(self):
        for hashes in (None, {}, "0" * 64, [True], [0], [None], ["0" * 63], ["0" * 65],
                       ["g" * 64], ["INPUT_MARKER"], ["0" * 64 + "\n"]):
            self.assert_config_refused({**self.host_config, "known_prior_launcher_sha256": hashes})
        self.write_config(known_prior_launcher_sha256=["AB" * 32, "01" * 32])
        self.assertEqual(b.load_config(self.home).known_prior_launcher_sha256,
                         frozenset({"ab" * 32, "01" * 32}))

    def test_config_daily_path_validation(self):
        for daily in (None, True, [], {}, "", "/absolute/config.toml", "../config.toml",
                      "daily/../config.toml", "daily//config.toml", "daily/", "./config.toml",
                      "daily/./config.toml", "daily/\x00INPUT_MARKER"):
            with self.subTest(daily=daily):
                self.assert_config_refused({**self.host_config, "daily_config": daily})

    def test_config_python_path_validation(self):
        for python in (None, 1, True, [], {}, "", "python3", "./python3", "/bin/\x00INPUT_MARKER"):
            self.assert_config_refused({**self.host_config, "python": python})
        self.write_config()
        self.assertEqual(b.load_config(self.home).python, PYTHON)

    def test_config_duplicate_keys_encoding_and_json(self):
        raw = json.dumps(self.host_config).encode()
        for bad in (raw.replace(b'"version": 1', b'"version": 1, "version": 1'),
                    raw.replace(b'"runner_dir": "actions-runner"',
                                b'"runner_dir": "actions-runner", "runner_dir": "actions-runner"'),
                    b'{"INPUT_MARKER": 1, "INPUT_MARKER": 2}', b'\xffINPUT_MARKER',
                    b'{"INPUT_MARKER":', b'[' * 2000 + b']' * 2000):
            self.assert_config_refused(bad)

    def test_config_size_cap(self):
        raw = json.dumps(self.host_config).encode()
        at_limit = raw + b" " * (b.MAX_BYTES - len(raw))
        self.write(b.HOST_CONFIG, at_limit, 0o644)
        self.assertEqual(b.load_config(self.home).owner, OWNER)
        self.assert_config_refused(at_limit + b" ")

    def test_config_nonsecret_modes_and_file_safety(self):
        path = self.home / b.HOST_CONFIG
        path.parent.chmod(0o755)
        self.assertEqual(b.load_config(self.home).owner, OWNER)
        path.chmod(0o666)
        with self.assertRaisesRegex(b.Refusal, "^Invalid host config$"):
            b.load_config(self.home)
        path.chmod(0o644)
        other = path.with_name("other-host.json")
        path.rename(other)
        path.symlink_to(other)
        with self.assertRaisesRegex(b.Refusal, "^Invalid host config$"):
            b.load_config(self.home)
        path.unlink()
        os.link(other, path)
        with self.assertRaisesRegex(b.Refusal, "^Invalid host config$"):
            b.load_config(self.home)
        path.unlink()
        os.mkfifo(path, 0o600)
        with self.assertRaisesRegex(b.Refusal, "^Invalid host config$"):
            b.load_config(self.home)
        path.unlink()
        with self.assertRaisesRegex(b.Refusal, "^Invalid host config$"):
            b.load_config(self.home)
        other.rename(path)
        path.parent.chmod(0o777)
        with self.assertRaisesRegex(b.Refusal, "^Invalid host config$"):
            b.load_config(self.home)

    def test_config_rejects_symlink_ancestor_and_wrong_file_owner(self):
        path = self.home / b.HOST_CONFIG
        other = path.parent.with_name("physical-config")
        path.parent.rename(other)
        path.parent.symlink_to(other, target_is_directory=True)
        with self.assertRaisesRegex(b.Refusal, "^Invalid host config$"):
            b.load_config(self.home)
        path.parent.unlink()
        other.rename(path.parent)
        original = os.fstat
        def wrong_owner(fd):
            values = list(original(fd))
            values[4] = os.getuid() + 1
            return os.stat_result(values)
        with mock.patch.object(os, "fstat", side_effect=wrong_owner):
            with self.assertRaisesRegex(b.Refusal, "^Invalid host config$"):
                b.load_config(self.home)

    def test_config_owner_override_and_missing_owner_via_cli(self):
        expected = b.plan(self.home, PYTHON)["id"]
        for owner in ("other-owner", None):
            if owner is None:
                self.host_config.pop("owner")
                self.write_config()
            else:
                self.write_config(owner=owner)
            self.assertEqual(b.load_config(self.home, owner=OWNER).owner, OWNER)
            before = self.snapshot()
            result = self.cli("--owner", OWNER)
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            public, _ = json.JSONDecoder().raw_decode(result.stdout.decode())
            self.assertEqual(public["plan_id"], expected)
            self.assertEqual(before, self.snapshot())
        for owner in ("", "INPUT_MARKER", "../INPUT_MARKER"):
            result = self.cli("--owner", owner)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn(b"INPUT_MARKER", result.stdout + result.stderr)

    def test_config_override_loaded_for_install_run_and_rollback(self):
        self.store()
        manifest = self.install()
        target = self.write("actions-runner-shared-ci/runsvc.sh", b"#!/bin/sh\nexit 0\n", 0o700)
        self.host_config.pop("owner")
        path = self.write_config()
        alternate = path.with_name("alternate-host.json")
        path.rename(alternate)
        before = self.snapshot()
        commands = [[], ["run", "--label", SHARED_LABEL, "--", str(target)],
                    ["rollback", "--manifest", str(manifest)]]
        for command in commands:
            with self.subTest(command=command):
                result = self.cli(*command)
                self.assertEqual(result.returncode, 2)
                result = self.cli("--config", str(alternate), "--owner", OWNER, *command)
                self.assertEqual(result.returncode, 0, result.stderr.decode())
                self.assertEqual(before, self.snapshot())

    def test_default_daily_directory_skips_alias_check_but_rejects_symlinks(self):
        (self.home / ".codex").unlink()
        self.host_config.pop("daily_config")
        self.write_config()
        path = self.write(".codex/config.toml", DAILY)
        current = b.plan(self.home, PYTHON)
        self.assertEqual(current["public"]["daily_source"], str(path))
        self.assertEqual(self.cli().returncode, 0)
        path.unlink()
        path.parent.rmdir()
        path.parent.symlink_to((self.home / DAILY_PATH).parent, target_is_directory=True)
        with self.assertRaises(b.Refusal):
            b.plan(self.home, PYTHON)

    def test_empty_default_seed_needs_add_runner_and_then_is_valid(self):
        self.host_config.pop("default_runners")
        self.write_config()
        before = self.snapshot()
        with self.assertRaisesRegex(b.Refusal, "Invalid allowlist runners"):
            b.plan(self.home, PYTHON)
        self.assertEqual(before, self.snapshot())
        self.write_runner_plist()
        current = b.plan(self.home, PYTHON, [ADDED_SPEC])
        self.assertEqual(b.parse_allowlist(current["changes"][0]["new"], OWNER),
                         {ADDED_LABEL: (ADDED_RUNNER, ADDED_HOME)})
        self.assertEqual(self.cli("--add-runner", ADDED_SPEC).returncode, 0)

    def assert_review_reuse_refused(self, specs):
        before = self.snapshot()
        paths = sorted(self.home.rglob("*"))
        with self.assertRaisesRegex(b.Refusal, "^New runner requires an independent review home$"):
            b.plan(self.home, PYTHON, specs)
        for mode in ("--dry-run", "--apply"):
            result = self.cli(mode, *[arg for spec in specs for arg in ("--add-runner", spec)])
            self.assertEqual(result.returncode, 2)
            self.assertIn(b"REFUSED", result.stderr)
            self.assertNotIn(ADDED_LABEL.encode(), result.stdout + result.stderr)
            self.assertEqual(before, self.snapshot())
            self.assertEqual(paths, sorted(self.home.rglob("*")))

    def test_add_runner_reusing_legacy_review_home_refused_in_plan_and_cli(self):
        self.write_allowlist({SHARED_LABEL: DEFAULT_RUNNERS[SHARED_LABEL]})
        self.write_runner_plist()
        # Refuse the legacy home even when it is not currently allowlisted.
        self.assert_review_reuse_refused([f"{ADDED_LABEL}={ADDED_RUNNER}:{b.LEGACY_REVIEW_HOME}"])

    def test_add_runner_reusing_existing_dedicated_review_home_refused(self):
        self.write_allowlist()
        self.write_runner_plist()
        self.assert_review_reuse_refused([f"{ADDED_LABEL}={ADDED_RUNNER}:.codex-review-shared-ci"])

    def test_added_runners_cannot_share_a_new_review_home(self):
        self.write_runner_plist()
        other_label = "actions.runner.example-owner-other.mac"
        self.write_runner_plist(other_label, "actions-runner-other")
        specs = [ADDED_SPEC, f"{other_label}=actions-runner-other:{ADDED_HOME}"]
        self.assert_review_reuse_refused(specs)
        self.assert_review_reuse_refused(list(reversed(specs)))

    def test_identical_legacy_runner_readd_remains_noop(self):
        self.store()
        self.install()
        specs = [f"{label}={runner}:{review}" for label, (runner, review) in DEFAULT_RUNNERS.items()]
        before = self.snapshot()
        current = b.plan(self.home, PYTHON, specs)
        self.assertEqual(current["public"]["allowlist"]["added_labels"], [])
        self.assertTrue(all(c["action"] == "unchanged" for c in current["changes"]))
        self.assertIsNone(b.apply(self.home, PYTHON, current["id"], specs))
        self.assertEqual(before, self.snapshot())

    def write(self, relative, data, mode=0o600):
        path = self.home / relative
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        path.write_bytes(data)
        path.chmod(mode)
        return path

    def plist(self, label=None):
        return "Library/LaunchAgents/" + (label or next(iter(DEFAULT_RUNNERS))) + ".plist"

    def store(self, value=b"fixture-client-key"):
        b.store_secret(self.home, "OPENAI_API_KEY", value)

    def install(self):
        current = b.plan(self.home, PYTHON)
        return b.apply(self.home, PYTHON, current["id"])

    def cli(self, *args, stdin=None, env=None):
        return subprocess.run([PYTHON, str(ROOT / "host-bootstrap.py"), "--home", str(self.home),
                               *args], input=stdin, capture_output=True,
                              env=env if env is not None else {"PATH": "/usr/bin:/bin", "HOME": str(self.home)})

    def snapshot(self):
        return {str(p.relative_to(self.home)): (p.read_bytes(), stat.S_IMODE(p.stat().st_mode))
                for p in self.home.rglob("*") if p.is_file()}

    def write_allowlist(self, runners=None):
        doc = b.allowlist_document(DEFAULT_RUNNERS if runners is None else runners)
        return self.write(b.ALLOWLIST, (json.dumps(doc, indent=2, sort_keys=True) + "\n").encode())

    def write_runner_plist(self, label=ADDED_LABEL, runner=ADDED_RUNNER, wrapped=False):
        doc = plistlib.loads(self.original[self.plist()])
        doc.update(Label=label, WorkingDirectory=str(self.home / runner),
                   ProgramArguments=[str(self.home / runner / "runsvc.sh"), "literal argument"])
        if wrapped:
            doc["ProgramArguments"] = b.launcher_prefix(self.home, PYTHON, label) + doc["ProgramArguments"]
        return self.write(self.plist(label), plistlib.dumps(doc, fmt=plistlib.FMT_BINARY), 0o644)

    def assert_run_refused(self, label, args):
        argv = ["host-bootstrap.py", "--home", str(self.home), "run", "--label", label, "--", *args]
        with mock.patch.object(sys, "argv", argv), mock.patch.object(os, "execve") as execute:
            with self.assertRaises(b.Refusal):
                b.main()
            execute.assert_not_called()
        result = self.cli("run", "--label", label, "--", *args)
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"REFUSED", result.stderr)
        self.assertNotIn(label.encode(), result.stdout + result.stderr)
        self.assertNotIn(b"Traceback", result.stderr)

    def test_seed_allowlist_canonical_order_metadata_and_deterministic_plan(self):
        before = self.snapshot()
        current = b.plan(self.home, PYTHON)
        self.assertEqual(current, b.plan(self.home, PYTHON))
        public = current["public"]
        self.assertEqual(current["id"], b.digest(json.dumps(public, sort_keys=True).encode()))
        self.assertEqual(public["allowlist"], {"path": str(self.home / b.ALLOWLIST), "source": "seed-default",
                                               "runners": b.allowlist_document(DEFAULT_RUNNERS)["runners"]})
        expected = [b.ALLOWLIST, REVIEW, SHARED_REVIEW, b.LAUNCHER,
                    *[self.plist(label) for label in sorted(DEFAULT_RUNNERS)]]
        self.assertEqual([c["path"] for c in current["changes"]], expected)
        self.assertEqual([c["kind"] for c in public["changes"]],
                         ["allowlist", "review_home", "review_home", "launcher"] + ["plist"] * 4)
        self.assertEqual([c["action"] for c in public["changes"]], ["create"] * 4 + ["replace"] * 4)
        self.assertEqual(current["changes"][0]["new"],
                         (json.dumps(b.allowlist_document(DEFAULT_RUNNERS), indent=2, sort_keys=True) + "\n").encode())
        self.assertEqual(public["rollback_manifest"],
                         str(self.home / b.STATE / "txn-<random>/manifest.json") + " (created only by --apply)")
        self.assertFalse((self.home / b.STATE).exists())
        self.assertEqual(before, self.snapshot())

    def test_allowlist_file_modes_symlink_and_private_directory_refused(self):
        path = self.write_allowlist()
        path.chmod(0o644)
        with self.assertRaises(b.Refusal):
            b.plan(self.home, PYTHON)
        path.chmod(0o600)
        path.parent.chmod(0o755)
        with self.assertRaises(b.Refusal):
            b.plan(self.home, PYTHON)
        path.unlink()  # An absent allowlist still requires a private existing parent.
        with self.assertRaises(b.Refusal):
            b.plan(self.home, PYTHON)
        path.parent.chmod(0o700)
        self.write_allowlist()
        other = path.with_name("fixture-allowlist.json")
        path.rename(other)
        path.symlink_to(other)
        with self.assertRaises((b.Refusal, OSError)):
            b.plan(self.home, PYTHON)
        result = self.cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"REFUSED", result.stderr)

    def test_unknown_and_invalid_labels_refused_without_exec(self):
        self.store()
        self.install()
        runner = self.home / "actions-runner/runsvc.sh"
        for label in ("actions.runner.example-owner-Unknown.mac", "actions.runner.Other-INPUT_MARKER.mac",
                      "../INPUT_MARKER", "actions.runner.example-owner-A.mac name"):
            self.assert_run_refused(label, [str(runner)])

    def test_missing_or_invalid_allowlist_at_run_never_falls_back(self):
        self.store()
        self.install()
        label, (runner, _) = next(iter(DEFAULT_RUNNERS.items()))
        (self.home / b.ALLOWLIST).unlink()
        self.assert_run_refused(label, [str(self.home / runner / "runsvc.sh")])
        for raw in (b'{"INPUT_MARKER":', b'{"version": 1, "runners": {}}', b'\xffINPUT_MARKER'):
            self.write(b.ALLOWLIST, raw)
            self.assert_run_refused(label, [str(self.home / runner / "runsvc.sh")])

    def test_run_requires_exact_allowlisted_executable(self):
        self.store()
        self.install()
        label = next(iter(DEFAULT_RUNNERS))
        for args in ([], ["/bin/sh"], [str(self.home / "actions-runner-shared-ci/runsvc.sh")],
                     [str(self.home / "actions-runner/../actions-runner/runsvc.sh")]):
            self.assert_run_refused(label, args)

    def test_per_label_review_home_isolation_and_private_modes(self):
        self.store()
        self.install()
        selected, _ = b.connection(self.home)
        expected = b.review_bytes(b.read_file(self.home / b.REVIEW_SOURCE), selected)
        for rel in (REVIEW, SHARED_REVIEW):
            path = self.home / rel
            self.assertEqual(b.read_file(path, secret=True)["bytes"], expected)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((self.home / b.ALLOWLIST).stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE((self.home / b.ALLOWLIST).parent.stat().st_mode), 0o700)
        for label, (runner, review) in DEFAULT_RUNNERS.items():
            env = b.runner_environment(self.home, label, [str(self.home / runner / "runsvc.sh")], {})
            self.assertEqual(review, ".codex-review-shared-ci" if label == SHARED_LABEL else b.LEGACY_REVIEW_HOME)
            self.assertEqual(env["CODEX_HOME"], str(self.home / review))
            self.assertEqual(env["CODEX_REVIEW_HOME"], str(self.home / review))

    def test_existing_allowlist_is_authoritative_preserved_and_custom_runner_rolls_back(self):
        label = "actions.runner.example-owner-Custom_42.mac-2"
        runner, review = "actions-runner-custom", ".codex-review-custom"
        doc = b.allowlist_document({label: (runner, review)})
        raw = ("\n" + json.dumps(doc, separators=(",", ":")) + "  \n").encode()
        path = self.write(b.ALLOWLIST, raw)
        allowlist_before = b.read_file(path, secret=True)
        plist = plistlib.loads(self.original[self.plist()])
        plist.update(Label=label, WorkingDirectory=str(self.home / runner),
                     ProgramArguments=[str(self.home / runner / "runsvc.sh"), "literal argument"])
        original = plistlib.dumps(plist)
        self.write(self.plist(label), original, 0o644)
        self.store()
        plan = b.plan(self.home, PYTHON)
        self.assertEqual(plan["public"]["allowlist"]["source"], "existing")
        self.assertEqual(plan["changes"][0]["new"], raw)
        self.assertEqual(plan["changes"][0]["action"], "unchanged")
        self.assertEqual([c["path"] for c in plan["changes"]],
                         [b.ALLOWLIST, review + "/config.toml", b.LAUNCHER, self.plist(label)])
        manifest = self.install()
        env = b.runner_environment(self.home, label, [str(self.home / runner / "runsvc.sh")], {})
        self.assertEqual(env["CODEX_REVIEW_HOME"], str(self.home / review))
        self.assertEqual(env["CODEX_HOME"], str(self.home / review))
        self.assert_run_refused(next(iter(DEFAULT_RUNNERS)), [str(self.home / "actions-runner/runsvc.sh")])
        for rel, old in self.original.items():
            self.assertEqual((self.home / rel).read_bytes(), old)
        self.assertTrue(b.same(allowlist_before, b.read_file(path, secret=True)))
        self.assertIsNone(self.install())
        with b.lock(self.home):
            self.assertEqual(b.rollback(self.home, manifest, True), 3)
        self.assertEqual((self.home / self.plist(label)).read_bytes(), original)
        self.assertFalse((self.home / review / "config.toml").exists())
        self.assertTrue(b.same(allowlist_before, b.read_file(path, secret=True)))

    def test_legacy_install_only_adds_allowlist_shared_home_and_rewrites_shared_plist(self):
        selected, _ = b.connection(self.home)
        self.write(REVIEW, b.review_bytes(b.read_file(self.home / b.REVIEW_SOURCE), selected))
        self.write(b.LAUNCHER, (ROOT / "host-bootstrap.py").read_bytes(), 0o700)
        for label in LEGACY_LABELS:
            doc = plistlib.loads(self.original[self.plist(label)])
            doc["ProgramArguments"] = [PYTHON, str(self.home / b.LAUNCHER), "run", "--label", label, "--"] + doc["ProgramArguments"]
            self.write(self.plist(label), plistlib.dumps(doc, fmt=plistlib.FMT_BINARY), 0o644)
        before = self.snapshot()
        current = b.plan(self.home, PYTHON)
        self.assertEqual(current["id"], b.plan(self.home, PYTHON)["id"])
        actions = {c["path"]: c["action"] for c in current["changes"]}
        self.assertEqual({p for p, action in actions.items() if action == "create"}, {b.ALLOWLIST, SHARED_REVIEW})
        self.assertEqual({p for p, action in actions.items() if action == "replace"}, {self.plist(SHARED_LABEL)})
        for rel in [REVIEW, b.LAUNCHER, *[self.plist(label) for label in LEGACY_LABELS]]:
            self.assertEqual(actions[rel], "unchanged")
            self.assertEqual(next(c["new"] for c in current["changes"] if c["path"] == rel), before[rel][0])
        self.store()
        manifest = self.install()
        self.assertEqual([r["path"] for r in json.loads(manifest.read_bytes())["records"]],
                         [b.ALLOWLIST, SHARED_REVIEW, self.plist(SHARED_LABEL)])

    def test_add_existing_allowlist_plan_dry_run_and_apply_preserve_other_plists(self):
        base = {SHARED_LABEL: DEFAULT_RUNNERS[SHARED_LABEL]}
        self.write_allowlist(base)
        self.store()
        self.install()
        self.write_runner_plist(SHARED_LABEL, base[SHARED_LABEL][0], wrapped=True)
        self.write_runner_plist()
        other_label = "actions.runner.example-owner-Metrics.mac"
        other_runner, other_home = "actions-runner-metrics", ".codex-review-metrics"
        self.write_runner_plist(other_label, other_runner, wrapped=True)
        specs = [ADDED_SPEC, f"{other_label}={other_runner}:{other_home}"]
        before = self.snapshot()
        paths_before = sorted(self.home.rglob("*"))
        baseline = b.plan(self.home, PYTHON)
        original_read = b.read_file
        def guarded_read(path, **kwargs):
            self.assertNotEqual(Path(path), self.home / b.PRIVATE)
            return original_read(path, **kwargs)
        with mock.patch.object(b, "read_file", side_effect=guarded_read):
            current = b.plan(self.home, PYTHON, specs)
            self.assertEqual(current, b.plan(self.home, PYTHON, specs))
            self.assertEqual(current["id"], b.plan(self.home, PYTHON, list(reversed(specs)))["id"])
        self.assertNotEqual(current["id"], baseline["id"])
        merged = {**base, ADDED_LABEL: (ADDED_RUNNER, ADDED_HOME),
                  other_label: (other_runner, other_home)}
        expected_bytes = (json.dumps(b.allowlist_document(merged), indent=2, sort_keys=True) + "\n").encode()
        self.assertEqual(current["changes"][0]["new"], expected_bytes)
        self.assertEqual(current["public"]["allowlist"], {
            "path": str(self.home / b.ALLOWLIST), "source": "existing+added",
            "runners": b.allowlist_document(merged)["runners"],
            "added_labels": sorted([ADDED_LABEL, other_label])})
        cli_args = ["--add-runner", specs[0], "--add-runner", specs[1]]
        result = self.cli("install", "--dry-run", *cli_args)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        public, end = json.JSONDecoder().raw_decode(result.stdout.decode())
        self.assertEqual(public["plan_id"], current["id"])
        summary = result.stdout.decode()[end:]
        self.assertIn("ALLOWLIST SOURCE: existing+added", summary)
        for label in (ADDED_LABEL, other_label):
            self.assertIn(label, summary.split("ADDED RUNNERS:")[1].split("FILES TO WRITE:")[0])
        self.assertEqual(before, self.snapshot())
        self.assertEqual(paths_before, sorted(self.home.rglob("*")))
        result = self.cli("install", "--apply", "--approve-plan", current["id"], *cli_args)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(b.read_file(self.home / b.ALLOWLIST, secret=True)["bytes"], expected_bytes)
        for review in (ADDED_HOME, other_home):
            profile = self.home / review / "config.toml"
            self.assertEqual(b.read_file(profile, secret=True)["bytes"], before[SHARED_REVIEW][0])
            self.assertEqual(stat.S_IMODE(profile.parent.stat().st_mode), 0o700)
            self.assertEqual([p.name for p in profile.parent.iterdir()], ["config.toml"])
        for rel, value in before.items():
            if rel not in {b.ALLOWLIST, self.plist(ADDED_LABEL)}:
                self.assertEqual(self.snapshot()[rel], value)
        old = plistlib.loads(before[self.plist(ADDED_LABEL)][0])
        installed = plistlib.loads((self.home / self.plist(ADDED_LABEL)).read_bytes())
        self.assertEqual(installed["ProgramArguments"],
                         b.launcher_prefix(self.home, PYTHON, ADDED_LABEL) + old["ProgramArguments"])
        installed["ProgramArguments"] = old["ProgramArguments"]
        self.assertEqual(installed, old)
        self.assertEqual(stat.S_IMODE((self.home / self.plist(ADDED_LABEL)).stat().st_mode), 0o644)
        manifest = next(p for p in (self.home / b.STATE).glob("txn-*/manifest.json")
                        if json.loads(p.read_bytes())["plan"] == current["id"])
        self.assertEqual({r["path"] for r in json.loads(manifest.read_bytes())["records"]},
                         {b.ALLOWLIST, ADDED_HOME + "/config.toml", other_home + "/config.toml",
                          self.plist(ADDED_LABEL)})

    def test_add_runner_to_default_seed_and_duplicate_spec_is_deterministic(self):
        self.write_runner_plist()
        before = self.snapshot()
        current = b.plan(self.home, PYTHON, [ADDED_SPEC])
        self.assertEqual(current, b.plan(self.home, PYTHON, [ADDED_SPEC, ADDED_SPEC]))
        self.assertEqual(current["public"]["allowlist"]["source"], "seed-default+added")
        self.assertEqual(current["public"]["allowlist"]["added_labels"], [ADDED_LABEL])
        self.assertEqual(b.parse_allowlist(current["changes"][0]["new"], OWNER),
                         {**DEFAULT_RUNNERS, ADDED_LABEL: (ADDED_RUNNER, ADDED_HOME)})
        self.assertEqual(before, self.snapshot())

    def test_identical_readd_is_noop_even_with_noncanonical_allowlist_bytes(self):
        self.store()
        self.install()
        self.write_runner_plist()
        current = b.plan(self.home, PYTHON, [ADDED_SPEC])
        b.apply(self.home, PYTHON, current["id"], [ADDED_SPEC])
        doc = json.loads((self.home / b.ALLOWLIST).read_bytes())
        raw = ("\n" + json.dumps(doc, separators=(",", ":")) + "  \n").encode()
        path = self.write(b.ALLOWLIST, raw)
        original = b.read_file(path, secret=True)
        before = self.snapshot()
        current = b.plan(self.home, PYTHON, [ADDED_SPEC, ADDED_SPEC])
        self.assertEqual(current["public"]["allowlist"]["source"], "existing")
        self.assertEqual(current["public"]["allowlist"]["added_labels"], [])
        self.assertTrue(all(c["action"] == "unchanged" for c in current["changes"]))
        self.assertIsNone(b.apply(self.home, PYTHON, current["id"], [ADDED_SPEC, ADDED_SPEC]))
        self.assertEqual(before, self.snapshot())
        self.assertTrue(b.same(original, b.read_file(path, secret=True)))

    def test_conflicting_readd_refused_without_overwrite_or_input_echo(self):
        self.write_allowlist({ADDED_LABEL: (ADDED_RUNNER, ADDED_HOME)})
        before = self.snapshot()
        for spec in (f"{ADDED_LABEL}=actions-runner-other:{ADDED_HOME}",
                     f"{ADDED_LABEL}={ADDED_RUNNER}:.codex-review-other",
                     f"{ADDED_LABEL}=INPUT_MARKER:INPUT_MARKER"):
            with self.subTest(spec=spec):
                with self.assertRaises(b.Refusal) as error:
                    b.plan(self.home, PYTHON, [spec])
                self.assertNotIn(ADDED_LABEL, str(error.exception))
                self.assertNotIn("INPUT_MARKER", str(error.exception))
                result = self.cli("install", "--add-runner", spec)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn(ADDED_LABEL.encode(), result.stdout + result.stderr)
                self.assertNotIn(b"INPUT_MARKER", result.stdout + result.stderr)
                self.assertEqual(before, self.snapshot())

    def test_conflicting_duplicate_add_specs_refused(self):
        before = self.snapshot()
        with self.assertRaises(b.Refusal):
            b.plan(self.home, PYTHON, [ADDED_SPEC, f"{ADDED_LABEL}={ADDED_RUNNER}:.codex-review-other"])
        self.assertEqual(before, self.snapshot())

    def test_malformed_add_runner_specs_refused_without_echo(self):
        before = self.snapshot()
        for spec in ("", "INPUT_MARKER", f"{ADDED_LABEL}:{ADDED_RUNNER}:{ADDED_HOME}",
                     f"{ADDED_LABEL}={ADDED_RUNNER}", f"={ADDED_RUNNER}:{ADDED_HOME}",
                     f"{ADDED_LABEL}=:{ADDED_HOME}", f"{ADDED_LABEL}={ADDED_RUNNER}:",
                     ADDED_SPEC + ":INPUT_MARKER", ADDED_SPEC + "=INPUT_MARKER"):
            with self.subTest(spec=spec):
                with self.assertRaises(b.Refusal) as error:
                    b.plan(self.home, PYTHON, [spec])
                self.assertNotIn("INPUT_MARKER", str(error.exception))
                result = self.cli("install", "--add-runner", spec)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn(b"INPUT_MARKER", result.stdout + result.stderr)
                self.assertNotIn(ADDED_LABEL.encode(), result.stdout + result.stderr)
                self.assertEqual(before, self.snapshot())

    def test_invalid_add_runner_label_directory_and_review_home_refused(self):
        before = self.snapshot()
        for label, runner, review in (
                ("../INPUT_MARKER", ADDED_RUNNER, ADDED_HOME),
                ("actions.runner.Other-INPUT_MARKER.mac", ADDED_RUNNER, ADDED_HOME),
                (ADDED_LABEL + "\n", ADDED_RUNNER, ADDED_HOME),
                (ADDED_LABEL, "../INPUT_MARKER", ADDED_HOME),
                (ADDED_LABEL, "actions-runner-UPPER", ADDED_HOME),
                (ADDED_LABEL, ADDED_RUNNER + "/child", ADDED_HOME),
                (ADDED_LABEL, ADDED_RUNNER, "../INPUT_MARKER"),
                (ADDED_LABEL, ADDED_RUNNER, ".codex-review"),
                (ADDED_LABEL, ADDED_RUNNER, ".codex-review-UPPER"),
                (ADDED_LABEL, ADDED_RUNNER, ADDED_HOME + "\n")):
            spec = f"{label}={runner}:{review}"
            with self.subTest(spec=spec):
                with self.assertRaises(b.Refusal) as error:
                    b.plan(self.home, PYTHON, [spec])
                self.assertNotIn("INPUT_MARKER", str(error.exception))
                result = self.cli("install", "--add-runner", spec)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn(b"INPUT_MARKER", result.stdout + result.stderr)
                self.assertEqual(before, self.snapshot())

    def test_add_runner_duplicate_directory_in_base_or_batch_refused(self):
        self.write_allowlist()
        before = self.snapshot()
        for specs in ([f"{ADDED_LABEL}=actions-runner:{ADDED_HOME}"],
                      [ADDED_SPEC, f"actions.runner.example-owner-Other.mac={ADDED_RUNNER}:.codex-review-other"]):
            with self.subTest(specs=specs), self.assertRaisesRegex(b.Refusal, "Duplicate runner directory"):
                b.plan(self.home, PYTHON, specs)
            self.assertEqual(before, self.snapshot())

    def test_add_runner_revalidates_base_and_merged_allowlist_size(self):
        for raw in (b'{"version":1,"runners":{}}', b'{"INPUT_MARKER":',
                    b'INPUT_MARKER' + b' ' * (64 * 1024)):
            self.write(b.ALLOWLIST, raw)
            before = self.snapshot()
            with self.assertRaises(b.Refusal):
                b.plan(self.home, PYTHON, [ADDED_SPEC])
            self.assertEqual(before, self.snapshot())
        self.write_allowlist()
        before = self.snapshot()
        oversized = f"{ADDED_LABEL}=actions-runner-{'a' * (64 * 1024)}:{ADDED_HOME}"
        with self.assertRaisesRegex(b.Refusal, "Allowlist is oversized"):
            b.plan(self.home, PYTHON, [oversized])
        self.assertEqual(before, self.snapshot())

    def test_add_runner_is_rejected_for_run_rollback_and_secret_write_before_io(self):
        before = self.snapshot()
        for command in ("run", "rollback", "secret-write"):
            argv = ["host-bootstrap.py", "--home", str(self.home), command, "--add-runner", ADDED_SPEC]
            with mock.patch.object(sys, "argv", argv), \
                 mock.patch.object(b, "read_file", side_effect=AssertionError("unexpected read")), \
                 mock.patch.object(os, "execve", side_effect=AssertionError("unexpected exec")):
                with self.assertRaisesRegex(b.Refusal, "Add-runner requires install"):
                    b.main()
            result = self.cli(command, "--add-runner", ADDED_SPEC)
            self.assertEqual(result.returncode, 2)
            self.assertIn(b"REFUSED", result.stderr)
            self.assertEqual(before, self.snapshot())

    def test_add_runner_approval_requires_same_additions_before_secret_read_or_writes(self):
        self.write_allowlist()
        self.write_runner_plist()
        baseline = b.plan(self.home, PYTHON)
        current = b.plan(self.home, PYTHON, [ADDED_SPEC])
        before = self.snapshot()
        altered = f"{ADDED_LABEL}={ADDED_RUNNER}:.codex-review-other"
        for approved, specs in ((current["id"], []), (baseline["id"], [ADDED_SPEC]),
                                (current["id"], [altered])):
            with mock.patch.object(b, "parse_env", side_effect=AssertionError("secret parsed")):
                with self.assertRaisesRegex(b.Refusal, "Plan approval missing or stale"):
                    b.apply(self.home, PYTHON, approved, specs)
            result = self.cli("install", "--apply", "--approve-plan", approved,
                              *[arg for spec in specs for arg in ("--add-runner", spec)])
            self.assertEqual(result.returncode, 2)
            self.assertEqual(before, self.snapshot())
        self.assertFalse((self.home / b.STATE).exists())

    def test_add_runner_missing_plist_refuses_entire_plan_before_writes(self):
        self.write_allowlist()
        before = self.snapshot()
        with self.assertRaises(FileNotFoundError):
            b.plan(self.home, PYTHON, [ADDED_SPEC])
        for mode in ("--dry-run", "--apply"):
            result = self.cli("install", mode, "--add-runner", ADDED_SPEC)
            self.assertEqual(result.returncode, 2)
            self.assertIn(b"REFUSED", result.stderr)
            self.assertEqual(before, self.snapshot())
        self.assertFalse((self.home / b.STATE).exists())
        self.assertFalse((self.home / ADDED_HOME).exists())

    def test_add_runner_rollback_restores_prior_bytes_and_removes_created_profile(self):
        self.store()
        self.install()
        doc = b.allowlist_document(DEFAULT_RUNNERS)
        prior = ("\n" + json.dumps(doc, separators=(",", ":")) + "  \n").encode()
        self.write(b.ALLOWLIST, prior)
        self.write_runner_plist()
        before = self.snapshot()
        current = b.plan(self.home, PYTHON, [ADDED_SPEC])
        manifest = b.apply(self.home, PYTHON, current["id"], [ADDED_SPEC])
        records = json.loads(manifest.read_bytes())["records"]
        self.assertEqual([r["path"] for r in records],
                         [b.ALLOWLIST, ADDED_HOME + "/config.toml", self.plist(ADDED_LABEL)])
        self.assertEqual((manifest.parent / records[0]["backup"]).read_bytes(), prior)
        self.assertIsNone(records[1]["backup"])
        installed = self.snapshot()
        self.assertEqual(b.rollback(self.home, manifest), 3)
        self.assertEqual(installed, self.snapshot())
        with b.lock(self.home):
            self.assertEqual(b.rollback(self.home, manifest, True), 3)
        self.assertEqual(json.loads(manifest.read_bytes())["status"], "rolled_back")
        self.assertFalse((self.home / ADDED_HOME / "config.toml").exists())
        self.assertEqual(list((self.home / ADDED_HOME).iterdir()), [])
        for rel, value in before.items():
            self.assertEqual(self.snapshot()[rel], value)

    def test_no_key_material_in_add_lifecycle_output_or_state(self):
        marker = b"SYNTHETIC_ADD_CLIENT_KEY_NEVER_LOG_THIS"
        self.store(marker)
        self.install()
        self.write_runner_plist()
        outputs = [self.cli("install", "--add-runner", ADDED_SPEC)]
        self.assertEqual(outputs[0].returncode, 0, outputs[0].stderr.decode())
        public, _ = json.JSONDecoder().raw_decode(outputs[0].stdout.decode())
        outputs.append(self.cli("install", "--apply", "--approve-plan", public["plan_id"],
                                "--add-runner", ADDED_SPEC))
        self.assertEqual(outputs[-1].returncode, 0, outputs[-1].stderr.decode())
        manifest = next(p for p in (self.home / b.STATE).glob("txn-*/manifest.json")
                        if json.loads(p.read_bytes())["plan"] == public["plan_id"])
        script = f"#!{PYTHON}\nimport os\nprint(' '.join(sorted(os.environ)))\n".encode()
        target = self.write(ADDED_RUNNER + "/runsvc.sh", script, 0o700)
        outputs.append(self.cli("run", "--label", ADDED_LABEL, "--", str(target)))
        self.assertIn(b"OPENAI_API_KEY", outputs[-1].stdout)
        outputs.append(self.cli("install", "--add-runner", ADDED_SPEC))
        repeated, _ = json.JSONDecoder().raw_decode(outputs[-1].stdout.decode())
        outputs.append(self.cli("install", "--apply", "--approve-plan", repeated["plan_id"],
                                "--add-runner", ADDED_SPEC))
        self.assertIn(b"Already installed", outputs[-1].stdout)
        outputs.append(self.cli("rollback", "--manifest", str(manifest)))
        outputs.append(self.cli("rollback", "--apply", "--manifest", str(manifest)))
        for result in outputs:
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            self.assertNotIn(marker, result.stdout + result.stderr)
        for rel, (data, _) in self.snapshot().items():
            if rel != b.PRIVATE:
                self.assertNotIn(marker, data)
        self.assert_run_refused(ADDED_LABEL, [str(target)])

    def test_configured_prior_launcher_digest_accepted_during_add_and_restored(self):
        prior = b"# Synthetic launcher standing in for the previous source digest\n"
        self.write_config(known_prior_launcher_sha256=[b.digest(prior)])
        self.store()
        self.install()
        self.write_runner_plist()
        launcher = self.write(b.LAUNCHER, prior, 0o700)
        current = b.plan(self.home, PYTHON, [ADDED_SPEC])
        self.assertEqual(next(c["action"] for c in current["changes"] if c["kind"] == "launcher"), "replace")
        manifest = b.apply(self.home, PYTHON, current["id"], [ADDED_SPEC])
        self.assertEqual(launcher.read_bytes(), (ROOT / "host-bootstrap.py").read_bytes())
        with b.lock(self.home):
            b.rollback(self.home, manifest, True)
        self.assertEqual(launcher.read_bytes(), prior)
        self.assertEqual(stat.S_IMODE(launcher.stat().st_mode), 0o700)

    def test_known_prior_launcher_upgrades_and_rollback_restores_bytes_and_mode(self):
        prior = b"# Synthetic previous reviewed release\n"
        launcher = self.write(b.LAUNCHER, prior, 0o700)
        self.store()
        self.write_config(known_prior_launcher_sha256=[b.digest(prior)])
        current = b.plan(self.home, PYTHON)
        self.assertEqual(next(c["action"] for c in current["changes"] if c["kind"] == "launcher"), "replace")
        manifest = self.install()
        self.assertEqual(launcher.read_bytes(), (ROOT / "host-bootstrap.py").read_bytes())
        record = next(r for r in json.loads(manifest.read_bytes())["records"] if r["path"] == b.LAUNCHER)
        self.assertEqual((manifest.parent / record["backup"]).read_bytes(), prior)
        with b.lock(self.home):
            b.rollback(self.home, manifest, True)
        self.assertEqual(launcher.read_bytes(), prior)
        self.assertEqual(stat.S_IMODE(launcher.stat().st_mode), 0o700)

    def test_known_prior_launcher_requires_mode_0700(self):
        prior = b"# Synthetic reviewed launcher\n"
        self.write_config(known_prior_launcher_sha256=[b.digest(prior)])
        for mode in (0o600, 0o644, 0o755):
            self.write(b.LAUNCHER, prior, mode)
            with self.assertRaises(b.Refusal):
                b.plan(self.home, PYTHON)

    def test_apply_rechecks_unchanged_allowlist_after_journal(self):
        self.write_allowlist()
        self.store()
        approved = b.plan(self.home, PYTHON)["id"]
        original = b.write_manifest
        def concurrent_change(path, doc):
            original(path, doc)
            runners = dict(DEFAULT_RUNNERS)
            runners[SHARED_LABEL] = ("actions-runner-shared-ci", ".codex-review-concurrent")
            self.write_allowlist(runners)
        with mock.patch.object(b, "write_manifest", side_effect=concurrent_change), self.assertRaises(b.Refusal):
            b.apply(self.home, PYTHON, approved)
        for rel in (REVIEW, SHARED_REVIEW, b.LAUNCHER):
            self.assertFalse((self.home / rel).exists())
        for rel, data in self.original.items():
            self.assertEqual((self.home / rel).read_bytes(), data)

    def test_apply_private_check_covers_new_shared_review_home(self):
        self.store()
        ensure = b.ensure_dir
        parent = (self.home / SHARED_REVIEW).parent
        def changed_mode(path):
            ensure(path)
            if Path(path) == parent:
                parent.chmod(0o755)
        with mock.patch.object(b, "ensure_dir", side_effect=changed_mode), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(b.Refusal):
                self.install()
        self.assertFalse((self.home / SHARED_REVIEW).exists())
        self.assertFalse((self.home / b.LAUNCHER).exists())
        parent.chmod(0o700)
        manifest = next((self.home / b.STATE).glob("txn-*/manifest.json"))
        with b.lock(self.home):
            self.assertEqual(b.rollback(self.home, manifest, True), 2)

    def test_allowlist_drift_or_invalid_file_blocks_entire_rollback(self):
        self.store()
        manifest = self.install()
        path = self.home / b.ALLOWLIST
        raw = path.read_bytes()
        for data in (raw + b"\n", b'{"INPUT_MARKER":', b'\xff'):
            path.write_bytes(data)
            before = self.snapshot()
            with self.assertRaises(b.Refusal):
                b.rollback(self.home, manifest, True)
            self.assertEqual(before, self.snapshot())

    def test_rollback_created_plist_is_not_an_allowed_absent_backup(self):
        self.store()
        manifest = self.install()
        doc = json.loads(manifest.read_bytes())
        record = next(r for r in doc["records"] if r["path"] == self.plist())
        record.update(backup=None, before_sha256=None, before_mode=None)
        manifest.write_text(json.dumps(doc))
        before = self.snapshot()
        with self.assertRaises(b.Refusal):
            b.rollback(self.home, manifest, True)
        self.assertEqual(before, self.snapshot())

    def test_all_cli_argument_errors_omit_input(self):
        for args in (("INPUT_MARKER",), ("--INPUT_MARKER",), ("--key", "INPUT_MARKER"),
                     ("run", "--label")):
            result = self.cli(*args)
            self.assertEqual(result.returncode, 2)
            self.assertIn(b"REFUSED", result.stderr)
            self.assertNotIn(b"INPUT_MARKER", result.stdout + result.stderr)

    def test_cli_summary_and_no_key_in_output_or_state_through_full_lifecycle(self):
        marker = b"SYNTHETIC_CLIENT_KEY_NEVER_LOG_THIS"
        self.store(marker)
        result = self.cli("install", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        output = result.stdout.decode()
        public, end = json.JSONDecoder().raw_decode(output)
        summary = output[end:]
        for heading in ("FILES TO WRITE:", "PLISTS REWRITTEN:", "UNCHANGED:", "ROLLBACK MANIFEST:"):
            self.assertIn(heading, summary)
        for label in DEFAULT_RUNNERS:
            self.assertIn(label, summary.split("PLISTS REWRITTEN:")[1].split("UNCHANGED:")[0])
        self.assertTrue(output.rstrip().endswith("No files written; private key NOT read; no service or model requests."))
        self.assertIn(public["rollback_manifest"], summary)
        outputs = [result]
        outputs.append(self.cli("install", "--apply", "--approve-plan", public["plan_id"]))
        manifest = next((self.home / b.STATE).glob("txn-*/manifest.json"))
        label, (runner, _) = next(iter(DEFAULT_RUNNERS.items()))
        script = f"#!{PYTHON}\nimport os\nprint(' '.join(sorted(os.environ)))\n".encode()
        target = self.write(runner + "/runsvc.sh", script, 0o700)
        outputs.append(self.cli("run", "--label", label, "--", str(target)))
        self.assertIn(b"OPENAI_API_KEY", outputs[-1].stdout)
        outputs.append(self.cli("rollback", "--manifest", str(manifest)))
        outputs.append(self.cli("rollback", "--apply", "--manifest", str(manifest)))
        for result in outputs:
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            self.assertNotIn(marker, result.stdout + result.stderr)
        for path in (self.home / b.STATE).rglob("*"):
            if path.is_file():
                self.assertNotIn(marker, path.read_bytes())

    def test_legacy_version_1_manifest_without_allowlist_still_rolls_back(self):
        selected, _ = b.connection(self.home)
        targets = [(REVIEW, b.review_bytes(b.read_file(self.home / b.REVIEW_SOURCE), selected), 0o600, None),
                   (b.LAUNCHER, b"# Synthetic installed legacy launcher\n", 0o700, None)]
        for label in sorted(LEGACY_LABELS):
            rel = self.plist(label)
            original = self.original[rel]
            doc = plistlib.loads(original)
            doc["ProgramArguments"] = [PYTHON, str(self.home / b.LAUNCHER), "run", "--label", label, "--"] + doc["ProgramArguments"]
            targets.append((rel, plistlib.dumps(doc), 0o644, original))
        b.ensure_dir(self.home / b.STATE)
        transaction = b.STATE + "/txn-" + "1" * 32
        records = []
        for i, (rel, data, mode, before) in enumerate(targets):
            self.write(rel, data, mode)
            backup = f"before-{i}.bin" if before else None
            if backup:
                self.write(transaction + "/" + backup, before)
            records.append({"path": rel, "backup": backup, "before_sha256": b.digest(before) if before else None,
                            "before_mode": 0o644 if before else None, "after_sha256": b.digest(data), "after_mode": mode})
        manifest = self.write(transaction + "/manifest.json", json.dumps({"version": 1, "home": str(self.home),
                              "plan": "0" * 64, "status": "installed", "records": records}).encode())
        # Historical rollback paths must survive even future changes to the seed.
        self.write_config(default_runners={})
        self.assertEqual(b.rollback(self.home, manifest), 5)
        with b.lock(self.home):
            self.assertEqual(b.rollback(self.home, manifest, True), 5)
        for rel, data in self.original.items():
            self.assertEqual((self.home / rel).read_bytes(), data)
        self.assertFalse((self.home / REVIEW).exists())
        self.assertFalse((self.home / b.LAUNCHER).exists())
        self.assertFalse((self.home / b.ALLOWLIST).exists())
        self.assertEqual(b.rollback(self.home, manifest), 0)

    def test_dry_run_is_no_write_no_secret_no_service(self):
        self.write(b.PRIVATE, b"malformed secret MUST NOT READ", 0o600)
        before = self.snapshot()
        with mock.patch.object(b, "parse_env", side_effect=AssertionError("secret parsed")), \
             mock.patch.object(os, "execve", side_effect=AssertionError("exec")):
            result = b.plan(self.home, PYTHON)
        self.assertEqual(before, self.snapshot())
        out = self.cli()
        self.assertEqual(out.returncode, 0)
        self.assertIn(b"DRY-RUN", out.stdout)
        self.assertNotIn(b"MUST NOT READ", out.stdout + out.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(result["public"]["connection"]["env_key"], "OPENAI_API_KEY")

    def test_apply_preserves_profile_and_every_unrelated_plist_field(self):
        self.store()
        manifest = self.install()
        doc = tomllib.loads((self.home / REVIEW).read_text())
        doc.pop("model_provider")
        provider = doc.pop("model_providers")
        self.assertEqual(doc, tomllib.loads(PROFILE.decode()))
        self.assertEqual(set(provider["raven"]), b.CONNECTION_KEYS)
        self.assertIs(provider["raven"]["requires_openai_auth"], False)
        self.assertIn(b"requires_openai_auth = false\n", (self.home / REVIEW).read_bytes())
        self.assertIn(PROFILE, (self.home / REVIEW).read_bytes())
        for rel, raw in self.original.items():
            old, new = plistlib.loads(raw), plistlib.loads((self.home / rel).read_bytes())
            self.assertEqual(new["ProgramArguments"][6:], old["ProgramArguments"])
            new["ProgramArguments"] = old["ProgramArguments"]
            self.assertEqual(old, new)
            self.assertEqual(stat.S_IMODE((self.home / rel).stat().st_mode), 0o644)
        self.assertEqual((self.home / "Library/LaunchAgents/actions.runner.unrelated.plist").read_bytes(), b"leave-alone")
        self.assertEqual(json.loads(manifest.read_text())["status"], "installed")
        backup_bytes = b"".join(p.read_bytes() for p in manifest.parent.iterdir())
        self.assertNotIn(b"fixture-client-key", backup_bytes)

    def test_rerun_noop_and_rollback_exact_then_rerun(self):
        self.store()
        original = self.snapshot()
        manifest = self.install()
        installed = self.snapshot()
        self.assertIsNone(self.install())
        self.assertEqual(installed, self.snapshot())
        self.assertEqual(b.rollback(self.home, manifest), 8)
        self.assertEqual(installed, self.snapshot())
        with b.lock(self.home):
            self.assertEqual(b.rollback(self.home, manifest, True), 8)
        for rel, value in original.items():
            self.assertEqual(self.snapshot()[rel], value)
        self.assertFalse((self.home / b.LAUNCHER).exists())
        self.assertEqual(b.rollback(self.home, manifest), 0)
        self.assertIsNotNone(self.install())

    def test_unknown_concurrent_change_blocks_entire_rollback(self):
        self.store()
        manifest = self.install()
        with (self.home / self.plist()).open("ab") as stream:
            stream.write(b"\n<!-- Owner changed me -->\n")
        before = self.snapshot()
        with self.assertRaises(b.Refusal):
            b.rollback(self.home, manifest, True)
        self.assertEqual(before, self.snapshot())

    def test_stale_plan_and_compare_replace_fail_closed(self):
        self.store()
        plan = b.plan(self.home, PYTHON)
        path = self.home / b.REVIEW_SOURCE
        old = b.read_file(path)
        path.write_bytes(PROFILE + b"\n# Owner change\n")
        before = self.snapshot()
        with self.assertRaises(b.Refusal):
            b.apply(self.home, PYTHON, plan["id"])
        with self.assertRaises(b.Refusal):
            b.replace_checked(path, old, PROFILE, 0o600)
        self.assertEqual(before, self.snapshot())

    def test_secret_literal_no_shell_interpolation_no_overwrite(self):
        value = b'$(touch${IFS}SENTINEL)`whoami`;$GH_TOKEN=value'
        self.store(value)
        path = self.home / b.PRIVATE
        self.assertEqual(b.parse_env(b.read_file(path, secret=True)["bytes"]), {"OPENAI_API_KEY": value.decode()})
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
        with self.assertRaises(FileExistsError):
            self.store(b"replacement")
        self.assertEqual(path.read_bytes(), b"OPENAI_API_KEY=" + value + b"\n")
        self.assertFalse((self.home / "SENTINEL").exists())

    def test_malformed_empty_multiline_arbitrary_env_rejected(self):
        for raw in [b"", b"OPENAI_API_KEY=", b"OPENAI_API_KEY=\n", b"GH_TOKEN=fixture", b"CUSTOM=fixture",
                    b"export OPENAI_API_KEY=fixture", b"OPENAI_API_KEY=a\nRAVEN_API_KEY=b\n",
                    b"OPENAI_API_KEY=a\nb\n", b"OPENAI_API_KEY=a\r\n", b"OPENAI_API_KEY=a b",
                    b"OPENAI_API_KEY=a\x00b", b"OPENAI_API_KEY=\xff"]:
            with self.subTest(raw=raw), self.assertRaises(b.Refusal):
                b.parse_env(raw)
        for raw in [b"", b"line1\nline2", b"line1\rline2", b"x" * 4097]:
            with self.assertRaises(b.Refusal):
                self.store(raw)
        self.assertFalse((self.home / b.PRIVATE).exists())

    def test_secret_symlink_hardlink_fifo_permissions_and_owner(self):
        path = self.write(b.PRIVATE, b"OPENAI_API_KEY=fixture\n")
        path.chmod(0o644)
        with self.assertRaises(b.Refusal):
            b.read_file(path, secret=True)
        path.chmod(0o600)
        alias = path.with_name("alias")
        os.link(path, alias)
        with self.assertRaises(b.Refusal):
            b.read_file(path, secret=True)
        alias.unlink()
        real = os.fstat
        def wrong_owner(fd):
            s = real(fd)
            return type("WrongOwner", (), {"st_mode": s.st_mode, "st_uid": os.getuid() + 1})()
        with mock.patch.object(os, "fstat", side_effect=wrong_owner), self.assertRaises(b.Refusal):
            b.read_file(path, secret=True)
        path.rename(alias)
        path.symlink_to(alias)
        with self.assertRaises((b.Refusal, OSError)):
            b.read_file(path, secret=True)
        with self.assertRaises((b.Refusal, OSError)):
            self.store()
        path.unlink()
        os.mkfifo(path, 0o600)
        with self.assertRaises(b.Refusal):
            b.read_file(path, secret=True)

    def test_directory_symlink_and_insecure_parent_rejected(self):
        path = self.write(b.PRIVATE, b"OPENAI_API_KEY=fixture\n")
        path.parent.chmod(0o755)
        with self.assertRaises(b.Refusal):
            b.read_file(path, secret=True)
        path.parent.chmod(0o700)
        target = path.parent.with_name("alternate")
        path.parent.rename(target)
        path.parent.symlink_to(target, target_is_directory=True)
        with self.assertRaises(b.Refusal):
            b.read_file(path, secret=True)
        with self.assertRaises(b.Refusal):
            self.store()

    def test_no_git_secret_and_no_missing_env_fallback(self):
        (self.home / ".git").mkdir()
        (self.home / ".git/HEAD").touch()
        with self.assertRaises(b.Refusal):
            self.store()
        (self.home / ".git/HEAD").unlink()
        (self.home / ".git").rmdir()
        with mock.patch.object(b.os, "environ", {"GH_TOKEN": "fixture", "GITHUB_TOKEN": "fixture", "OPENAI_API_KEY": "fixture"}):
            with self.assertRaises(FileNotFoundError):
                self.install()

    def test_runner_uses_private_only_preserves_nonclient_environment(self):
        self.store()
        self.install()
        label, (runner, _) = next(iter(DEFAULT_RUNNERS.items()))
        args = [str(self.home / runner / "runsvc.sh"), "--unchanged"]
        inherited = {"OPENAI_API_KEY": "stale", "RAVEN_API_KEY": "stale2", "GH_TOKEN": "not-a-client-key", "OTHER": "keep",
                     "CODEX_HOME": str(self.home / ".codex"), "CODEX_REVIEW_HOME": str(self.home / "other-home")}
        original = dict(inherited)
        env = b.runner_environment(self.home, label, args, inherited)
        self.assertEqual(env, {"OPENAI_API_KEY": "fixture-client-key", "GH_TOKEN": "not-a-client-key", "OTHER": "keep",
                               "CODEX_HOME": str(self.home / ".codex-review-raven-actions"),
                               "CODEX_REVIEW_HOME": str(self.home / ".codex-review-raven-actions")})
        self.assertEqual(inherited, original)
        (self.home / b.PRIVATE).unlink()
        with self.assertRaises(FileNotFoundError):
            b.runner_environment(self.home, label, args, inherited)
        with self.assertRaises(b.Refusal):
            b.runner_environment(self.home, "unrelated", args, inherited)

    def test_provider_rejections_and_no_isolation_replacement(self):
        for old, new in [(b"localhost:7024", b"example.com:7024"), (b'responses', b'chat'),
                         (b'OPENAI_API_KEY', b'GH_TOKEN'), (b'OPENAI_API_KEY', b'GITHUB_TOKEN'),
                         (b'OPENAI_API_KEY', b'ARBITRARY_KEY')]:
            self.write(DAILY_PATH, DAILY.replace(old, new))
            with self.assertRaises(b.Refusal):
                b.plan(self.home, PYTHON)
        self.write(DAILY_PATH, DAILY + b'requires_openai_auth = true\n')
        with self.assertRaises(b.Refusal):
            b.plan(self.home, PYTHON)
        self.write(DAILY_PATH, DAILY)
        for old, new in [(b'never', b'on-request'), (b'read-only', b'workspace-write'), (b'hooks = false', b'hooks = true')]:
            self.write(b.REVIEW_SOURCE, PROFILE.replace(old, new))
            with self.assertRaises(b.Refusal):
                b.plan(self.home, PYTHON)

    def test_unexpected_plist_env_program_and_target_refused(self):
        original = plistlib.loads(self.original[self.plist()])
        for field, value in [("EnvironmentVariables", {"GH_TOKEN": "fixture-private"}),
                             ("Program", "/bin/sh"), ("Label", "unrelated"),
                             ("WorkingDirectory", "/tmp"), ("ProgramArguments", ["/bin/sh"])]:
            doc = dict(original)
            doc[field] = value
            self.write(self.plist(), plistlib.dumps(doc))
            with self.assertRaises(b.Refusal):
                b.plan(self.home, PYTHON)

    def test_cli_diagnostics_do_not_leak_parser_excerpt_or_secret(self):
        marker = b"FAKE_PRIVATE_MARKER"
        self.write(DAILY_PATH, b'bad = "' + marker + b'\n')
        result = self.cli()
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(marker, result.stderr + result.stdout)
        self.write(DAILY_PATH, DAILY)
        result = self.cli("secret-write", "--apply", "--approve-plan", b.plan(self.home, PYTHON)["id"],
                          stdin=marker + b"\nsecond-line")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(marker, result.stderr + result.stdout)

    def test_interrupted_apply_journal_allows_guarded_partial_rollback(self):
        self.store()
        original = b.replace_checked
        count = 0
        def interrupt(path, expected, data, mode):
            nonlocal count
            if path.name != "manifest.json":
                count += 1
                if count == 3:
                    raise OSError("synthetic interruption")
            return original(path, expected, data, mode)
        with mock.patch.object(b, "replace_checked", side_effect=interrupt), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(OSError):
                self.install()
        manifest = next((self.home / b.STATE).glob("txn-*/manifest.json"))
        self.assertEqual(b.rollback(self.home, manifest), 2)
        with b.lock(self.home):
            b.rollback(self.home, manifest, True)
        self.assertEqual((self.home / b.REVIEW_SOURCE).read_bytes(), PROFILE)
        self.assertFalse((self.home / REVIEW).exists())
        for rel, data in self.original.items():
            self.assertEqual((self.home / rel).read_bytes(), data)

    def test_tampered_manifest_path_backup_and_unknown_launcher_refused(self):
        self.store()
        self.write(b.LAUNCHER, b"unknown launcher", 0o700)
        with self.assertRaises(b.Refusal):
            self.install()
        (self.home / b.LAUNCHER).unlink()
        manifest = self.install()
        doc = json.loads(manifest.read_text())
        doc["records"][0]["path"] = "../../outside"
        manifest.write_text(json.dumps(doc))
        with self.assertRaises(b.Refusal):
            b.rollback(self.home, manifest, True)

    def test_real_exec_handoff_synthetic_runner_without_shell(self):
        self.store()
        self.install()
        label, (runner, _) = next(iter(DEFAULT_RUNNERS.items()))
        script = (f"#!{PYTHON}\n" + "import os, sys, json\n" +
                  "print(json.dumps({'argv': sys.argv[1:], 'private_loaded': os.environ.get('OPENAI_API_KEY') == 'fixture-client-key', "
                  "'old_alias_removed': 'RAVEN_API_KEY' not in os.environ, 'github_not_used': os.environ.get('GH_TOKEN') == 'fixture-github'}))\n")
        target = self.write(runner + "/runsvc.sh", script.encode(), 0o700)
        literal = "$(touch SHOULD_NOT_EXIST);`whoami`"
        result = subprocess.run([PYTHON, str(self.home / b.LAUNCHER), "--home", str(self.home), "run", "--label", label,
                                 "--", str(target), literal, "space argument"],
                                env={"HOME": str(self.home), "PATH": "/usr/bin:/bin", "OPENAI_API_KEY": "old",
                                     "RAVEN_API_KEY": "old-alias", "GH_TOKEN": "fixture-github"},
                                capture_output=True, cwd=self.home)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        output = json.loads(result.stdout)
        self.assertEqual(output, {"argv": [literal, "space argument"], "private_loaded": True,
                                  "old_alias_removed": True, "github_not_used": True})
        self.assertFalse((self.home / "SHOULD_NOT_EXIST").exists())

    def test_exec_handoff_pins_legacy_and_new_review_homes_despite_inherited_redirects(self):
        self.store()
        self.install()
        inherited = {"HOME": str(self.home), "PATH": "/usr/bin:/bin",
                     "CODEX_HOME": str(self.home / ".codex"),
                     "CODEX_REVIEW_HOME": str(self.home / "unrelated-review-home"),
                     "OTHER": "preserved", "OPENAI_API_KEY": "stale", "RAVEN_API_KEY": "stale-alias"}
        original = dict(inherited)
        # A real exec into a synthetic shell covers both trusted-base selector forms.
        script = b'''#!/bin/bash
set -eu
legacy_home="${CODEX_HOME:-$HOME/.codex-review}"
explicit_review_home="${CODEX_REVIEW_HOME:-$HOME/.codex-review}"
printf '%s\\n' "$legacy_home" "$explicit_review_home" "$OTHER"
test "$OPENAI_API_KEY" = fixture-client-key
test "${RAVEN_API_KEY+x}" != x
'''
        for label, (runner, review_home) in DEFAULT_RUNNERS.items():
            with self.subTest(label=label):
                expected = str(self.home / review_home)
                target = self.write(runner + "/runsvc.sh", script, 0o700)
                result = subprocess.run([PYTHON, str(self.home / b.LAUNCHER), "--home", str(self.home), "run", "--label", label,
                                         "--", str(target)], env=inherited, cwd=self.home, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr.decode())
                self.assertEqual(result.stdout.decode().splitlines(), [expected, expected, "preserved"])
                self.assertEqual(inherited, original)

    def test_backup_tamper_and_lock_collision_refuse(self):
        self.store()
        manifest = self.install()
        record = next(r for r in json.loads(manifest.read_text())["records"] if r["backup"] is not None)
        backup = manifest.parent / record["backup"]
        backup.write_bytes(b"changed by another actor")
        before = self.snapshot()
        with self.assertRaises(b.Refusal):
            b.rollback(self.home, manifest, True)
        self.assertEqual(before, self.snapshot())
        with b.lock(self.home):
            with self.assertRaises(FileExistsError):
                with b.lock(self.home):
                    self.fail("Second writer entered")

    def test_symlink_target_and_existing_private_leaf_refuse(self):
        target = self.home / b.REVIEW_SOURCE
        other = self.write("separate-profile", PROFILE)
        target.unlink()
        target.symlink_to(other)
        with self.assertRaises(OSError):
            b.plan(self.home, PYTHON)
        target.unlink()
        self.write(b.REVIEW_SOURCE, PROFILE)
        self.store()
        result = self.cli("secret-write", "--apply", "--approve-plan", b.plan(self.home, PYTHON)["id"],
                          stdin=b"second-fixture-key")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(b"second-fixture-key", result.stdout + result.stderr)
        self.assertEqual((self.home / b.PRIVATE).read_bytes(), b"OPENAI_API_KEY=fixture-client-key\n")

    def test_raven_alias_supported_but_provider_name_must_match(self):
        self.write(DAILY_PATH, DAILY.replace(b"OPENAI_API_KEY", b"RAVEN_API_KEY"))
        self.store()
        with self.assertRaises(b.Refusal):
            self.install()
        (self.home / b.PRIVATE).unlink()
        b.store_secret(self.home, "RAVEN_API_KEY", b"fixture-raven-alias")
        self.install()
        label, (runner, _) = next(iter(DEFAULT_RUNNERS.items()))
        env = b.runner_environment(self.home, label, [str(self.home / runner / "runsvc.sh")], {})
        self.assertEqual(env, {"RAVEN_API_KEY": "fixture-raven-alias",
                               "CODEX_HOME": str(self.home / ".codex-review-raven-actions"),
                               "CODEX_REVIEW_HOME": str(self.home / ".codex-review-raven-actions")})

    def test_launcher_revalidates_local_endpoint_and_isolation(self):
        self.store()
        self.install()
        profile = (self.home / REVIEW).read_bytes()
        label, (runner, _) = next(iter(DEFAULT_RUNNERS.items()))
        for old, new in [(b"localhost:7024", b"external.example:7024"), (b"read-only", b"workspace-write"),
                         (b"requires_openai_auth = false", b"requires_openai_auth = true"),
                         (b"requires_openai_auth = false\n", b"")]:
            self.write(REVIEW, profile.replace(old, new))
            with self.assertRaises(b.Refusal):
                b.runner_environment(self.home, label, [str(self.home / runner / "runsvc.sh")], {})

    def test_daily_alias_only_allows_known_canonical_readonly_source(self):
        alias = self.home / ".codex"
        alias.unlink()
        alias.symlink_to(self.home / "other-config", target_is_directory=True)
        with self.assertRaises(b.Refusal):
            b.plan(self.home, PYTHON)
        alias.unlink()
        alias.symlink_to((self.home / DAILY_PATH).parent, target_is_directory=True)
        canonical = self.home / DAILY_PATH
        other = self.write("other-config.toml", DAILY)
        canonical.unlink()
        canonical.symlink_to(other)
        with self.assertRaises(OSError):
            b.plan(self.home, PYTHON)

    def test_rerun_preserves_later_unrelated_plist_edits(self):
        self.store()
        self.install()
        path = self.home / self.plist()
        doc = plistlib.loads(path.read_bytes())
        doc["OwnerNewProperty"] = "preserve"
        path.write_bytes(plistlib.dumps(doc))
        before = self.snapshot()
        self.assertIsNone(self.install())
        self.assertEqual(before, self.snapshot())

    def test_explicit_false_required_in_installed_provider_and_preserved(self):
        for suffix in (b"", b"requires_openai_auth = false\n"):
            self.write(DAILY_PATH, DAILY + suffix)
            selected, _ = b.connection(self.home)
            self.assertIs(selected["requires_openai_auth"], False)
            profile = b.review_bytes(b.read_file(self.home / b.REVIEW_SOURCE), selected)
            parsed = tomllib.loads(profile.decode())
            self.assertIs(parsed["model_providers"]["raven"]["requires_openai_auth"], False)
            self.assertEqual(b.review_bytes({"bytes": profile}, selected), profile)
            parsed.pop("model_provider")
            parsed.pop("model_providers")
            self.assertEqual(parsed, tomllib.loads(PROFILE.decode()))
        selected.pop("requires_openai_auth")
        with self.assertRaises(b.Refusal):
            b.validate_connection(selected)
        for invalid in (True, "false", 0, None):
            with self.assertRaises(b.Refusal):
                b.validate_connection({**selected, "requires_openai_auth": invalid})

    def test_approved_plan_cli_mismatch_precedes_any_secret_or_target_write(self):
        approved = b.plan(self.home, PYTHON)["id"]
        before = self.snapshot()
        result = self.cli("install", "--dry-run", "--approve-plan", approved)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        for command in (("install", "--dry-run"), ("install", "--apply"), ("secret-write", "--apply")):
            result = self.cli(*command, "--approve-plan", "0" * 64, stdin=b"synthetic-not-persisted")
            self.assertEqual(result.returncode, 2)
            self.assertNotIn(b"synthetic-not-persisted", result.stdout + result.stderr)
            self.assertEqual(before, self.snapshot())
        result = self.cli("secret-write", "--apply", "--approve-plan", approved, stdin=b"synthetic-approved")
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual((self.home / b.PRIVATE).read_bytes(), b"OPENAI_API_KEY=synthetic-approved\n")
        self.assertEqual(b.plan(self.home, PYTHON)["id"], approved)

    def test_shared_source_and_auth_neighbors_untouched_install_rerun_rollback(self):
        self.store()
        neighbors = {
            ".codex-review/auth.json": b"SYNTHETIC_AUTH_NEIGHBOR_DO_NOT_COPY",
            ".codex-review/cache/catalog.json": b"SYNTHETIC_CACHE_DO_NOT_COPY",
            ".codex-review/sessions/fixture.jsonl": b"SYNTHETIC_SESSION_DO_NOT_COPY",
            "daily-config/auth.json": b"SYNTHETIC_DAILY_AUTH_DO_NOT_COPY",
        }
        for rel, data in neighbors.items():
            self.write(rel, data)
        protected = {rel: b.read_file(self.home / rel) for rel in [b.REVIEW_SOURCE, DAILY_PATH, *neighbors]}
        original_read = b.read_file
        def guarded_read(path, **kwargs):
            self.assertNotIn(Path(path), {self.home / rel for rel in neighbors})
            return original_read(path, **kwargs)
        with mock.patch.object(b, "read_file", side_effect=guarded_read):
            plan = b.plan(self.home, PYTHON)
            self.assertNotIn(b.REVIEW_SOURCE, [c["path"] for c in plan["changes"]])
            self.assertEqual(plan["public"]["review_source_sha256"], b.digest(PROFILE))
            manifest = self.install()
            target = self.home / REVIEW
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(target.parent.stat().st_mode), 0o700)
            self.assertEqual([p.name for p in target.parent.iterdir()], ["config.toml"])
            records = json.loads(manifest.read_text())["records"]
            self.assertNotIn(b.REVIEW_SOURCE, [r["path"] for r in records])
            self.assertIsNone(next(r for r in records if r["path"] == REVIEW)["backup"])
            self.assertIsNone(self.install())
            for rel, snapshot in protected.items():
                self.assertTrue(b.same(original_read(self.home / rel), snapshot))
            with b.lock(self.home):
                b.rollback(self.home, manifest, True)
        self.assertFalse(target.exists())
        self.assertTrue(target.parent.is_dir())
        self.assertEqual(list(target.parent.iterdir()), [])
        for rel, snapshot in protected.items():
            self.assertTrue(b.same(b.read_file(self.home / rel), snapshot))
        backups = b"".join(p.read_bytes() for p in manifest.parent.iterdir())
        for sentinel in neighbors.values():
            self.assertNotIn(sentinel, backups)

    def test_unknown_target_and_nonprivate_target_modes_refused_compatible_target_retained(self):
        self.store()
        target = self.write(REVIEW, b"unknown = true\n")
        before = self.snapshot()
        with self.assertRaises(b.Refusal):
            self.install()
        self.assertEqual(before, self.snapshot())
        selected, _ = b.connection(self.home)
        compatible = b.review_bytes(b.read_file(self.home / b.REVIEW_SOURCE), selected)
        target.write_bytes(compatible)
        target.chmod(0o644)
        with self.assertRaises(b.Refusal):
            self.install()
        target.chmod(0o600)
        target.parent.chmod(0o755)
        with self.assertRaises(b.Refusal):
            self.install()
        target.parent.chmod(0o700)
        original = b.read_file(target)
        manifest = self.install()
        self.assertNotIn(REVIEW, [r["path"] for r in json.loads(manifest.read_text())["records"]])
        self.assertIsNone(self.install())
        with b.lock(self.home):
            b.rollback(self.home, manifest, True)
        self.assertTrue(b.same(b.read_file(target), original))

    def test_created_target_drift_blocks_rollback_and_shared_source_is_not_allowed(self):
        self.store()
        manifest = self.install()
        target = self.home / REVIEW
        original = target.read_bytes()
        for drift in ("bytes", "mode"):
            target.write_bytes(original + (b"\n# owner edit\n" if drift == "bytes" else b""))
            target.chmod(0o640 if drift == "mode" else 0o600)
            before = self.snapshot()
            with self.assertRaises(b.Refusal):
                b.rollback(self.home, manifest, True)
            self.assertEqual(before, self.snapshot())
        target.write_bytes(original)
        target.chmod(0o600)
        doc = json.loads(manifest.read_text())
        record = next(r for r in doc["records"] if r["path"] == REVIEW)
        record["path"] = b.REVIEW_SOURCE
        manifest.write_text(json.dumps(doc))
        before = self.snapshot()
        with self.assertRaises(b.Refusal):
            b.rollback(self.home, manifest, True)
        self.assertEqual(before, self.snapshot())

    def test_source_identity_change_invalidates_plan_even_when_bytes_match(self):
        approved = b.plan(self.home, PYTHON)["id"]
        source = self.home / b.REVIEW_SOURCE
        source.rename(source.with_name("original-fixture-config.toml"))
        self.write(b.REVIEW_SOURCE, PROFILE)
        self.assertNotEqual(b.plan(self.home, PYTHON)["id"], approved)
        before = self.snapshot()
        with self.assertRaises(b.Refusal):
            b.apply(self.home, PYTHON, approved)
        self.assertEqual(before, self.snapshot())

    def test_concurrent_source_change_after_journal_prevents_target_writes(self):
        self.store()
        approved = b.plan(self.home, PYTHON)["id"]
        original = b.write_manifest
        def concurrent_change(path, doc):
            original(path, doc)
            self.write(b.REVIEW_SOURCE, PROFILE + b"\n# synthetic concurrent source edit\n")
        with mock.patch.object(b, "write_manifest", side_effect=concurrent_change), self.assertRaises(b.Refusal):
            b.apply(self.home, PYTHON, approved)
        self.assertFalse((self.home / REVIEW).exists())
        self.assertFalse((self.home / b.LAUNCHER).exists())
        for rel, data in self.original.items():
            self.assertEqual((self.home / rel).read_bytes(), data)



if __name__ == "__main__":
    unittest.main(verbosity=2)
