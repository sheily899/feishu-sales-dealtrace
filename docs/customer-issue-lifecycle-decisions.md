# Customer issue lifecycle decisions

## Status

Accepted.

## Context

The original customer-state extractor asked the model for both a complete
snapshot and a delta. A syntactically valid response could retain an issue in
the snapshot while resolving it in the delta. Cross-round correlation also
fell back to mutable natural-language titles, which made renamed issues fragile
and made two same-category business objects easy to conflate.

## Decision

The application owns one canonical `CustomerIssue` list. Each issue contains:

- application-assigned stable `issue_id`;
- category and model-proposed `business_object`;
- current `open|resolved` status;
- current title/detail;
- append-only evidence history;
- creation and last-update message IDs;
- source creation/update timestamps when the event supplies them.

The model proposes only `create`, `update`, `resolve`, and `reopen` operations.
Application code validates evidence against the current message batch and
validates update/resolve/reopen against the exact historical ID, category,
business object, and old status. It then derives the final state and legacy UI
collections. A create ID is deterministic from category, first evidence message
ID, and per-message ordinal; no product name or case-specific keyword is part of
the algorithm.

Legacy `{state, change}` responses remain readable during migration. The
adapter ignores the duplicated state snapshot and converts only `change` into
operations. A missing legacy ID may use exact normalized-title lookup only when
there is exactly one historical candidate. Ambiguous matches are rejected.

## Alternatives considered

- Keep snapshot and delta and define precedence: rejected because it preserves
  two competing fact sources and requires conflict rules for every field.
- Correlate with fuzzy titles: rejected because thresholds can join different
  objects or lose the same object after a legitimate rename.
- Add product-specific keyword rules: rejected because they do not generalize
  across commercial, technical, contract, and implementation matters.

## Compatibility consequences

- `CustomerState.issues` and `StateChange.operations` are additive fields.
- Existing collection fields remain as deterministic projections for the
  workbench, persistence layer, and legacy evaluator.
- Previously persisted snapshots without `issues` are migrated in memory to
  deterministic `legacy:*` IDs. New state versions persist canonical issues.
- New prompts require operation-shaped output. Old captured responses can be
  replayed through the compatibility adapter, but old model mistakes are not
  repaired by business-specific inference in application code.
- Lifecycle v2 evaluation uses a separate sidecar and report. Legacy Golden,
  similarity threshold, and historical report remain unchanged.
