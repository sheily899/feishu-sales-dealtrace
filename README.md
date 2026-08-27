# DealTrace | Feishu Sales Conversation Issue Tracker

[中文说明](README.zh-CN.md)

DealTrace extracts customer needs, concerns, risks, follow-ups, and commitments from Feishu group chats, then preserves each issue’s status and source evidence across conversations.

## Demo

> **[Try the offline demo](https://sheily899.github.io/feishu-sales-dealtrace/)** — opens directly in the browser; no setup or API key required.

![DealTrace workbench](docs/assets/demo-workbench.png)

![DealTrace workbench overview](docs/assets/demo-workbench-overview.png)

The public demo uses ten bundled anonymized sales messages and a precomputed report. It never calls a model and does not consume API quota.

Demo path: open the public link → inspect issues, state, and source evidence.

## Workflow

```text
Feishu chat → message and role normalization → issue extraction
            → historical linking → state merge and evidence checks
            → customer snapshot with source-message links
```

Unresolved issues are not removed merely because the next conversation changes topic. Unsupported state changes are rejected and the previous state is preserved.

Internal collaboration and data flow:

```mermaid
flowchart LR
    A[New Feishu message] --> B[Message normalization and role filtering\nworkbench.py]
    B --> C[Analysis agent\npipeline.py + llm.py]
    C --> D[Issue and change parsing\ncustomer_state.py]
    D --> E[Historical issue linking\nissue_id]
    E --> F[State merge and evidence checks\ncustomer_state.py]
    F --> G[Persist state snapshot and changes\nworkbench_store.py]
    G --> H[Workbench UI and source navigation\nworkbench.py]
    H -. wait for next messages .-> A
```

| Module | Responsibility |
|---|---|
| Feishu event listener | Receives group messages and triggers a new processing cycle |
| Message normalization and role filtering | Standardizes time, text, and customer/sales roles |
| Analysis agent | Extracts needs, concerns, risks, todos, commitments, and next steps |
| Issue and change parsing | Converts model output into structured issue operations |
| Historical issue linking | Links cross-round issues using existing issue IDs and evidence |
| State merge and evidence checks | Merges old and new state and rejects unsupported changes |
| State storage | Saves versions, changes, and rejection reasons |
| Workbench UI | Shows customer state and navigates to source messages |

The model proposes analysis results; the state module validates and persists the canonical state. The next message batch reads the previous snapshot and starts the cycle again.

## Features

- Normalize Feishu events and identify customer/sales roles;
- Extract needs, concerns, risks, stakeholders, commitments, todos, and next steps;
- Preserve unresolved issues across days;
- Support create, update, accepted-workaround, and resolved states;
- Link accepted changes to source messages;
- Save state versions, analysis output, and rejection reasons.

## Feishu integration

Live Feishu mode requires the Feishu connector and LLM client dependencies. The public offline demo needs neither.

Live mode stores messages and state in `data/workbench.sqlite3`. It is a single-machine prototype without authentication, multi-tenancy, full CRM permissions, or automatic task dispatch.

### Feishu setup

1. Open the [Feishu Open Platform](https://open.feishu.cn/app) and sign in as an enterprise administrator.
2. Create an enterprise app. Copy its `App ID` and `App Secret` from the app details page.
3. Enable the group-message read/receive permissions and group-message event subscription, then publish a testable app version.
4. Add the app to a dedicated test group and note its group ID (usually starts with `oc_`).
5. Copy `.env.example` to `.env` and fill in:
   - `FEISHU_APP_ID` and `FEISHU_APP_SECRET` from the app details;
   - `FEISHU_GROUP_ALLOWLIST` with one or more comma-separated group IDs;
   - `FEISHU_ROLE_MAP` to map group members to customer or sales roles;
   - `DEEPSEEK_API_KEY` only for live analysis; the Offline demo never reads it.
6. In PowerShell at the project root, verify Python 3.10 or newer:
   ```powershell
   python --version
   ```
7. (Recommended) Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
8. Install the base package, DeepSeek clients, and Feishu connector:
   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -e ".[llm,feishu]"
   ```
9. Copy `.env.example` to `.env` and fill in `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_GROUP_ALLOWLIST`, `FEISHU_ROLE_MAP`, and `DEEPSEEK_API_KEY`.
10. Start live mode:
   ```powershell
   python -m dealtrace workbench --feishu --port 8766
   ```
11. Open <http://127.0.0.1:8766/>, send a message in the test group, and click **Generate analysis**.

Troubleshooting: an empty chat list usually means the group ID is not allowlisted; a missing report usually means the model key or network is unavailable. Use the port-8765 Offline demo when you only want to explore the UI.

Keep all secrets in the local `.env`; never commit them.

## Evaluation

The evaluation set contains six sales scenarios, six cases, and 18 sequential rounds covering discovery, product demo, technical integration, pricing, post-signing implementation, and renewal handling.

Current internal evaluation (`deepseek-v4-flash`, seed 42, single run):

| Metric | Result | Meaning |
|---|---:|---|
| Change precision | 84.6% | How often each recorded addition or resolution matches the conversation |
| Change recall | 61.1% | How many real changes in the conversation were captured in time |
| State precision | 94.1% | How many items kept in the customer record are supported by chat evidence |
| State recall | 66.7% | How many items that should be kept in the customer record were retained |
| Evidence traceability | 100% | Whether every analysis result links back to its source message |

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

## Future improvements

- Expand the evaluation set with real, multi-industry conversations over longer sales cycles;
- Add item-level review and edit history so sales teams can correct analyses quickly;
- Add access control, sensitive-data redaction, and retention policies before wider deployment;
- Reduce model cost and latency while keeping every result traceable to source messages.

## Privacy and security

Never commit `.env`, API keys, or real customer conversations. Add authentication, authorization, retention, and redaction controls before production use.

## License

Apache-2.0. See [LICENSE](LICENSE).
