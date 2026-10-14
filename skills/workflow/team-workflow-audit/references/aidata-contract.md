# aidata / AIDash Contract

The audit output is append-only, immutable, structured, and redacted. Do not copy full raw daemon or session logs.

Data progression:

`team_audit_snapshot → L1 ingest → L2 normalized evidence → L3 case/finding facts → L4 audit metrics → L5/AIDash views`

Required identities are `snapshot_id`, source stable ID, case/subject ID, finding fingerprint, instruction observation hash, event timestamp, agent attempt ID, actor role, cycle kind, artifact identity, problem fingerprint, delivery issue, release/build, and observation event. Consumers deduplicate by stable identity and retain provenance.

AIDash may show the Owner summary, scope, evidence coverage, findings, timelines, individual metrics, per-role repeat metrics and causes, Task Effectiveness lineage and pending observation state, approval state, and Archify links. It must present confirmed positive, confirmed negative, pending, and unknown counts together. It may record Owner acknowledgement/approval or effectiveness confirmation as new events. It must not mutate source issues/runs, dispatch agents, or remediate automatically.

Resolve repositories/projects through stored authoritative mappings or source metadata. No local checkout path is part of this contract.
