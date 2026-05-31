---
description: Coach every transcript in a folder and produce a ranked summary table.
argument-hint: <directory> [optional focus, e.g. "only discovery calls"]
---

Batch-coach a folder of call transcripts using the **sales-coach** skill.

Target directory (and any focus): $ARGUMENTS

Steps:
1. List the transcript files in the directory (`.txt`, `.vtt`, `.srt`, `.json`, `.md`).
   If a focus is given (e.g. "only renewals"), classify first and filter to it.
2. For each transcript, run the full pipeline: classify → infer outcomes → score →
   coach. Write a Markdown report per call (you may save to `<dir>/coaching/<name>.md`
   if the user wants files, otherwise summarize inline).
3. End with a ranked table:

   | File | Call type | Overall | Top fix |
   |------|-----------|--------:|---------|

   sorted by overall ascending (worst first, so the user sees where coaching helps
   most). Add one or two cross-call patterns you notice (e.g. "next steps are the
   common weak point").

Rules: never invent quotes; calibrate honestly; coach the rep. For large folders,
process in batches and tell the user how many you covered.

If $ARGUMENTS is empty, ask for a directory path.
