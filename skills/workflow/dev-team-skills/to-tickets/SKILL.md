---
name: to-tickets
description: Turn an accepted spec and plan into vertical product slices plus a dependency graph of layer-scoped implementation tasks. Use when Planner Lead creates or refines Spec Kit `tasks.md` or Multica child issues for work that spans one or more repository layers.
---

# To Tickets

Extend Matt Pocock's tracer-bullet decomposition for Spec Kit and layered execution. Vertical slices define delivered user value; `Txxx` tasks define Fullstack layer ownership.

## Workflow

1. Read the accepted spec, plan, constitution, layer indexes, changed domain context, and existing task graph. Use repository terminology and preserve declared dependency direction.
2. Map every vertical slice to one Spec Kit user story and phase. Each slice must deliver one narrow, independently demonstrable or verifiable user outcome and cover its complete acceptance surface. Give every slice its upstream slice dependencies.
3. Under each user-story phase, create the minimum **layer-scoped implementation tasks** needed to realize it. Serialize every executable row using native Spec Kit syntax: `- [ ] Txxx [P?] [US#] Action with exact file path`. Use `[P]` only when files do not conflict and no incomplete dependency blocks it.
4. Add a stable metadata table keyed by `Txxx` adjacent to the task phase. Each task must declare:
   - owning layer and context pointer;
   - concrete files or narrow paths in scope;
   - sibling files, layers, and behavior out of scope;
   - public interface or contract affected, or an explicit internal-only boundary;
   - task-local acceptance criteria and exact layer verification;
   - blocking task edges and the vertical slice it serves.
5. Express cross-layer behavior through explicit contracts and blocking edges in the metadata table. A Fullstack task changes one layer. When end-to-end proof requires assembled layers, add a `Txxx` verification task owned by the repository's declared integration/test layer; do not hide cross-layer implementation inside it.
6. For a wide mechanical refactor that cannot stay green as a vertical slice, use expand–migrate–contract. Keep each migrate batch layer-scoped and make the final contraction depend on every migration.
7. Validate the graph:
   - every spec acceptance criterion is covered by a slice;
   - every slice is realized by one or more layer tasks;
   - every task has one owner layer and a runnable verification command;
   - dependency edges are acyclic and follow layer direction;
   - parallel tasks have non-conflicting files and contracts;
   - no task asks Fullstack Engineer to infer missing scope or product behavior.
8. Before independent planning review, write only repository Spec Kit artifacts. After `PASS` or `PASS WITH FOLLOW-UP` for the exact planning revision, reconcile Multica slice parents and child issues from the reviewed graph. Preserve `US#` and `Txxx` in issue descriptions so tracker state can be traced back without flattening the hierarchy.

Escalate only unresolved product, content, or authority decisions. Granularity and dependency mechanics are Planner Lead responsibilities.
