# Repository gate adoption

## Effective versus proposed

The 2026-09-25 readback of the active default-branch ruleset showed deletion and force-push protection
and a required PR, but no required checks. Code-owner review and stale-review dismissal were false.
The App could not read classic branch protection (403), and the ruleset response omitted bypass actors;
those surfaces are **unverified**, not evidence of absent protection or approved bypass.

The repository previously had only validate-skills CI and no CODEOWNERS. This candidate adds the
published shared-ci v0.1.0 caller, review callers and important-path coverage. These files do not
install remote protection. Existing validate-skills commands and job identity remain unchanged.

| Setting | Observed old value | Proposed value |
|---|---|---|
| Required status checks in active ruleset | no rule | quality / aggregate; codex-review-target / codex-review; validate |
| Require code-owner review | false | true |
| Dismiss stale reviews on push | false | true |
| Extra required approvals | 0 | 0 (preserve) |
| Extra approval for unattributed changes | true | true (preserve) |
| Last-push approval / resolved threads | false / false | false / false (preserve) |
| Bypass actors | omitted from App response; unverified | empty list; no bypass |
| Strict required-check policy | no status-check rule | false, as published template |
| Delete / force-push protection | enabled | preserve |
| Allowed merge methods | squash, merge, rebase | preserve |

`policy/main-protection.proposed.json` is the exact proposed payload, not an applied rule or approval.
Before applying it, the Owner must obtain a complete fresh readback (including classic protection and
bypass actors), preserve every additional or stronger requirement, and approve the exact diff.
No setting, runner registration, license, release or merge is authorized by this document.

## Bootstrap hold

- Keep the adoption PR Draft under explicit Owner hold. Labels do not replace server enforcement.
- The review workflow is read from main; this initial PR cannot prove that new caller works merely by
  adding it. A suitable pre-existing trusted review runner must be confirmed; no runner is registered here.
- Install required check names only after they are observed on real runs. Owner approval of an exact
  bootstrap candidate is distinct from claiming the final automated merge contract is installed.
- Do not enable immediately executable auto-merge before protection or exact Owner approval is verified;
  never disable an existing auto-merge request. W4 owns the later lifecycle.

## Validation and recovery

`scripts/verify --all` runs the pinned unmodified contract audit, workflow lint, skill validators,
registry consistency, Python/shell syntax and deterministic unit/integration tests. The legacy
validate-skills workflow continues to run its original checks independently.

Text safety tests are not behavioral evaluations. The multica-issue evaluation reference specifies
dirty-checkout, hook-failure, explicit-hold, live-run/API-error and missing-spec fixtures. Independent
agent evaluation and real dispatch remain unmeasured unless separately run and recorded.
Consumer template builds, UI tests and product effectiveness are outside these repository tests.

If verification fails, keep the failure and repair the owned cause; do not weaken scanners or gates.
If the dependency cache is damaged or at the wrong pin, verification preserves it and stops. Inspect
and explicitly preserve/remove that exact cache before fetching again; no automatic recursive deletion.

Rollback is a reviewed revert of the affected commit(s), keeping the existing validator workflow and
remote protections. Reverting files does not revert rulesets. If a remote gate has since been installed,
prepare a coordinated Owner-approved gate transition before removing its emitter, so checks cannot
remain pending forever. Do not rewrite history or remove another task's worktree.
