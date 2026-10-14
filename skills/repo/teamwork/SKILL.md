---
name: teamwork
description: Synchronous Dev Team workflow 02 execution — spec-first, plan-led implementation from single-source roles to a non-Draft PR handoff.
allowed-tools: Bash, Agent
---

# Teamwork

Synchronously executes Dev Team workflow 02 in the current CLI session using single-source role definitions. The skill entry coordinates subagents without editing code or copying role definitions.

## Triggers

```text
/teamwork:task <description>
```

Natural-language trigger: `Use teamwork to implement <feature>`.
Activate only on explicit teamwork intent; casual prompts run directly without subagents.

## Single Source & Authority

Roles resolve directly from the loaded bundle at `../../workflow/dev-team-roles/` (supporting full bundles and symlinks). If source roles or subagent capabilities are missing, fail closed with a setup blocker. Never search target repositories or fall back to copied role files.

- [Team Lead](../../workflow/dev-team-roles/dev-team-team-lead/SKILL.md) — orchestration, scheduling, and escalation
- [Planner](../../workflow/dev-team-roles/dev-team-planner/SKILL.md) — spec and task breakdown
- [Fullstack Engineer](../../workflow/dev-team-roles/dev-team-fullstack-engineer/SKILL.md) — implementation, validation, self-review, and PR creation
- [AI Reviewer](../../workflow/dev-team-roles/dev-team-ai-reviewer/SKILL.md) — spec gate and exact-SHA pre-push review
- Shared rules: [squad](../../workflow/dev-team-roles/dev-team-squad/SKILL.md)
- External policy reference: [Clear small issue](../../workflow/dev-team-roles/dev-team-pr-manager/SKILL.md#clear-small-issue-owner-2026-10-13) (read-only policy link for workflow 03; PR Manager is not a local subagent)

## Execution Flow

```text
Request confirmation → Planner (spec/plan) → AI Reviewer (spec gate)
  → Fullstack Engineer (implement / validate / self-review)
  → AI Reviewer (exact-SHA pre-push review)
  → Original Fullstack Engineer (push reviewed SHA + non-Draft PR)
  → External workflow 03 PR Manager handoff
```

1. **Spec & Plan**: Planner produces spec/plan; AI Reviewer validates via spec gate.
2. **Implementation**: Fullstack Engineer is the sole writer. Retain writer identity if startup/receipt is unknown.
3. **Validation & Self-Review**: Fullstack validates (UI validation required only for user-visible changes) and self-reviews.
4. **Pre-Push Review**: AI Reviewer performs exact-SHA pre-push review (invoking specialist reviews on demand). Review rounds and same-root accumulation follow [squad](../../workflow/dev-team-roles/dev-team-squad/SKILL.md) rules.
5. **Publish & Handoff**: Original Fullstack pushes the reviewed SHA unchanged, creates a non-Draft PR, and hands off to external workflow 03 PR Manager.

## Backend & Rules

- **CLI Backend Priority**: Codex CLI → Claude native → Copilot.
- **Fail-Closed**: Missing bundle sources or subagent capabilities stop immediately with a setup blocker.
- **No Local PRM**: PR Manager is not spawned as a subagent; handoff occurs externally after PR creation.
