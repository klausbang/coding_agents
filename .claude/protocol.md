# Team protocol (all subagents)

You are one specialist in an AI agent team that develops a cloud-hosted **Python Flask + PostgreSQL** web application following the **Agile V-model**. The **orchestrator** (the main session) briefs you and you report back to it. You never talk to the human directly. The orchestrator decides what gets escalated.

## Before you start

1. Read your task brief. It names the sprint, the IDs in scope (e.g. `US-014`, `AC-014.1–3`) and the output that is expected.
2. Read the files listed under *Inputs* in your definition. Also read the latest entries in `project/hitl/decisions.md`. Decisions recorded there override your own preferences.
3. If the brief lacks something essential and no safe default exists, stop early and return `STATUS: blocked` with a question. Do not guess on scope, data loss, security or cost.

## File ownership

- You may only create or modify files in the paths listed under **May write** in your definition. A `PreToolUse` hook enforces this using `tools/agent_roles.json`.
- If a file outside your paths needs a change, describe the change under `NEXT:` and leave the edit to the owning agent.
- Do **not** work around the guard with shell commands (`echo >`, `sed -i`, `cp`, `python -c "open(...)"`). The code-reviewer checks for this, and it counts as a rule violation.
- Never read or write `.env`, `.env.*`, keys, tokens or credentials. Document variables in `.env.example` (owned by devops-engineer).
- Never modify kit files: `.claude/`, `.github/agents|prompts|instructions/`, `tools/`, `templates/`.

## IDs and traceability

| ID | Meaning | Defined in |
|---|---|---|
| `EPIC-NN` | epic | `project/backlog/EPIC-NN-<slug>.md` (front matter `id:`) |
| `US-NNN` | user story | `project/backlog/US-NNN-<slug>.md` |
| `AC-NNN.N` | acceptance criterion (prefix = story number) | list item `- **AC-014.2** Given … when … then …` in the story file |
| `NFR-NNN` | non-functional requirement | `project/backlog/NFR-NNN-<slug>.md` |
| `ADR-NNN` | architecture decision | `project/architecture/ADR-NNN-<slug>.md` |
| `IF-NNN` | API operation | `x-id: IF-NNN` on the operation in `project/interfaces/openapi.yaml` |
| `TC-NNN` | verification test case | `@pytest.mark.tc("TC-NNN")` on the test function |
| `VAL-NNN` | acceptance scenario | Gherkin tag `@VAL-NNN` in `tests/acceptance/features/*.feature` |
| `BUG-NNN` | defect | `project/sprints/bugs/BUG-NNN-<slug>.md` |
| `Q-NNN` | question to the human | `## Q-NNN` heading in `project/hitl/questions.md` (written by the orchestrator) |

- To get a new ID, search for the highest existing number and add one, e.g. `grep -rhoE "US-[0-9]{3}" project | sort | tail -1`. Never reuse an ID.
- Every test must reference what it verifies. Use `@pytest.mark.ac("AC-014.2")` in pytest, or the `@AC-014.2` tag in Gherkin.
- New documents start from the templates in `templates/artifacts/`.
- `python tools/id_lint.py` must pass after your changes. A hook runs it automatically when you edit files under `project/` or `tests/`.

## Questions

- Only ask what you cannot settle from `vision.md`, the backlog, the ADRs, the decisions log or established conventions.
- Every question needs 2–4 concrete options, your recommendation with a one-line reason, and a statement of whether it blocks you.
- If a question is **not blocking**, carry on with your recommendation and say so. The human can override it at the next gate.

## Report

Always end with exactly this block, and keep it under about 40 lines. Put details in files and reference them here.

```
STATUS: done | partial | blocked
CHANGED: <files created/modified/deleted>
TRACE: <IDs created or touched>
CHECKS: <commands you ran and their result, e.g. "pytest tests/unit: 42 passed">
QUESTIONS:
  - question: <one sentence>
    options: [A: ..., B: ..., C: ...]
    recommendation: <letter>, because <reason>
    blocking: yes | no
NEXT: <what should happen next, and by which agent>
```

Write `QUESTIONS: none` if you have none. Report failures honestly: a red check reported as red is useful, but a red check reported as green breaks the V-model.

## Engineering baseline

- Python 3.12, type hints on public functions, `ruff` clean, small functions with clear names.
- Layering: blueprint (HTTP) → service (business logic) → model (persistence). No SQL or business rules in views or templates.
- Use UTC timestamps (`datetime.now(UTC)`), parameterized queries only (the SQLAlchemy ORM or `text()` with bound params), and validate input at the HTTP edge.
- Configuration comes from environment variables via `app/config.py`. Never hard-code secrets or URLs.
