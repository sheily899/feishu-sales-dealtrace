# DealTrace | Feishu Sales Conversation Issue Tracker

DealTrace extracts customer needs, concerns, risks, follow-ups, and commitments from Feishu group chats, then preserves each issue’s status and source evidence across conversations.

## Demo

![DealTrace workbench](docs/assets/demo-workbench.png)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[llm]"
python -m dealtrace workbench --port 8765
```

Open <http://127.0.0.1:8765/>. The demo uses bundled anonymized messages; live analysis requires a working DeepSeek API key.

## Workflow

```text
Feishu chat → message and role normalization → issue extraction
            → historical linking → state merge and evidence checks
            → customer snapshot with source-message links
```

Unresolved issues are not removed merely because the next conversation changes topic. Unsupported state changes are rejected and the previous state is preserved.

## Features

- Normalize Feishu events and identify customer/sales roles;
- Extract needs, concerns, risks, stakeholders, commitments, todos, and next steps;
- Preserve unresolved issues across days;
- Support create, update, accepted-workaround, and resolved states;
- Link accepted changes to source messages;
- Save state versions, analysis output, and rejection reasons.

## Feishu integration

Copy `.env.example` to `.env`, configure Feishu credentials, chat allowlist, and role mapping, then run:

```bash
pip install -e ".[llm,feishu]"
python -m dealtrace workbench --feishu --port 8766
```

Live mode stores messages and state in `data/workbench.sqlite3`. It is a single-machine prototype without authentication, multi-tenancy, full CRM permissions, or automatic task dispatch.

## Evaluation

The evaluation set contains six sales scenarios, six cases, and 18 sequential rounds covering discovery, product demo, technical integration, pricing, post-signing implementation, and renewal handling.

Current internal evaluation (`deepseek-v4-flash`, seed 42, single run):

| Metric | Result | Meaning |
|---|---:|---|
| Change precision | 84.6% | Correct accepted changes among predictions |
| Change recall | 61.1% | Gold changes that were identified |
| State precision | 94.1% | Correct entries among saved state items |
| State recall | 66.7% | Gold state items that were saved |
| Evidence traceability | 100% | Accepted results linked to source messages |

These figures come from a small internal set and validate short-horizon multi-turn tracking, not months-long production conversations.

```bash
python evals/run_eval.py
```

## Layout

```text
src/dealtrace/     Core application, Feishu integration, LLM, and state logic
fixtures/          Anonymized local demo events
prompts/           Analysis prompts
schemas/           Output schemas
evals/             Golden cases and evaluators
tests/             Automated tests
```

## Privacy and security

Never commit `.env`, API keys, or real customer conversations. Add authentication, authorization, retention, and redaction controls before production use.

## License

Apache-2.0. See [LICENSE](LICENSE).
