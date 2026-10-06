---
name: teamwork
description: Multi-agent pipeline for complex tasks — spec-first, plan-led execution with gated review, verification, and shipping. team-lead orchestrates; specialist agents do the work.
allowed-tools: Bash, Agent
---

# Teamwork Skill

Run a structured multi-agent pipeline where `team-lead` orchestrates every stage and delegates
all real work to specialist sub-agents. The skill entry itself only validates readiness, reads
team config, and spawns `team-lead` — it never implements, plans, or edits files directly.

> Vendored copy. The authoritative source is the standalone `teamwork` plugin repo. Keep this
> copy's `SKILL.md` and `agents/*.md` in sync with each other; do not describe behavior an agent
> file does not implement.

## Triggers

```text
/teamwork:task <description>
```

Natural-language trigger:

```text
Use teamwork to implement <feature>
```

Activation safety:
- Only activate for explicit teamwork intent (`/teamwork:task ...` or a clear "use teamwork" request).
- Do not activate for casual chat, greetings, or unrelated prompts.
- Without an explicit trigger, normal Claude execution may run directly — no `team-lead`/subagents.

**After the required read-only preflight: immediately spawn `team-lead`.** Using `Write`, `Edit`, or any file-mutating
tool in this skill entry is a hard pipeline violation.

## Pipeline

```text
team-lead  (triage: feature | bugfix | bugfix-docs; docs_needed?)
  ├── planner-lead (mode:spec)   → reviewable spec/PRD + optional docs/ target-state docs
  │     ├── researcher(s)         → parallel single-scope research workers
  │     └── designer              → only when design output is required
  │   ▶ SPEC GATE: plan-reviewer(spec-review) + pm(spec-gate)   ← features / bugfix-docs
  ├── planner-lead (mode:breakdown) → executable plan derived from the approved spec
  │     └── linter                → layered dependency lint contract (inter- + intra-layer)
  │   ▶ PLAN GATE: plan-reviewer(review) + pm(plan-gate)
  ├── fullstack-engineer  → executes tasks in isolated worktrees
  ├── verifier            → command-level verification evidence (lint mandatory)
  ├── pm (delivery-gate)  → delivery supervision over verifier evidence
  ├── final-reviewer      → code review + specialty review coalition
  │     ├── security-reviewer
  │     ├── devil-advocate
  │     ├── a11y-reviewer
  │     └── perf-reviewer
  ├── user-perspective    → mandatory real UX testing gate (Playwright / XCUITest)
  └── git-monitor         → commit / PR output → PRM handoff (only after user-perspective passes)
```

Bugfix fast path: a plain `bugfix` skips the spec phase and spec gate, going straight to
`planner-lead (mode:breakdown)`. The skip is recorded as a controlled exemption in the run ledger.
A `bugfix-docs` (defect caused by inaccurate docs) runs the spec phase to unify docs first.

## Stage Model

```text
triage → [spec → spec-gate]? → breakdown → plan-gate → execute → verify
       → pm-delivery → final-review → user-perspective → ship
```

The `[spec → spec-gate]?` phase runs for features and bugfix-docs; a plain bugfix fast-paths past it.

Here `ship` ends this implementation with a successfully created/updated PR and its required local evidence,
not merge or release. PRM alone follows non-Draft CI/review/approval and delivery; Draft stays with its original
author/approval path. Preserve all existing pipeline gates and the target repo's remote completion rules.

Gate policy (mandatory for each task type — no "simple task" or "CLI unavailable" exemption):
- **Spec gate** (features / bugfix-docs): passes only when `plan-reviewer` (spec-review) AND `pm` (spec-gate) both pass. The merged goal-list confirmation lives here. Bugfix fast-path skips this as a recorded exemption.
- **Plan gate**: passes only when `plan-reviewer` (review) AND `pm` (plan-gate) both pass.
- **Delivery gate**: `verifier` evidence (lint required) plus `pm` (delivery-gate) supervision.
- **Final gate**: `final-reviewer` consolidated verdict over the specialty coalition.
- **User-perspective gate** (non-skippable for user-facing changes): real automated UX testing.
  `git-monitor` is blocked until it passes. 🟡 ITERATE → one repair cycle, then re-run. 🔴 FAIL → halt.

A returned 🟡 means exactly one bounded repair cycle. 🔴 halts unless the user explicitly overrides.

## Plan Integrity (portable, no external libs)

There is no `pipeline-lib.sh`. State lives only in the spec/plan files. Use plain shell:

- **Artifact separation**: the reviewable spec is `$REPO_ROOT/.claude/spec/<slug>.md`; the derived
  executable plan is `$REPO_ROOT/.claude/plan/<slug>.md`; target-state project docs live under `docs/`.
- **Spec identity** is the sha of the approved spec file:
  `shasum -a 256 "$SPEC_PATH" | awk '{print $1}'`. `team-lead` recomputes it before the spec gate and
  before breakdown; a change means the spec was mutated after approval → re-run the spec gate.
- **Plan identity** is the sha of the approved plan file:
  `shasum -a 256 "$PLAN_PATH" | awk '{print $1}'`. `team-lead` recomputes it before execution and
  before each gate; a change means the plan was mutated after approval → re-run the plan gate.
- **Repair budget** is a single automatic cycle per gate, tracked in `team-lead`'s reasoning.
  Exhausted budget with a still-failing gate → return `needs_manual_fix`, never loop.
- **Resume** reads the spec/plan `status:` fields and continues from the first phase/stage not done.

## Workflow

### 1. Read repo team config

```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
cat "$REPO_ROOT/.claude/team.md" 2>/dev/null
```

If `.claude/team.md` exists, read: review mode (`review` or `adversarial-review`), preferred
verification commands (`## Verification`), and per-agent model config.

### 2. Detect optional CLI backends

```bash
COPILOT_BIN=$(which copilot 2>/dev/null)
CODEX_BIN=$(which codex 2>/dev/null)
```

Backend priority applied *within* each spawned executor/researcher (never inline in the entry):
Copilot CLI → Claude-native → Codex CLI (tertiary fallback). CLI unavailability never collapses a
pipeline stage into the skill entry or into `team-lead` — every stage is always a spawned agent.

### 3. Delegate to `team-lead`

Resolve the required workflow contract from this loaded skill bundle before delegation. Set
`TEAMWORK_SKILL_DIR` to the directory containing the loaded `SKILL.md`, using the runtime's actual
source location (it may be a symlink), not the consumer repo or `.claude/agents` directory.
Resolve the **actual selected team-lead file** from the runtime's role discovery and existing override priority;
bind it as `TEAM_LEAD_ROLE_FILE`. If that selection cannot be established, stop before delegation rather than
assuming the bundled role will run. Bind paths as data, not evaluated shell text. This read-only preflight
checks its mandatory handoff interface and prints the authoritative contract pointer:

```bash
: "${TEAMWORK_SKILL_DIR:?loaded teamwork skill directory is required}"
: "${TEAM_LEAD_ROLE_FILE:?actual selected team-lead file is required}"
TEAMWORK_SOURCE=$(cd "$TEAMWORK_SKILL_DIR" && pwd -P)
WORKFLOW_DIR=$(cd "$TEAMWORK_SOURCE/../../workflow" && pwd -P) || exit 1
WORKFLOW_CONTRACT_PATH="$WORKFLOW_DIR/README.md"
[ -f "$WORKFLOW_CONTRACT_PATH" ] && [ -r "$WORKFLOW_CONTRACT_PATH" ] || {
  echo "required workflow contract is unavailable in the loaded bundle" >&2
  exit 1
}
python3 "$TEAMWORK_SOURCE/scripts/check_contract_handoff.py" team-lead "$TEAM_LEAD_ROLE_FILE" || exit 1
printf '%s\n' "$WORKFLOW_CONTRACT_PATH"
```

Pass that path as `workflow_contract_path` to team-lead and preserve it through the git-monitor handoff.
Also pass `teamwork_source_dir` as the resolved physical `TEAMWORK_SOURCE`, so the copied team-lead uses
the same read-only compatibility check immediately before invoking its selected git-monitor.
Overrides keep priority and ownership: compatible local changes outside the mandatory interface remain;
an incompatible or unverified selected role stops with a setup blocker. Never overwrite it or silently choose
another role. Read the selected role for conflicting instructions as well: the interface check does not certify
arbitrary customization or prove model behavior. Recheck selection on resume/before invocation if it changed.
Missing bundle/contract is a setup blocker; do not copy policy, substitute a moving remote version or
silently omit the required read. The runtime pointer belongs to the invocation, not a committed machine path.

**HARD STOP — mandatory Agent delegation:**
- After preflight and selected-role compatibility succeed, spawn `team-lead` via `Agent`. Do not implement, plan, or edit anything here.
- If `Agent` delegation fails, report the failure and stop — never fall back to local implementation.

```text
Agent: team-lead
Prompt: <user's description>
        workflow_contract_path: <resolved WORKFLOW_CONTRACT_PATH from preflight>
        teamwork_source_dir: <resolved TEAMWORK_SOURCE from preflight>
        Routing preferences: <from .claude/team.md, or "use defaults">
        CLI availability: copilot=<true|false> codex=<true|false>
```

### 4. Report outcome

After `team-lead` returns, report only (no further implementation). Include:
- triage decision (`task_type`, `docs_needed`, whether the spec gate ran or was exempted)
- spec path and plan path with gate outcomes (spec / plan / delivery / final / user-perspective)
- modified files grouped by executor
- verification result with command evidence (lint evidence required)
- final review key findings
- failed/skipped tasks and follow-ups
- the stage-level execution ledger `team-lead` returns

## Per-Repo Customization

Drop a `.claude/team.md` in the target repo to override defaults:

```markdown
## Review Mode
default: adversarial-review

## Verification
- npm run lint
- npm test

## Models
planner-lead: opus
fullstack-engineer: sonnet
```

Project-level agent overrides in `.claude/agents/<role>.md` take priority over the shipped ones.

## Constraints

- The skill entry must not edit files or run its own post-delegation verification.
- Always delegate real work to `team-lead`; `team-lead` in turn spawns every stage as a sub-agent.
- Require spec gate (features), plan gate, delivery gate, final-review gate, and user-perspective
  gate unless the user explicitly overrides (recorded in the run). Bugfix fast-path may skip the
  spec gate as a recorded exemption.
- Enforce a single bounded automatic repair cycle; re-run gates after any code-changing repair.
- `researcher`/`designer`/`linter` are planning-support roles — they never execute coding tasks.
- Require `team-lead`'s final output to include a stage-level execution ledger
  (`role / model / tools / skills / status / evidence`).

## Shipped Agents

- `team-lead.md`
- `planner-lead.md`
- `researcher.md`
- `designer.md`
- `linter.md`
- `plan-reviewer.md`
- `pm.md`
- `fullstack-engineer.md`
- `verifier.md`
- `final-reviewer.md`
- `security-reviewer.md`
- `devil-advocate.md`
- `a11y-reviewer.md`
- `perf-reviewer.md`
- `user-perspective.md`
- `git-monitor.md`

Install into a repo (or `~/.claude/agents/`) when needed:

```bash
cp agents/*.md ~/.claude/agents/
```

Copying role files does not copy their workflow contract. Even with preinstalled roles, use the step 3
bundle resolution and pass its pointer through the invocation; a direct role caller must provide the same
required input. Do not resolve bundle-relative paths from the copied role's destination.
