# {{PROJECT_NAME}}

A Flask + PostgreSQL web application, developed with the coding_agents Agile V-model agent team.

## Quick start

```bash
cp .env.example .env            # adjust values
docker compose up --build       # app on http://localhost:8000, mail UI on http://localhost:8025
```

Without Docker:

```bash
python -m venv .venv && . .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
flask --app wsgi db upgrade                       # needs DATABASE_URL pointing at PostgreSQL
flask --app wsgi run --debug
```

## Tests

```bash
pytest tests/unit                                 # fast, no database needed
TEST_DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/app_test pytest -m integration
python tools/id_lint.py && python tools/trace_check.py
```

## How this project is developed

Open the folder in Claude Code and use:

| Command | What it does |
|---|---|
| `/sprint-start <goal>` | Plan a v-sprint: stories, acceptance criteria, gate G1 |
| `/sprint-status` | Show where things stand and what is waiting for you |
| `/gate G1..G4` | Run a human approval gate |
| `/trace` | Check traceability from stories to tests |
| `/release` | Run gate G4 and the production deploy |
| `/kit-sync status, pull or push` | Sync the agent kit with the shared coding_agents repo |

The project state (vision, backlog, architecture, sprints, decisions) lives in `project/`. The agent team is described in `docs/kit/agent-setup.html`.
