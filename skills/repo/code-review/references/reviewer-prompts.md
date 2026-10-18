# Reviewer Prompt Contracts

Use these contracts as prompt payloads. Include exact diff commands or bounded diff text, commit list, and source paths. Ask reviewers for concrete findings only; no praise or summary prose.

## Spec reviewer

Review the complete change against the supplied fixed native spec/plan/issue or Spec Kit artifacts. Absence of Spec Kit alone is not missing intent. These packets apply within the caller's assignment; full independent review covers both axes, self-check is not independent acceptance, and a restricted role does not gain extra responsibilities from this template.

Return every instance of:

- required intent or acceptance that is missing, partial, or implemented incorrectly;
- behavior or files outside declared scope;
- plan/contract constraints contradicted by the implementation;
- internal task/acceptance items claimed complete without corresponding implementation artifacts, whether recorded in a native plan or `tasks.md`.

For each finding return the output-contract fields. Quote the requirement source. Do not apply repository-style preferences unless they are also specification requirements.

## Layer Standards reviewer

Review only the supplied layer diff. Treat the constitution, repository standards, and this layer's tech-context as authoritative.

Check:

- every `red_line` projected onto the layer;
- imports/dependencies against `depends_on`;
- intra-layer dependencies against `roles` and top-level `canonical_roles`;
- changes outside the layer's `owns` responsibility;
- required test artifacts or coverage explicitly named by supplied authority;
- security, privacy, correctness, failure paths, documentation, and code-quality smells supported by cited repository rules.

Return no finding that requires inspecting another layer. Instead return a cross-layer concern with evidence for the aggregator.

Inspect content only. Do not execute build, test, lint, hook, simulator, hardware, or CI commands; do not evaluate whether FS ran local tests or whether a gate passed. Do not emit optional improvements or generic preferences.

## Cross-layer reviewer

Review only relationships between changed layers and unmapped/top-level files.

Check:

- package dependency direction and `depends_on` consistency;
- whether changed lower layers account for every `depended_by` consumer affected by their interface change;
- whether real producer/consumer contracts and affected scope match the fixed target and its internal task/acceptance mapping;
- whether the atomic cross-layer change is covered and verifiable as a target; do not demand a separate task, issue or PR for each layer;
- whether an unmapped file is intentionally top-level or indicates missing/stale layer context.

Do not repeat layer-local style findings.

## Reviewer return format

Return a JSON array of finding objects matching `output-contract.md`. Return `[]` when there are no findings. Do not produce a verdict; aggregation owns axis results.
