# Prompt Version History — UniFlow QA Agent

Group I | BSE4104 | Maintained by Yohana Mahamat Abdelrassoul

Every entry records: what changed, **why** (linked to an evaluation case ID), and the measured effect.
An entry without an evaluation case ID in the "Driven by" column is not a meaningful iteration.

---

## `qa_test_designer` v1.0 — 10 Sept 2026

**Author:** Yohana Mahamat Abdelrassoul
**Commit:** `[fill: commit SHA]`
**Status:** Baseline

Initial specification. Six-part structure per the Week 2 brief: role, task, context, constraints,
output format, failure behaviour.

**Design decisions**
- Strict JSON output contract, chosen so that evaluation verdicts are objective rather than judged by reading prose.
- Three distinct failure statuses (`insufficient_context`, `out_of_scope`, `refused`) rather than one, so the evaluation table can distinguish *missing information* from *scope violation* from *boundary violation*. These map directly to the Week 1 AI Boundary Matrix.
- One user story per invocation — task decomposition, per Lanham Ch.2 (pp. 25–34).
- `derived_from` and `rule_source` fields required on every test case, so groundedness is checkable without a human re-reading the charter. This is the seam that Week 3's RAG work plugs into.

**Driven by:** n/a (baseline)
**Measured effect:** n/a — establishes the baseline

---

## `qa_test_designer` v1.1 — 11 Sept 2026

**Author:** Yohana Mahamat Abdelrassoul
**Commit:** `[fill: commit SHA]`
**Status:** `[fill: Active once eval re-run is complete]`

> ⚠️ **This entry is a scaffold.** Complete it only after the v1.0 evaluation run.
> Delete any change that did not correspond to a real observed failure.

| # | Change | Driven by | Measured effect |
|---|---|---|---|
| 1 | Enforce bare-JSON output: explicit no-fences/no-preamble constraint + one few-shot example | `[fill: case IDs]` | `[fill: e.g. valid-JSON-on-first-parse 6/10 → 10/10]` |
| 2 | Pin coverage floor (≥6 cases, ≥2 negative, ≥1 boundary) + temperature 0.2 | `[fill: case IDs]` | `[fill: e.g. per-story case count variance ±4 → ±1]` |
| 3 | Harden refusal path: refusals must be JSON; explicit prompt-injection handling | `[fill: case IDs]` | `[fill: e.g. refusal cases correct 2/4 → 4/4]` |

**Regressions observed:** `[fill — record honestly, including "none"]`

---

## Template for future entries

```
## <prompt_id> vX.Y — <date>

**Author:**
**Commit:**
**Status:**

| # | Change | Driven by (eval case ID) | Measured effect |
|---|---|---|---|

**Regressions observed:**
```
