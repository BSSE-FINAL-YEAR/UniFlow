# Approved UniFlow Rule Pack

Extracted verbatim from the Week 1 Project Charter §5 (Key Rules and Constraints).
Owner: Yohana Mahamat Abdelrassoul.

**Provenance matters.** Each rule is tagged as either *source-derived* (originating from the
team's supplied documentation) or *UniFlow Business Rule* (introduced by the team). The QA
Agent must preserve this tag in the `rule_source` field of every generated test case. This
is the groundwork for Week 3's source-grounding requirement.

---

## R-01 Student identity — *source-derived*
Registration numbers preserve the source format, e.g. `23/U/05288/PS` or `23/U/05288/EVE`.
The student number is derived from the registration number (e.g. `2305288`) and is unique
regardless of the PS/EVE suffix.

## R-02 Study mode — *source-derived*
`PS` means Day; `EVE` means Evening. Only programme/year combinations defined for the
UniFlow colleges and programmes are supported.

## R-03 Programme structure — *source-derived*
CEAD programmes are four-year programmes. CoCIS includes BSc Software Engineering (4 years),
BSc Computer Science (3 years) and BSc Information Systems Technology (3 years).

## R-04 Course load — *UniFlow Business Rule*
Maximum course load is 6 units in Year 1, 6 in Year 2, 5 in Year 3 and 4 in Year 4.

## R-05 Teaching windows — *UniFlow Business Rule*
Day classes: 08:00–16:00. Evening classes: 16:30–20:30.

## R-06 Course frequency — *UniFlow Business Rule*
Each course in a programme must be taught at least once and at most twice per week,
regardless of year.

## R-07 Registration — *source-derived*
Students must satisfy applicable enrollment, eligibility, prerequisite, duplicate-registration,
course-load and timetable checks before course registration is accepted.

## R-08 Assessment / academic context — *source-derived*
The simulated system reflects only academic-management rules relevant to the three selected
workflows. Unrelated institutional processes are excluded.

---

## Scope exclusions (Week 1 Charter )

The following are **outside** the approved scope. Requests concerning them must return
`status: "out_of_scope"`:

- Real student accounts, real institutional databases, real financial transactions
- Admissions
- Examinations and grading
- Discipline
- Elections, library processes
- Autonomous production deployment
- Autonomous source-code modification

**Retake management** is explicitly deferred to a later requirements iteration and is
therefore **not** in this rule pack. Requests concerning retakes must return
`status: "insufficient_context"`.

---

## Prohibited agent actions (Week 1 AI Boundary Matrix)

Requests asking the agent to do any of the following must return `status: "refused"`:

- Modify source code autonomously
- Modify academic records
- Delete data or files
- Access production systems
- Access credentials, `.env` files or secrets
- Execute arbitrary shell or system commands
- Deploy or merge changes
- Make academic or financial decisions
