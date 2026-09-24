# Feature Specification: Code Review

## Intent

Create a reusable repository review skill that preserves Matt Pocock's two independent review axes while making repository context discovery deterministic for Spec Kit and layered-agent-context repositories.

## User scenarios

1. A Fullstack Engineer self-reviews a branch before handoff. The skill resolves the branch baseline, reads the feature spec and repository standards, reviews every changed layer, and returns actionable findings without editing code.
2. A reviewer inspects a PR spanning several layers. Each changed layer is checked against its own `tech-context` frontmatter, while a separate Spec axis checks the whole diff against Spec Kit intent and acceptance.
3. A repository lacks Spec Kit or layer metadata. The skill reports exactly which context is missing and performs an explicit degraded review without inventing requirements or layer rules.

## Functional requirements

- **FR-001 — Fixed point:** Accept a supplied commit/branch/tag or derive the target branch merge-base. Fail clearly on an invalid or empty diff.
- **FR-002 — Read contract:** Read the repository's `AGENTS.md`/`CLAUDE.md` routing index before following context pointers.
- **FR-003 — Three context layers:** Discover and distinguish constitution/red lines, technical context, and feature requirements.
- **FR-004 — Spec Kit:** Prefer the active feature's `spec.md`, `plan.md`, and `tasks.md`; use contracts/research only when linked by those primary artifacts.
- **FR-005 — Layer mapping:** Map every changed path to a layer using the repository layer index and nearest layer `tech-context.md`/`CONTEXT.md` frontmatter.
- **FR-006 — Standards axis:** Review each changed layer against repository standards, its `depends_on`, `roles`, `red_lines`, ownership, and declared verification command.
- **FR-007 — Spec axis:** Review the complete diff against feature intent, acceptance, scope, plan constraints, and task completion.
- **FR-008 — Cross-layer check:** When two or more layers change, check dependency direction, declared task boundaries, and whether the change should have been split by layer.
- **FR-009 — Parallel isolation:** Run the Spec reviewer and layer Standards reviewers in parallel so evidence and conclusions do not contaminate one another.
- **FR-010 — Structured findings:** Every finding carries axis, severity, layer, path/line when available, source citation, evidence, and remediation. Keep Standards and Spec results separate.
- **FR-011 — Review only:** Do not edit files, commit, push, create issues, or merge. The caller decides how findings are fixed.
- **FR-012 — Degraded mode:** Missing Spec Kit or layer context reduces coverage explicitly; it never becomes fabricated context or a silent pass.

## Severity

- **P0:** security/privacy red-line breach, constitutional violation, destructive defect, data loss, or implementation contradicts a required acceptance criterion.
- **P1:** incorrect behavior, missing required behavior/test, layer dependency violation, or material scope error.
- **P2:** maintainability, documentation, or non-blocking quality improvement backed by a cited standard.

## Acceptance criteria

- A single-layer fixture produces one Standards packet plus one Spec packet.
- A two-layer fixture produces two layer packets, one cross-layer packet, and one Spec packet.
- Findings cite the exact spec/constitution/tech-context rule rather than generic preference.
- An unmapped file is reported as `layer: unmapped`, not forced into a guessed layer.
- Repositories without Spec Kit or layer metadata receive a clearly labeled degraded report.
- The skill passes repository skill validation and discriminating eval cases cover baseline, Spec Kit, layer, cross-layer, degraded, and clean-diff behavior.

## Out of scope

- Fixing findings.
- Running CI or merging PRs.
- Installing Spec Kit or layered-agent-context into the target repository.
- Replacing the Dev Team's independent AI Reviewer stage.
