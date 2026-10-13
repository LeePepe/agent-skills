# LeePepe GitHub Autopilot Registration

Owner-authorized workflow registration. On 2026-09-11 the Owner expanded the responsibility from the initial VoxPocket delivery to **all GitHub repositories owned by `LeePepe`**. This is a standing account-level supervision scope, not a single-project or single-PR task. It is not a completed audit or a claim that the live deployment has already been migrated.

## Account-wide coverage and routing

- Discover repositories from authoritative GitHub owner metadata, matching `owner.login == LeePepe` case-insensitively. Include public/private repositories accessible to the authorized account and newly discovered repositories; do not maintain a VoxPocket-only or static project allowlist. Report missing access or incomplete pagination as a coverage gap.
- Include each repository's relevant issues and delivery PRs regardless of who authored them, including non-Dev-Team PRs. For a fork-origin PR, use the **base repository owner** to determine scope and preserve the repository's untrusted-code/secret restrictions. Repositories merely contributed to by LeePepe but owned by someone else are outside this scope.
- Resolve every repository to its own Multica project through the authoritative `github_repo` resource. Preserve each project's Dev Team, workdir, review/CI, release and acceptance rules. An unmapped repository remains a visible routing gap; report it for ownership resolution rather than silently ignoring it or assigning it to VoxPocket.
- Keep archived, disabled or otherwise read-only repositories visible in the inventory, with that limitation recorded; observation responsibility does not override platform restrictions.
- Partition cursors, action ownership, deduplication and retry budgets by repository/project and case. Reconcile with any existing project supervisor so two supervisors do not dispatch or rerun the same case.
- Completion of one issue or PR closes that case only. Continue account-wide supervision until an explicit Owner pause/stop; installation, benchmark and release requirements come from each case, not from the initial VoxPocket example.

## Operating contract

Reuse native Multica autopilot in `run_only` mode on the Owner-approved NAS observer, with the existing ten-minute schedule once readiness is verified. The intended account-level display name is **LeePepe GitHub Delivery Supervisor**. Refresh live IDs, instructions, runtime health and bindings before operating; renaming this document does not rename or reconfigure the deployed agent.

Apply [the autopilot contract](autopilot-contract.md): observe, dispatch, bounded rerun and report only. Dev Team owns code/config/runtime repair; PR Manager adopts reviewed candidates from any author through an exact-SHA handoff. Preserve the Owner-approved common execution computer/daemon and existing provider/model split for Dev Team; the independently hosted observer is not an execution-team migration.

Repository coverage does not grant blanket permission to implement features, install apps, change credentials, alter gates or release software. Use each project's current authority and task acceptance. Owner plan-only/pause decisions suspend the affected case's mutations, not unrelated safe supervision.

## Initial instance and seed case (historical registration)

The following identities locate the original 2026-09-10 instance. The VoxPocket project, issue and PR are the **first covered case**, not the account-wide scope or routing destination for other repositories. Reconcile the existing Multica instance with the expanded contract through a separately authorized configuration change; do not claim account-wide operation from this record alone.

| Item | Identity |
|---|---|
| Workspace | `my` |
| Seed project | VoxPocket |
| Seed repository | https://github.com/LeePepe/VoxPocket |
| Seed delivery issue | MY-1540 |
| Seed external-origin PR | https://github.com/LeePepe/VoxPocket/pull/35 |
| Existing native Multica autopilot | VoxPocket Log Delivery Supervisor |
| Existing observer agent | VoxPocket PR Autopilot |
| Schedule trigger | (Multica ID, resolve via `multica`) |
| Observer runtime | NAS Codex |
| Observer daemon | NAS |
| Dev Team daemon | Current Mac |
| Team Codex runtime | (Multica ID, resolve via `multica`) |
| Team Copilot runtime | (Multica ID, resolve via `multica`) |

The seed project/repository association was verified through its `github_repo` resource. Record IDs are not published here; resolve them through `multica`; display names and checkout paths do not establish identity or prove current runtime readiness.

## Seed-case acceptance, not global defaults

- The recorded VoxPocket connectivity failure had two attempted review runs; further same-failure retry waits for verified repair/readiness instead of resetting the counter each sweep.
- MY-1540 completion includes normal PR merge, a fresh main build, real VoxPocket log receipt, the approved private multi-model audio timing/accuracy evaluation, and a backed-up local App update. Other repositories use their own acceptance criteria. No audio, reference text, transcript, credential or private model configuration belongs in this registration.
- The Owner approved this seed case after reviewing its plan; obtain later pause/resume decisions from current issue evidence. Its completion must not stop supervision of other LeePepe repositories.

## Observation at 2026-09-10T15:06:27Z

The autopilot record was `active`, with `updated_at=2026-09-10T14:50:03Z`; its schedule trigger was **disabled** pending the dedicated NAS runtime/model compatibility repair. Initial dispatches did not establish successful execution. This documents a configured but not yet verified supervisor; it does not claim recurring supervision is operational. This documentation update changed no live configuration.

Resolve current state through `multica autopilot get/runs`, the observer agent/runtime, live GitHub repository discovery and each repository's mapped Multica project/issues. For an actual audit, capture current instruction versions with `updated_at + SHA-256(content)` as required by the skill rather than treating this registration as a substitute snapshot.
