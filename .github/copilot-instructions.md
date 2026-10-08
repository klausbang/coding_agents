# Copilot instructions (coding_agents kit)

This repository is developed by an **Agile V-model agent team**. The team's definitions live in `.claude/`, and the Copilot custom agents in `.github/agents/` are generated from them. Pick the **orchestrator** agent to run a sprint, or a specialist agent for a focused task.

## Always
- Read `project/vision.md` and the relevant stories in `project/backlog/` before you change behaviour.
- Use the traceability IDs from `.claude/protocol.md`: US-NNN, AC-NNN.N, IF-NNN, TC-NNN, VAL-NNN, BUG-NNN, ADR-NNN, NFR-NNN. Tests reference the AC they verify with `@pytest.mark.ac("…")`, or with a Gherkin tag.
- Respect file ownership (`tools/agent_roles.json`). When working as a specialist agent, only change files that role owns. Copilot has no hooks to enforce this, so CI checks the IDs and the traceability instead.
- Never change `project/interfaces/openapi.yaml` while implementing. The contract belongs to the system-architect.
- The human approves at four gates: G1 scope, G2 design, G3 V&V review, G4 release. Never deploy to production without G4.
- Never read or write `.env` files or secrets.

## Stack conventions
- Python 3.12, Flask app factory (`app/__init__.py`), blueprints → services → models.
- SQLAlchemy 2 typed models. The schema only changes through Alembic migrations (`flask db migrate`), each with upgrade and downgrade.
- pytest. Unit tests run without a database (SQLite in memory). Integration tests need `TEST_DATABASE_URL` (PostgreSQL).
- `ruff`, `mypy` and `bandit` must be clean. `python tools/id_lint.py` and `python tools/trace_check.py` must pass.

## Kit maintenance
Edit agents in `.claude/agents/*.md` and skills in `.claude/skills/*/SKILL.md`, then run `python tools/build_copilot.py`. Never edit `.github/agents/*` or `.github/prompts/*` by hand.
