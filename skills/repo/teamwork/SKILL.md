---
name: teamwork
description: Synchronous Dev Team workflow 02 execution — spec-first, plan-led implementation from single-source roles to a non-Draft PR handoff.
allowed-tools: Bash, Agent
---

# Teamwork

Synchronously executes Dev Team workflow 02 in the current CLI session using single-source role definitions. The skill entry coordinates subagents via same-session spawn and wait, replacing Multica dispatch, comments, and wakeups without copying role definitions or editing code directly.

## Triggers

```text
/teamwork:task <description>
```

Natural-language trigger: `Use teamwork to implement <feature>`.
Activate only on explicit teamwork intent; casual prompts run directly without subagents.

## Single Source & Authority

Roles resolve directly from the loaded bundle at `../../workflow/dev-team-roles/` (supporting full bundles and symlinks). If source roles or subagent capabilities are missing, fail closed with a setup blocker before executing any role. Never search target repositories or fall back to copied role files.

- [Team Lead](../../workflow/dev-team-roles/dev-team-team-lead/SKILL.md) — orchestration, scheduling, and escalation
- [Planner](../../workflow/dev-team-roles/dev-team-planner/SKILL.md) — spec and task breakdown
- [Fullstack Engineer](../../workflow/dev-team-roles/dev-team-fullstack-engineer/SKILL.md) — implementation, validation, self-review, and PR creation
- [AI Reviewer](../../workflow/dev-team-roles/dev-team-ai-reviewer/SKILL.md) — spec gate and exact-SHA pre-push review
- Shared rules: [squad](../../workflow/dev-team-roles/dev-team-squad/SKILL.md)
- External policy reference: [Clear small issue](../../workflow/dev-team-roles/dev-team-pr-manager/SKILL.md#clear-small-issue-owner-2026-10-13) (read-only policy link for workflow 03; PR Manager is not a local subagent)

## Same-Session Spawn & Wait Adapter

The CLI session replaces Multica issue comments, mentions, and wakeups with synchronous subagent invocations (`Agent` tool) and direct in-memory handoffs:

1. **Preflight**: Verify bundle source roles exist and subagent capability is active; otherwise fail closed.
2. **Team Lead**: Spawn Team Lead first for request confirmation and triage; await orchestration handoff.
3. **Planner**: Spawn Planner with task intent; await reviewable spec and plan.
4. **Spec Gate**: Spawn AI Reviewer with spec/plan; await verdict. Review rounds, same-root accumulation, targeted final review, and escalation follow linked [squad](../../workflow/dev-team-roles/dev-team-squad/SKILL.md) rules.
5. **Implementation**: Spawn Fullstack Engineer (sole writer) with approved plan. Fullstack implements, verifies (UI validation only for user-visible changes), self-reviews, commits locally, and freezes candidate SHA. Retain writer identity if startup/receipt is unknown.
6. **Pre-Push Review**: Spawn AI Reviewer with frozen candidate SHA and base→candidate diff; await exact-SHA verdict (security/performance specialists are invoked by AI Reviewer on demand, never as fixed executing roles).
7. **Publish & Handoff**: Resume/reinvoke the already-created original Fullstack Engineer by identity (never spawn a replacement writer) and await that same subagent through pushing the reviewed SHA unchanged, opening a non-Draft PR, reporting the PR link/head, and handing off to external workflow 03 PR Manager (PRM is never spawned as a local subagent).

## Backend & Rules

- **CLI Backend Priority**: Codex CLI → Claude native → Copilot.
- **Fail-Closed**: Missing bundle sources or subagent capabilities stop immediately with a setup blocker.
- **No Local PRM**: PR Manager is an external workflow 03 role; do not spawn PRM locally.
