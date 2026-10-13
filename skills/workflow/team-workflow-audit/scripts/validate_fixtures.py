#!/usr/bin/env python3
"""Deterministically exercise the audit rubric against synthetic cases."""

import json
from collections import defaultdict
from pathlib import Path


def evaluate(case):
    findings = []
    events = case.get("events", [])
    if case.get("nonterminal") and not case.get("next_actor"):
        findings.append("silent_stall")
    if "executor_terminal_block" in events and not case.get("tl_recovery"):
        findings.append("invalid_executor_block")
    shas = [case.get(key) for key in ("implementation_sha", "review_sha", "merge_sha")]
    if all(shas) and len(set(shas)) != 1:
        findings.append("stale_sha")
    if "merged" in events and ("review_approved" not in events or events.index("merged") < events.index("review_approved")):
        findings.append("merge_before_review")
    if case.get("overlapping_runs") and not case.get("supersession_explicit"):
        findings.append("overlapping_runs")
    if case.get("workflow_fit") is False:
        findings.append("unfit_workflow")
    if case.get("protective_deviation"):
        findings.append("protective_deviation")
    return findings


def summarize_agent_repeats(case):
    attempts = case.get("agent_attempts", [])
    groups = defaultdict(list)
    for attempt in attempts:
        groups[(attempt["role"], attempt["cycle_kind"])].append(attempt)

    metrics = {}
    for (role, _cycle_kind), role_attempts in groups.items():
        current = metrics.setdefault(
            role,
            {
                "attempts_total": 0,
                "repeat_cycles": 0,
                "repeat_cases": 0,
                "same_artifact_repeat_cycles": 0,
                "changed_artifact_repeat_cycles": 0,
                "max_cycles_per_case": 0,
                "by_cycle_kind": {},
                "by_trigger_cause": {},
            },
        )
        current["attempts_total"] += len(role_attempts)
        current["max_cycles_per_case"] = max(
            current["max_cycles_per_case"], len(role_attempts)
        )
        repeats = role_attempts[1:]
        current["repeat_cycles"] += len(repeats)
        current["by_cycle_kind"][_cycle_kind] = {
            "attempts": len(role_attempts),
            "repeat_cycles": len(repeats),
        }
        for attempt in role_attempts:
            cause = attempt["trigger_cause"]
            current["by_trigger_cause"][cause] = (
                current["by_trigger_cause"].get(cause, 0) + 1
            )
        for previous, repeated in zip(role_attempts, repeats):
            key = (
                "same_artifact_repeat_cycles"
                if previous["artifact_id"] == repeated["artifact_id"]
                else "changed_artifact_repeat_cycles"
            )
            current[key] += 1

    for role_metrics in metrics.values():
        role_metrics["repeat_cases"] = int(role_metrics["repeat_cycles"] > 0)
    return metrics


def summarize_for_owner(case):
    verdicts = case["axis_verdicts"]

    def counts(axis, positive, negative):
        values = verdicts[axis]
        return {
            "positive": values.count(positive),
            "negative": values.count(negative),
            "unknown": values.count("insufficient_evidence"),
        }

    outcome = counts("outcome_integrity", "intact", "compromised")
    conformance = counts("workflow_conformance", "conformant", "nonconformant")
    fitness = counts("workflow_fitness", "fit", "unfit")
    effectiveness_values = verdicts["task_effectiveness"]
    return {
        "total_cases": len(verdicts["outcome_integrity"]),
        "delivery_trust": {
            "confirmed_trustworthy": outcome["positive"],
            "confirmed_compromised": outcome["negative"],
            "unknown": outcome["unknown"],
        },
        "rule_following": {
            "confirmed_following": conformance["positive"],
            "confirmed_violations": conformance["negative"],
            "unknown": conformance["unknown"],
        },
        "workflow_usability": {
            "confirmed_fit": fitness["positive"],
            "confirmed_unfit": fitness["negative"],
            "unknown": fitness["unknown"],
        },
        "task_effectiveness": {
            "confirmed_effective": effectiveness_values.count("effective"),
            "confirmed_ineffective": effectiveness_values.count("ineffective"),
            "confirmed_regressed": effectiveness_values.count("regressed"),
            "pending": sum(
                effectiveness_values.count(value)
                for value in (
                    "pending_delivery",
                    "pending_release",
                    "pending_observation",
                )
            ),
            "unknown": effectiveness_values.count("insufficient_evidence"),
        },
    }


def evaluate_task_effectiveness(case):
    evidence = case["task_effectiveness_evidence"]
    if evidence.get("delivery_status") != "done":
        return "pending_delivery"
    if not evidence.get("merge_sha"):
        return "insufficient_evidence"
    first_build = evidence.get("first_build")
    if not first_build:
        return (
            "pending_release"
            if evidence.get("release_pending")
            else "insufficient_evidence"
        )

    fingerprint = evidence.get("problem_fingerprint")
    effective_seen = False
    relevant_seen = False
    observations = sorted(
        evidence.get("observations", []),
        key=lambda observation: observation.get("observed_at", ""),
    )
    for observation in observations:
        if observation.get("kind") == "confirmed_effective":
            if observation.get("build") and int(observation["build"]) >= int(first_build):
                effective_seen = True
                relevant_seen = True
            continue
        if observation.get("kind") != "problem_reappeared":
            continue
        if observation.get("problem_fingerprint") != fingerprint:
            continue
        affected_build = observation.get("affected_build")
        if not affected_build:
            return "insufficient_evidence"
        if int(affected_build) < int(first_build):
            continue
        return "regressed" if effective_seen else "ineffective"

    if effective_seen:
        return "effective"
    if observations and not relevant_seen:
        return "insufficient_evidence"
    return "pending_observation"


def main():
    fixture_path = Path(__file__).parent.parent / "references" / "fixtures.json"
    cases = json.loads(fixture_path.read_text(encoding="utf-8"))
    failures = []
    for case in cases:
        actual = evaluate(case)
        if actual != case["expected"]:
            failures.append(f"{case['id']}: expected={case['expected']} actual={actual}")
        if "expected_agent_repeat" in case:
            actual_metrics = summarize_agent_repeats(case)
            if actual_metrics != case["expected_agent_repeat"]:
                failures.append(
                    f"{case['id']}: expected_agent_repeat={case['expected_agent_repeat']} "
                    f"actual_agent_repeat={actual_metrics}"
                )
        if "expected_owner_summary" in case:
            actual_summary = summarize_for_owner(case)
            if actual_summary != case["expected_owner_summary"]:
                failures.append(
                    f"{case['id']}: expected_owner_summary={case['expected_owner_summary']} "
                    f"actual_owner_summary={actual_summary}"
                )
        if "expected_task_effectiveness" in case:
            actual_effectiveness = evaluate_task_effectiveness(case)
            if actual_effectiveness != case["expected_task_effectiveness"]:
                failures.append(
                    f"{case['id']}: expected_task_effectiveness="
                    f"{case['expected_task_effectiveness']} "
                    f"actual_task_effectiveness={actual_effectiveness}"
                )
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"PASS: {len(cases)} audit fixtures")


if __name__ == "__main__":
    main()
