# Implementation Plan: Code Review

## Constitution check

This repository has no project constitution or layered context today. Follow its established skill conventions: `skills/<category>/<name>`, progressive references, generated registry/plugin metadata, discriminating eval cases, and `scripts/validate-skills.sh`.

## Design

Place the skill at `skills/repo/code-review`.

### Interface

The skill accepts an optional fixed point. Its output is a read-only review with two top-level axes:

- **Standards:** fan out by changed layer, plus one cross-layer reviewer when required.
- **Spec:** one isolated reviewer over the complete diff and active Spec Kit artifacts.

### Context discovery

Add `scripts/discover_review_context.py` to make baseline, Spec Kit, and layer discovery deterministic. It emits JSON consumed by the review workflow:

- repository root and fixed point;
- changed files;
- routing/context files;
- Spec Kit artifact candidates;
- layer frontmatter and changed-file mapping;
- explicit coverage gaps.

### Progressive references

- `references/reviewer-prompts.md`: exact isolated reviewer contracts.
- `references/output-contract.md`: finding schema and final report shape.
- `references/eval-cases.md`: discriminating cases and graders.

### Registry

Run `scripts/gen_registry.py` to update `skills.json`, README, and `.claude-plugin/plugin.json` from SKILL.md.

## Verification

1. Unit-test context discovery against temporary layered and unlayered git fixtures.
2. Run the skill creator validator.
3. Run `scripts/validate-skills.sh`.
4. Run `scripts/gen_registry.py --check`.
5. Evaluate all cases in `references/eval-cases.md` by inspecting deterministic discovery output and review routing decisions.
