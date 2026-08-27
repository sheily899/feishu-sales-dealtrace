# Contributing to GTM Superintelligence

Thanks for helping make open sales coaching better. Contributions of **adapters**,
**frameworks**, **scorecards**, language support, and docs are all welcome.

## Ground rules

- **Keep it vendor-neutral.** No proprietary playbooks, no company-internal scorecards,
  no real customer transcripts. Examples must be synthetic. Frameworks must be neutral
  paraphrases of public methodologies with attribution in `origin` / `further_reading`.
- **Everything stays forkable.** Coaching content lives in editable YAML, not in code.
- **Evidence-bound coaching.** Changes that make the coach less grounded (more vibes,
  fewer quotes) won't be merged.

## Dev setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Before every PR:

```bash
ruff check .                          # lint
python -m dealtrace validate          # knowledge-base integrity (cross-refs)
python .github/scripts/validate_schemas.py   # YAML conforms to JSON Schemas
pytest -q                             # unit tests
```

CI runs all of the above on 3.10–3.12.

## Adding a scorecard

1. Copy an existing file in `scorecards/` (e.g. `discovery.yaml`).
2. Set a unique `id`, `name`, `version`, `applies_to` (call-type ids), and the
   `frameworks` it draws on.
3. Write 6–9 criteria. Each needs `what_great_looks_like` and a `weight`;
   `framework_refs` must be `framework_id.element_id` for real elements.
4. Wire it into a call type in `config/call_types.yaml` (`scorecards: [...]`).
5. `python -m dealtrace validate` until clean. Full guide:
   [docs/writing-a-scorecard.md](./docs/writing-a-scorecard.md).

## Adding a framework

1. New file in `frameworks/` conforming to `schemas/framework.schema.json` (see
   `spiced.yaml` as the template).
2. Neutral paraphrase + attribution. Real `further_reading` link.
3. Reference its elements from scorecard `framework_refs`.

## Adding an adapter (new recorder)

1. New module in `src/dealtrace/adapters/` with a class exposing `name`, `sniff()`,
   and `parse() -> Transcript`. Keep it dependency-free. See
   [docs/adapters.md](./docs/adapters.md) for a skeleton.
2. Register it in `src/dealtrace/adapters/__init__.py` (order matters: specific before
   generic).
3. Add a test in `tests/test_adapters.py` with a small synthetic sample.

## Improving prompts / coaching quality

Prompts live in `prompts/` and are shared by the Python pipeline and the Claude skill.
If you change scoring behavior, add/extend a case in `evals/` and report the before/
after accuracy in your PR.

## Commit & PR

- Small, focused PRs. Describe the *why*.
- Run the checks above; green CI is required.
- Be kind in review. See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).
