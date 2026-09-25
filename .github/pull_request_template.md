<!--
PR goals: base = default branch; one purpose; one layer scope where possible;
independently mergeable. Stacked PR? After its base merges, retarget to main and
`git rebase --onto origin/main <old-base-tip>` before merging (squash merges
otherwise make the stacked branch conflict).
-->

## Existing behaviour

<!-- What the code does today that this PR touches, including behaviour that must stay unchanged. -->

## Intent

<!-- What changes and why. Link the task/issue/spec. -->

## Compatibility

<!-- API, data, config and UX compatibility; migrations; how to roll back. Write "no change" if so. -->

## Removed or weakened tests or policy

<!-- Explain test edits/deletions, lost coverage and replacement evidence for normal quality/AI review. Ordinary in-scope test changes do not require an Owner approver or owner-review label by themselves; applicable AI Plan-Review still runs. Separately identify policy/gate/permission changes and their required Owner decision (pending when not approved). Write "none" when neither applies. -->

## Test evidence

<!-- `scripts/verify` result and the tested SHA (the PR head). A new push invalidates this. -->
- Command:
- Result:
- Tested SHA:
