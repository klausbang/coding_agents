# {{PROJECT_NAME}}

@.claude/orchestrator.md

## Project specifics
<!-- Project-owned. Keep it short: facts the orchestrator needs every session that are not in project/. -->
- Product vision: `project/vision.md`
- Reference stack and deviations: `project/architecture/ADR-001-reference-stack.md`
- Run locally: `docker compose up --build`, then open http://localhost:8000 (Mailpit UI: http://localhost:8025)
- Tests: `pytest tests/unit`; integration: set `TEST_DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/app_test`, then `pytest -m integration`
- Kit: agents and skills come from the coding_agents kit (`kit.json`). Use `/kit-sync` to pull updates or contribute improvements.
