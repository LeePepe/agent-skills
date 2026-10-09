#!/usr/bin/env python3
"""Offline request/review adapters. No runner, network, subprocess or delivery."""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse


REPOSITORIES = frozenset({
    "agent-skills", "shared-ci", "shared-design-tokens", "shared-design-system",
    "shared-telemetry", "VoxKit", "VoxPocket", "VitalStride", "AIDash",
})
OUTCOMES = {"implementation_gap", "stale_document", "obsolete_code", "consistent", "clarify", "deferred"}
STATES = {"active", "superseded", "draft", "future", "hold", "unknown"}
RULES = Path(__file__).resolve().parent.parent / "references" / "review-rules.md"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def relative_path(value):
    require(text(value), "path must be nonempty")
    path = PurePosixPath(value)
    require(not path.is_absolute() and all(p not in {"", ".", ".."} for p in value.split("/"))
            and "\\" not in value and not any(ord(c) < 32 for c in value), "invalid relative path")
    return value


def repo_url(value):
    require(text(value), "repository URL required")
    parsed = urlparse(value)
    require(parsed.scheme == "https" and parsed.netloc == "github.com"
            and not parsed.query and not parsed.fragment, "canonical GitHub HTTPS URL required")
    parts = parsed.path.strip("/").removesuffix(".git").split("/")
    require(len(parts) == 2 and all(re.fullmatch(r"[A-Za-z0-9_.-]+", p) and p not in {".", ".."}
                                   for p in parts), "invalid repository URL")
    return "https://github.com/" + "/".join(parts).lower()


def validate_snapshot(snapshot, scope):
    """Scope is an independently supplied exact-remote map, never model output."""
    name = snapshot["repository"]
    require(name in REPOSITORIES and name in scope, "repository outside approved scope")
    remote = repo_url(snapshot["url"])
    require(remote == repo_url(scope[name]) and remote.rsplit("/", 1)[1] == name.lower(),
            "repository identity does not match approved scope")
    require(snapshot["visibility"] == "public", "public visibility must be verified")
    require(re.fullmatch(r"[a-f0-9]{40}", snapshot["revision"]) is not None, "full revision required")
    expected = snapshot["expected_paths"]
    require(isinstance(expected, list) and expected, "expected inspection paths required")
    require(len(set(expected)) == len(expected), "duplicate expected paths")
    for path in expected:
        relative_path(path)
    files = {}
    for source in snapshot["files"]:
        path = relative_path(source["path"])
        require(path not in files and path in expected, "duplicate or unexpected source path")
        require(source["role"] in {"current", "code", "history"}, "invalid source role")
        require(isinstance(source["content"], str), "source content must be text")
        require(re.fullmatch(r"[a-f0-9]{40}", source["commit"]) is not None, "full source commit required")
        require(datetime.fromisoformat(source["committed_at"]).tzinfo is not None,
                "source commit time must include timezone")
        require(isinstance(source.get("diff", ""), str), "diff must be text")
        files[path] = source
    require(isinstance(snapshot["gaps"], list) and all(text(g) for g in snapshot["gaps"]),
            "gaps must contain explanations")
    return files


def prepare_request(snapshot, scope):
    validate_snapshot(snapshot, scope)
    return {
        "mode": "offline", "sandbox": "read-only", "delivery": "not_submitted",
        "instructions": RULES.read_text(encoding="utf-8"),
        "untrusted_snapshot": snapshot,
    }


def evidence(reference, files, covered, roles):
    require(isinstance(reference, dict) and set(reference) == {"path", "quote"},
            "evidence needs only path and quote")
    path, quote = reference["path"], reference["quote"]
    require(path in files and path in covered, "evidence must refer to a checked snapshot file")
    require(files[path]["role"] in roles, "evidence has the wrong source role")
    require(text(quote) and quote in files[path]["content"], "evidence quote absent from snapshot")
    source = files[path]
    return {**reference, "commit": source["commit"], "committed_at": source["committed_at"],
            "diff": source.get("diff", "")}


def adapt_review(snapshot, response, scope, projects):
    """Validate a simulated semantic review and render unsubmitted backlog drafts."""
    files = validate_snapshot(snapshot, scope)
    require(set(response) == {"revision", "covered_paths", "assessments", "gaps"}, "unexpected review fields")
    require(response["revision"] == snapshot["revision"], "review is for a different revision")
    covered = response["covered_paths"]
    require(isinstance(covered, list) and len(set(covered)) == len(covered)
            and set(covered) <= files.keys(), "invalid review coverage")
    require(isinstance(response["gaps"], list) and all(text(g) for g in response["gaps"]),
            "review gaps must contain explanations")
    gaps = list(snapshot["gaps"]) + list(response["gaps"])
    gaps.extend("Not checked: " + path for path in snapshot["expected_paths"] if path not in covered)
    if not any(source["role"] == "current" for source in files.values()):
        gaps.append("No current documents available")
    conclusions, drafts, assessed = [], [], set()
    require(isinstance(response["assessments"], list), "assessments must be a list")
    for item in response["assessments"]:
        require(set(item) == {"statement", "decision", "implementation", "state", "outcome",
                              "reason", "desired", "acceptance"}, "unexpected assessment fields")
        require(item["state"] in STATES and item["outcome"] in OUTCOMES, "invalid semantic conclusion")
        require(all(text(item[key]) for key in ("reason", "desired", "acceptance")), "explanation required")
        statement = evidence(item["statement"], files, covered, {"current"})
        assessed.add(statement["path"])
        decision = evidence(item["decision"], files, covered, {"current", "history"}) if item["decision"] else None
        require(isinstance(item["implementation"], list), "implementation evidence must be a list")
        implementation = [evidence(ref, files, covered, {"code"}) for ref in item["implementation"]]
        state, outcome = item["state"], item["outcome"]
        reason, desired, acceptance = item["reason"], item["desired"], item["acceptance"]
        if state in {"draft", "future", "hold"}:
            require(outcome == "deferred", "draft/future/HOLD cannot become a development request")
            if not decision:
                gaps.append("Deferred requirement lacks decision evidence: " + statement["path"])
        elif outcome == "deferred":
            raise ValueError("only draft/future/HOLD may be deferred")
        elif state == "unknown" or not decision or not implementation:
            outcome = "clarify"
            reason = "Missing effective-decision or implementation evidence. " + reason
        if (outcome == "implementation_gap" and state != "active") or (
                outcome in {"stale_document", "obsolete_code"} and state != "superseded"):
            outcome = "clarify"
            reason = "Conclusion conflicts with the stated requirement status. " + reason
        if outcome == "clarify":
            desired = "Clarify the effective requirement and actual implementation before proposing changes."
            acceptance = "Record the missing decision/code evidence and resolve the uncertainty."
            gaps.append("Unresolved evidence: " + statement["path"])
        conclusion = {"outcome": outcome, "state": state, "reason": reason, "statement": statement,
                      "decision": decision, "implementation": implementation,
                      "desired": desired, "acceptance": acceptance}
        conclusions.append(conclusion)
        if outcome not in {"consistent", "deferred"}:
            drafts.append({"title": f"[{outcome}] {snapshot['repository']}: {statement['path']}",
                           "description": render_body(snapshot, conclusion), "status": "backlog"})
    gaps.extend("No statement assessed: " + path for path in covered
                if files[path]["role"] == "current" and path not in assessed)
    # Resource records are offline fixtures from one explicitly verified workspace.
    # Never infer a project from its title, or accept model-supplied dispatch fields.
    backlog = []
    if drafts:
        matches = []
        for project in projects:
            require(set(project) == {"workspace", "project", "repo_url"}
                    and text(project["workspace"]) and text(project["project"]), "invalid project binding")
            if repo_url(project["repo_url"]) == repo_url(snapshot["url"]):
                matches.append(project)
        if len(matches) != 1:
            gaps.append("Repository must have exactly one verified project resource binding")
        else:
            backlog = [{**draft, "workspace": matches[0]["workspace"], "project": matches[0]["project"]}
                       for draft in drafts]
    return {"mode": "offline", "revision": snapshot["revision"], "inspection": "incomplete" if gaps else "complete",
            "covered_paths": covered, "gaps": gaps, "conclusions": conclusions,
            "drafts": drafts, "backlog": backlog, "delivery": "not_submitted"}


def render_body(snapshot, conclusion):
    body = ["## Current behavior", conclusion["statement"]["quote"], "", "## Desired behavior",
            conclusion["desired"], "", "## Evidence", f"Repository: {snapshot['url']} @ {snapshot['revision']}",
            conclusion["reason"]]
    refs = [conclusion["statement"], conclusion["decision"], *conclusion["implementation"]]
    for ref in filter(None, refs):
        body.extend([f"- {ref['path']} @ {ref['commit']} ({ref['committed_at']}):", ref["quote"]])
        if ref["diff"]:
            body.extend(["Related diff (evidence only):", ref["diff"]])
    body.extend(["", "## Acceptance criteria", conclusion["acceptance"], "", "## Out of scope",
                 "This maintenance run does not implement, assign, dispatch, clean up code or follow repairs.",
                 "Offline draft only; receipt and remediation are unverified."])
    return "\n".join(body) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("request", "replay"))
    parser.add_argument("fixture", type=Path, help="offline JSON bundle; output is JSON on stdout")
    args = parser.parse_args()
    try:
        bundle = json.loads(args.fixture.read_text(encoding="utf-8"))
        if args.mode == "request":
            result = prepare_request(bundle["snapshot"], bundle["scope"])
        else:
            result = adapt_review(bundle["snapshot"], bundle["review"], bundle["scope"], bundle["projects"])
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("inspection", "complete") == "complete" else 2
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Invalid offline input: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
