# UniFlow — Corpus / Source Register

The canonical register is [`corpus_source_register.csv`](corpus_source_register.csv)
— one row per retrievable document in `knowledge/`. This file explains the
columns and the governance rule that keeps it honest.

## Why a register, not just a folder of files

A folder of markdown files has no provenance by itself. The register is what
lets every retrieved chunk be traced back to *where it came from* and *whether
it was ever approved* — which is the whole point of Week 3's "controlled,
traceable knowledge source" requirement.

`src/rag/ingest.py` enforces this at load time, the same "two files, always
both" discipline Week 2 used for the rule pack (`RUNBOOK.md` step 2):

- A file in `knowledge/` whose `doc_id` is not in the register **fails to
  load** — it cannot silently enter the index.
- A register row with no matching file **fails to load** — the register
  can't claim provenance for content that doesn't exist.

## Columns

| Column | Meaning |
|---|---|
| `doc_id` | Stable identifier, also present in the file's frontmatter. Used as the citation unit — this is what the model must name in its `sources` field. |
| `title` | Human-readable name. |
| `source_type` | `internal` (from this project's own approved artifacts) or `internal (synthetic)` (authored for Week 3 to stress the pipeline). No external real-world documents were used — see the note below. |
| `origin` | Where the content was pulled from (a Week 1 artifact, a Week 2 file, or "authored for Week 3"). |
| `provenance` | Carried over from Week 2's `uniflow_rules.md` convention: `source-derived`, `UniFlow Business Rule`, `approved-requirement`, `team-created`, or a draft/unapproved variant of the business-rule tag. |
| `status` | `approved` or `draft-unapproved`. This is the field that matters most for grounding: draft-unapproved content is deliberately kept **in** the index (not filtered out), so the pipeline's generation step — not the retriever — is what has to catch it and avoid presenting it as an approved rule. |
| `workflow` | Which of the three UniFlow workflows the document relates to, or `all`. |
| `rules_or_stories_covered` | Cross-reference to R-xx / US-xx IDs, for auditability against the Week 1 charter and Week 2 rule pack. |
| `date_added` | When the row entered the register. |
| `notes` | Anything a reader needs to interpret the row — in particular, flags the rows that were deliberately designed as retrieval/grounding traps. |

## Why no external documents

The Week 1 Charter and Architecture Description both specify that UniFlow's
knowledge base is built from *"approved requirements, business rules, [and]
project documentation"* (see `04_Initial_Architecture_Description GROUP I.docx`
§3) and that data is *"synthetic, team-created, public, or otherwise
authorized"* (Charter §7). No real external institutional document was ever
named as a source for the "source-derived" rules — that tag distinguishes
rules the team was given at the start of the project from rules the team
introduced itself. The Week 3 corpus formalizes exactly that existing
material into discrete, retrievable, individually-provenanced records rather
than importing outside content.

## Deliberate traps in this corpus

Four rows exist specifically to produce findable retrieval/grounding
failures (Week 3 activity 5), not just to pad the count:

- `KB-RETAKE-DRAFT`, `KB-WAIVER-MEMO` — plausible-sounding but explicitly
  unapproved content, to test whether generation launders a draft into a
  confident, authoritative-sounding answer.
- `KB-REGISTRAR-FAQ` — long enough to be split across multiple chunks by
  `src/rag/chunk.py`'s fixed-size window, to test whether chunking damages
  an answer that needs the full entry.
- `KB-CALENDAR-NOTE` — a topically-adjacent distractor for questions about
  `US-05` enrollment timing, to test whether the retriever surfaces the
  wrong-but-similar document over the right one.

## Corpus changelog

**2026-09-23 — added the second college and resolved the R-02 combination gap.**
The Week 1 Charter only ever detailed CoCIS; the College of Engineering, Art
and Design (CEAD) and its four programmes were missing from `data/seed.json`
and the corpus. Also added: `KB-R02-COMBINATIONS`, a new UniFlow Business
Rule enumerating exactly which programme/year pairs support Evening study
(BSSE Year 4, BSCS Year 3 — everything else, including all of CEAD and
BIST, is Day-only). This was a genuine gap in Week 1-3's supplied scope,
not a correction of an error, and is documented here rather than edited
into the Week 1 Charter retroactively.

Consequences, recorded rather than hidden: `KB-PROGRAMMES`, `KB-R02`,
`KB-R03`, `KB-US04` and `KB-REGISTRAR-FAQ` were updated to point at or
incorporate the new rule; synthetic Student C was reassigned from BIST to
BSCS (Year 3) because her original record became an invalid combination
under the new rule; and `eval/rag_eval_cases.json`'s `RQ-07` was
reclassified from "Partially answerable" to "Answerable" since the gap it
tested no longer exists. `eval/rag_results_v1.0.csv` and
`docs/Week3_Failures.md` are left as-is — they are the historical record of
a run against the pre-2026-09-23 corpus, not a live document.
