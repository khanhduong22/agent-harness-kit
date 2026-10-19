---
name: llm-eval-design
description: "Design, run, and review evaluation suites (evals) for LLM features, RAG pipelines, and AI agents: task contracts, failure taxonomy from real traces, property-based test cases, programmatic and calibrated LLM-judge graders, per-case paired comparisons, holdout sets, and CI regression gates."
---

Skill 200Lab «LLM eval design: thiết kế và chạy eval cho tính năng LLM, RAG hay agent: bộ case, grader, AI judge, so từng case, cổng regression trong CI» v1 — hướng dẫn do 200Lab soạn cho agent; ai_tutor rules vẫn quyết ngân sách, footer và việc hoàn thành bài. Parts: contract-and-cases, graders-and-calibration, comparison-and-gate, eval-review.

# LLM eval design (200Lab)

200Lab's judgment on designing, running and reviewing evals for something the learner builds on
a model: an LLM feature (classify, extract, summarise, draft), a RAG pipeline, or an agent. What
decision the eval serves, which cases it holds, who grades them, how two versions are compared,
and the gate that stops a regression. The `ai_tutor` rules still decide budgets, the provenance
footer, quizzes and lesson completion; read them first if you have not this session.
Not for a project the `ai_tutor` rules' "Lawful use only" excludes (attacking systems or accounts not the learner's, gambling, fraud or spam, content breaking Vietnamese law); for one, stop and decline as those rules say.
Measuring how well betting odds are predicted, or how often spam or phishing gets past a filter,
is that project, however the eval is framed. Adversarial cases test the learner's own system only.

Talk to the learner in their language; in Vietnamese use mình/bạn and write "khóa".

## Route

- **Build an eval** (a feature before launch, a prompt or model change, a job to keep or kill) →
  agree in a few lines the decision, the task contract and the acceptance rule; pause for the
  learner's yes; then cases (part `contract-and-cases`), graders (part `graders-and-calibration`),
  the baseline run, the comparison and the gate (part `comparison-and-gate`), in that order.
- **Review an existing eval** → no pause: read the case files, graders, last results and the CI
  config; grade with part `eval-review`; write `REVIEW.md` from the template in part `sdlc-chain`
  of skill `agent-harness`, verdict first.
- **One decision** (accept this change, trust this judge, how many cases or repeats, the cheaper
  model) → answer first from the learner's results; ask once for the number that is missing;
  read only the part that owns the decision.
- Elsewhere: trigger and outcome evals of one agent skill → `agent-skill-authoring`; tools,
  guardrails and the run contract of an agent → `agent-harness`; tests of ordinary code →
  `test-strategy`; one wrong output to trace to its cause → `systematic-debugging`, then the case
  joins the set here; sizing a RAG system → `system-design`; a knowledge wiki → `llm-wiki`; the
  checker inside an overnight loop → `agent-loop-orchestration`. Say which in one line.
- Read part `retrieval-200lab` of `agent-harness` before your first `ai_tutor_recommend`.

## How 200Lab sees an eval

- **An eval serves a decision.** Ship this prompt, switch to the cheaper model, keep the job.
  The acceptance rule is written before any result is seen; "looks fine" is not a rule.
- **Contract before cases.** Inputs, the output shape, what correct means, what the feature
  must never do, and the exception path. If a rule or a lookup already gets most cases right,
  that deterministic baseline is what the model must beat.
- **Failures come from traces, not imagination.** Read real runs (or realistic trial runs before
  launch), label every failure, group the labels; the taxonomy decides which cases and graders
  exist. A category with no case is untested, whatever the score says.
- **Expected properties, not golden strings.** Each case states what must hold (the label, the
  amount, the cited document, a refusal, no personal data, under N words). A golden string fails
  a correct paraphrase and passes a fluent wrong answer.
- **Code grades first.** Exact match and programmatic checks, then invariant checks on the
  output, and an LLM judge only for what code cannot check, with a rubric, calibrated against
  human labels with the agreement measured. The judge comes from another model family; a
  same-family judge is a documented exception, calibrated and reported as a limit.
- **Compare per case, never two averages.** Improved, regressed, same-right, same-wrong, sliced
  by failure category and by the cases that cost the most. One regression on a critical case
  outweighs a higher mean.
- **Variance is part of the result.** Repeat each case at the production temperature; a gap
  smaller than run-to-run noise is no gap. Report counts with the percentages: on 30 cases one
  flip moves the score 3.3 points.
- **Cost and latency are columns of every run.** A quality win that doubles the cost or the p95
  is the learner's call, made on numbers.
- **The eval stays out of the prompt.** No case becomes a few-shot example, a holdout nobody tunes
  against decides, and a gain on the dev cases that the holdout does not show is overfitting.
- **The gate is code.** A command that exits non-zero on a regression by the written rule, seen
  failing on a seeded regression before anyone trusts its green.

## Scale tier

Decide from signals; one signal of a higher tier moves the eval up. Counts are 200Lab working
bars (`own`), not standards.

| Tier | Signals | The eval must have | Allowed shortcuts (exit criterion) |
|---|---|---|---|
| PoC | one builder, before launch, trying prompts | the contract, a taxonomy from 20+ traces or trial runs, 20 to 30 cases with properties, programmatic graders, baseline vs candidate per case, 3 repeats | the builder grades the rest by hand, no judge, no CI; exit when real users see output |
| MVP | real users; prompt, model or retrieval changes most weeks | + 50 to 150 cases (real majority, adversarial, edge), a 20% holdout, any judge calibrated on 50+ human labels with agreement reported, slices, cost and latency, the gate run on every change | calibration once; exit before unattended actions or several people changing prompts |
| Production | unattended actions; money, messages or personal data; several people change prompts | + every incident becomes a case, the judge recalibrated on any judge or rubric change, the gate blocking merge in CI and tested with a seeded regression, versioned case files, a cost cap per run | none for the security rows |

Build only the chosen tier's rows; write the next tier's rows down as later work.

## Security

- Cases cut from real traces carry users' data: scrub or pseudonymise before they enter the
  repo, keep raw transcripts out of git, and send cases to a judge provider only under the same
  data policy as production.
- Include prompt-injection cases (an instruction hidden in a retrieved document or a user
  message) when the feature reads untrusted text; they run against the learner's own system.
- Provider keys come from the environment the existing scripts use; the eval never prints them.

## Getting 200Lab lessons

- `ai_tutor_recommend` once, after the contract, with `skill: llm-eval-design` and up to three
  queries, one subtopic each, for example `"viết eval case sao cho phép chấm không tự đánh lừa
  mình"`, `"người chấm và AI judge không đồng ý"`, `"điểm tổng tăng có đủ để nhận thay đổi
  không"`, `"việc nào thật sự cần giao cho LLM"`.
- Courses by decision: the decision, slices, cases, dataset and holdout, judge agreement, paired
  comparison (Đo chất lượng model và ứng dụng AI); task contract, deterministic baseline, trial
  records, structured output, temperature, examples in the prompt, cost and handoff (Xây dựng tính
  năng LLM có phạm vi rõ ràng); traces, repeatable runs, RAG fit, grounding (Agent Harness
  Foundations). Check each hit's `courseSlug`: these courses share lessons. Gaps, labelled
  `own`/`external`: retrieval metrics (recall@k, MRR), judge bias studies, significance tests, CI
  wiring. Each part names its lessons by slug.

## Output

- In the learner's repo, by default `evals/<feature>/`: `CONTRACT.md` (decision, contract,
  acceptance rule), `taxonomy.md`, `cases.jsonl` and `holdout.jsonl`, the graders, one run
  command, `results/` per run, and `REPORT.md` (per-case table, slices, agreement, cost and
  latency, decision).
- Every item carries `200Lab`, `own` or `external`; every 200Lab claim names a lesson by title
  with its `url`.
- Tell the learner the verdict, the cases that regressed, the judge's agreement number and,
  from MVP, the gate command.

## Done-check

- `cases.jsonl` and `taxonomy.md` exist; every case names its source (real, adversarial, edge),
  its category and its expected properties; every category has at least one case.
- Every judged criterion shows agreement against a human-labelled sample (n, percent, kappa),
  or is marked untrusted in `REPORT.md`.
- `REPORT.md` shows baseline vs candidate per case with repeat pass rates, cost and latency, under
  the acceptance rule as written before the run.
- MVP and up: the gate command exits 0 on the baseline and non-zero on a seeded regression (both
  outputs pasted), and the leakage check (part `comparison-and-gate`) printed no hit.
- `ai_tutor_recommend` ran once; lesson reads stayed within 12.
