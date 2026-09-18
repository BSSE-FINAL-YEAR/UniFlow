---
doc_id: KB-REGISTRAR-FAQ
title: Registrar FAQ notes (informal)
provenance: team-created
status: approved
workflow: all
---
## Why does the derived student number ignore PS/EVE?

Because the registration number's PS/EVE suffix only records study mode,
not identity. Two records that would otherwise collide on the same
underlying student number are treated as duplicates regardless of suffix
— this is the mechanism behind R-01 and is exactly what US-03 tests.

## Why is the 16:00-16:30 gap between Day and Evening not a valid window?

Day classes are defined to end at 16:00 and Evening classes are defined to
start at 16:30 (R-05). The half hour between them is reserved for
transition and is not an assignable teaching slot for either mode; a
timetable entry proposing a class inside that gap has no valid window to
belong to and should be rejected by the timetable-generation workflow
described in US-10, the same way an entry outside 08:00-20:30 entirely
would be.

## Are all programme/year/mode combinations from the programme reference
data automatically supported?

No. R-02 states that only "defined" programme/year combinations are
supported, but this knowledge base does not enumerate that table anywhere
— KB-PROGRAMMES only lists which modes each programme supports overall,
not a year-by-year combination table. Do not infer or invent a specific
combination table from the programme list; flag the gap instead.
