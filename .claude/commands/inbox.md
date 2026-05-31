---
description: Build a prioritized "what to improve" coaching inbox for a rep, team, or company.
argument-hint: <folder-of-reports-or-transcripts> [--scope rep|team|company] [name]
---

Build a coaching inbox using the **inbox-builder** subagent.

Target / scope / name: $ARGUMENTS

Steps:
1. Collect coaching reports (coach transcripts first if needed). For team/company,
   group by rep (e.g. one subfolder per rep).
2. Aggregate weaknesses by theme, ranked by frequency x impact; surface wins.
3. Output the inbox:
   - **Rep**: 3-6 focus areas, each with a concrete drill / better move, plus wins.
   - **Team/Company**: top systemic themes, affected reps, a per-member table, and one
     or two patterns worth a team session.

Action-first — what to do tomorrow, not a data dump. Offer JSON (per
`schemas/inbox.schema.json`) on request. Default scope is `rep`. If $ARGUMENTS is
empty, ask for the folder and scope.
