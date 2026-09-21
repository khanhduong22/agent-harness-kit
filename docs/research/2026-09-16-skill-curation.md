# Skill curation for agent execution

Status: recommendation only. No skills installed, restored, or removed.
Reviewed against `rules/core.md` and the current local spec, planning, testing,
debugging, review, orchestration, and verification skills. Upstream links use
mutable `main`; pin commit IDs before importing. Research delegation failed
because of a usage limit; the primary agent completed this review.

## Recommendation

Keep OpenSpec as the workflow authority. Adapt selected upstream methods into
existing canonical skills rather than install a second overlapping workflow.
Humans decide requirements and approve designated risk boundaries; agents plan,
implement, run tests, review, and prepare evidence within the approved scope.

## Ponytail

[Source](https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail/SKILL.md)

The useful ladder, reuse-first approach, and root-cause emphasis already appear
in the global rules. Retain them there. Do not import its persistent full/ultra
mode or minimal-check policy as the testing authority. Simplification must
preserve agreed acceptance criteria and repository verification gates.

## Matt Pocock engineering inventory

The complete directory has 18 skills. The following are recommendations, not
claims that the upstream author prescribes this local arrangement.

[Inventory and descriptions](https://github.com/mattpocock/skills/tree/main/skills/engineering)

| Skill | Local disposition |
| --- | --- |
| ask-matt | Skip extra router; existing workflow routing owns this. |
| code-review | Merge Standards + Spec independent review into local review. |
| codebase-design | Add targeted design reference; preserve project vocabulary. |
| diagnosing-bugs | Merge executable reproduction loop into local debugging. |
| domain-modeling | Add for glossary and domain ambiguity; align ADR locations. |
| grill-with-docs | Optional discovery; avoid duplicating interview-me. |
| implement | Skip wrapper; use local orchestrator and implementation workflow. |
| improve-codebase-architecture | Optional explicitly scoped architecture work. |
| prototype | Optional experiment; never count demo as production verification. |
| research | Add or merge into source-driven-development for delegated research. |
| resolving-merge-conflicts | Adapt into git workflow, retaining ownership gates. |
| setup-matt-pocock-skills | Skip competing tracker/bootstrap conventions. |
| tdd | Merge behavior testing and anti-tautology rules into local TDD. |
| to-spec | Adapt testing decisions and scope into OpenSpec; no second spec store. |
| to-tickets | Adapt vertical slices and dependency edges into OpenSpec tasks. |
| triage | Optional when incoming issue volume warrants it. |
| wayfinder | Optional for genuinely large, uncertain initiatives. |
| wizard | Fallback for human-only access or credentials steps. |

Specific primary sources:

- [TDD](https://github.com/mattpocock/skills/blob/main/skills/engineering/tdd/SKILL.md): behavior tests, independent expected values, vertical slices; adapt per-seam confirmation to prior spec approval. Do not copy its review-only refactoring rule automatically.
- [Review](https://github.com/mattpocock/skills/blob/main/skills/engineering/code-review/SKILL.md): separate Standards and Spec agents; supply OpenSpec path and fixed merge-base directly instead of requiring another tracker setup.
- [Diagnosis](https://github.com/mattpocock/skills/blob/main/skills/engineering/diagnosing-bugs/SKILL.md): an executed reproduction command must detect the actual reported symptom; preserve native regression requirements.
- [Spec](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-spec/SKILL.md) and [tickets](https://github.com/mattpocock/skills/blob/main/skills/engineering/to-tickets/SKILL.md): useful testing decisions and dependency structure, but tracker publication and repeated approvals need local adaptation.
- [Design](https://github.com/mattpocock/skills/blob/main/skills/engineering/codebase-design/SKILL.md) and [domain](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md): use selectively, without speculative abstractions.
- [Writing for agents](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL.md): worthwhile additional import outside engineering, for maintaining this harness.

## Local contradictions to resolve before import

1. Global orchestration expects OpenSpec, while spec/planning skills require
   `tasks/plan.md` and `tasks/todo.md`.
2. Spec skill requires human review at each phase; autonomous execution needs
   one approved scope and explicit escalation triggers.
3. Doubt-driven skill requires a repeated cross-model permission conversation.
   Configure an approved review policy instead of per-cycle workflow prompts.
4. Universal highly-scalable architecture wording competes with YAGNI. Require
   measured or specified capacity, with correctness and security preserved.
5. A hardcoded `100% VERIFIED` banner overstates evidence. Display actual tested
   scenarios, counts, environment, and limitations.

## Verification contract to adopt

Map requirement ID to test/assertion and recorded run. The implementation agent
must not weaken acceptance criteria to obtain green tests. An independent
verifier checks missing scenarios and assertion quality, then runs the affected
checks on the delivered revision. Record command, revision or working-tree
identity, environment, exit code, pass/fail/skip counts, and artifact locations.
Videos support review; assertions establish automated pass/fail. Missing or
blocked checks remain unverified. Shipping authorization remains separate.
