---
doc_id: KB-SEED-NOTE
title: Synthetic seed dataset note
provenance: team-created
status: approved
workflow: all
---
UniFlow's test data (students, courses, rooms, lecturers) is entirely
synthetic and team-created — no real student records. It exists to give
the QA Agent and the deterministic backend concrete records to reason
about: five synthetic students across BSSE and BSCS (including one Evening
student in the one combination that supports it, BSCS Year 3), five BSSE courses
(BSE1101 through BSE4105) with a linear prerequisite chain, four rooms and
three lecturer identifiers. See data/seed.json in the repository for the
current values; this note documents its purpose, not its exact contents,
since seed.json can change independently of this rule pack.
