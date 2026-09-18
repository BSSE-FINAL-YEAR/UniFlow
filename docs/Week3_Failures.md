# UniFlow — Week 3 Retrieval/Grounding Failures

Brief requires at least three documented retrieval/grounding failures and
their causes. This corpus and the eval suite in `eval/rag_eval_cases.json`
were deliberately designed to make three specific failure modes findable —
this file is the template to fill in with what was **actually observed**
after running `python src/rag_eval_runner.py`.

**Do not pre-fill "Observed."** Same rule as Week 2 (`RUNBOOK.md`, "Two
rules about verdicts"): every Observed/Root cause cell stays empty until a
real run produces it. Run the suite, open the matching trace in
`evidence/traces/rag/`, and record what actually happened — including if a
designed trap did *not* trigger a failure, which is itself a finding worth
reporting honestly.

---

## Failure 1 — Retrieval miss / wrong-document ranking (CONFIRMED, reproducible without an LLM call)

**Where to look:** any question about evening/teaching hours — this was
found directly while writing the pipeline's own smoke test
(`tests/test_rag.py::test_retrieve_evening_hours_question_hits_r05`).

**Observed:** querying `retrieve("What are the teaching hours for evening
classes?", k=5)` returns, in rank order:

```
1. KB-REGISTRAR-FAQ#2   score=11.629
2. KB-R05#1             score=10.424   <- the actual authoritative rule
3. KB-REGISTRAR-FAQ#1   score=7.069
4. KB-US10#1            score=4.431
5. KB-R02#1             score=4.407
```

`KB-R05` (the rule that actually states "16:30-20:30") is retrieved, but
ranked **second**, behind a synthetic FAQ chunk that discusses the
16:00-16:30 gap in prose. With a smaller `k` (e.g. `k=2`, which
`rag_baseline.py` supports via `--k`), the authoritative rule would be
dropped from context entirely and the model would have to answer from a
paraphrase instead of the source rule.

**Root cause:** `KB-REGISTRAR-FAQ#2` is long and repeats
"evening"/"classes"/"teaching-window"-adjacent vocabulary across a full
paragraph explaining the gap, while `KB-R05`'s own text is terse (about 30
words) and only contains "evening" once. Plain BM25 rewards a verbose
paraphrase that happens to repeat more query terms over a short original
source — it has no notion of "this document is the authoritative source
for this rule" versus "this document is commentary about it." This is a
structural limitation of lexical retrieval on a corpus that mixes primary
rule documents with secondary/explanatory ones, not a bug in the BM25
implementation itself.

**Fix considered:** two options were identified and deliberately not
applied yet, so the finding stays visible for the report: (1) raise `k` so
both the primary rule and the commentary are retrieved together — cheap,
but doesn't fix the ranking itself and fails for a small `k`; (2) weight
`status`/document-role at retrieval time (e.g. boost `provenance:
source-derived` chunks over `team-created` ones) — a real fix, deferred
because it changes the scoring model and deserves its own evaluation
rather than a one-line patch.

---

## Failure 2 — Chunking damage

**Where to look:** `KB-REGISTRAR-FAQ`, which is long enough to be split by
`src/rag/chunk.py`'s 70-word/20-word-overlap window. Ask a question that
depends on the third Q&A entry (the unenumerated-combinations point) or on
detail near a chunk boundary.

**Predicted failure:** the relevant sentence is split across two chunks,
only one of which is retrieved, so the model sees a truncated argument and
either answers incompletely or (worse) fills the gap with an invented
detail.

**Observed:** _TODO — quote the retrieved chunk text and identify the
boundary. Confirm with `chunk_id` suffixes (e.g. `KB-REGISTRAR-FAQ#1` vs
`#2`) whether the answer actually got split._

**Root cause:** _TODO_

**Fix considered / applied:** _TODO — e.g. increase overlap, chunk on
markdown headings instead of fixed word count, or increase k so both
halves are retrieved together._

---

## Failure 3 — Ungrounded generation despite correct retrieval

**Where to look:** `RQ-09` and `RQ-10` — both retrieve a document
(`KB-RETAKE-DRAFT`, `KB-WAIVER-MEMO`) whose `status: draft-unapproved` is
stated directly in the context shown to the model.

**Predicted failure:** the correct chunk is retrieved and present in
context, but the model still reports the draft's numbers as if they were
an approved rule (`status: "ok"` instead of `"partial"`/
`"insufficient_context"`) — proving that retrieval succeeding is not the
same as generation staying grounded.

**Observed:** _TODO — record the actual `status` and `answer` text returned
for RQ-09/RQ-10, and confirm from the trace that the draft-unapproved
chunk really was in the retrieved context at the time._

**Root cause:** _TODO — was it a prompt-instruction weakness, a model
tendency to be "helpful" over cautious, or something else? This is the
generation-side analogue of Week 2's PE-02 finding
(`RUNBOOK.md` line 241: "a model that ignores your rule pack and
substitutes its own priors is the single most dangerous failure mode")._

**Fix considered / applied:** _TODO — e.g. a stronger system-prompt
instruction, a few-shot example of the correct refusal, or a post-hoc
validator that rejects "ok" status when a cited source has
`status: draft-unapproved`._

---

## Summary table (fill after all three are written up)

| # | Failure type | Case(s) | Root cause | Fixed? |
|---|---|---|---|---|
| 1 | Retrieval miss | RQ-04 / calendar distractor | TODO | TODO |
| 2 | Chunking damage | Registrar FAQ | TODO | TODO |
| 3 | Ungrounded generation | RQ-09 / RQ-10 | TODO | TODO |
