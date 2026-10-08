# Implementation Plan — Agile V-Model AI Agent Team for Flask Web Applications

A generic, reusable agent setup for developing **cloud-hosted Python Flask web applications with a relational database**. It is designed to run in **Claude Code** first and to be ported to **VS Code + GitHub Copilot** afterwards. No physical hardware is involved, so every verification and validation step runs in software: locally, in CI and in a cloud staging environment.

> The visual overview is in **`agent-setup.html`**. It covers the V-model with the agents at each level, what each agent does, how the agents interact, and the sprint flow.

---

## 1. Design principles

| # | Principle | Consequence |
|---|---|---|
| 1 | **Claude Code subagents cannot start other subagents.** | The main session acts as the **Orchestrator**. All specialist agents are subagents, one level down, so the hierarchy is flat. The V-model levels describe *when* an agent works, not who reports to whom. |
| 2 | **Only the main session talks to the human.** | Subagents return questions in a fixed `QUESTIONS:` block. The Orchestrator asks the human with `AskUserQuestion` at defined gates and logs every answer in `project/hitl/`. |
| 3 | **Memory lives in files, not in agents.** | `project/` holds the backlog, architecture, contracts, decision log and traceability. Every agent reads these files first and writes back to them. No "knowledge manager" agent is needed. |
| 4 | **Independent verification.** | Tool restrictions per agent, plus `PreToolUse` hooks that guard which folders each agent may write to. Developers cannot edit `tests/integration`, `tests/system` or `tests/acceptance`. Testers cannot edit `app/`. |
| 5 | **Contracts are machine-checked.** | The OpenAPI spec, the database migrations, ID lint and the traceability check run in hooks and CI. A prompt alone is not trusted to enforce a rule. |
| 6 | **Product-agnostic.** | Nothing product-specific is hard-coded in agent prompts. The product lives only in `project/vision.md` and the backlog. |

---

## 2. Reference technology stack (adjustable)

| Concern | Default choice |
|---|---|
| Language / framework | Python 3.12, Flask (app factory + blueprints) |
| Database / ORM | PostgreSQL, SQLAlchemy 2.x, Alembic (Flask-Migrate) |
| API contract | OpenAPI 3.1 (`project/interfaces/openapi.yaml`) |
| UI | Jinja2 templates + HTMX (or a separate SPA, chosen at the architecture gate) |
| Auth | Flask-Login / OIDC provider |
| Unit / integration tests | pytest, Flask test client, testcontainers-postgres, factory-boy |
| Contract tests | schemathesis against the OpenAPI spec |
| System / E2E tests | Playwright (Python), locust for load |
| Acceptance tests | pytest-bdd (Gherkin), run against staging |
| Quality / security | ruff, mypy, bandit, pip-audit, OWASP ZAP baseline scan |
| Packaging / runtime | Docker, gunicorn |
| CI/CD | GitHub Actions → container registry → cloud (Azure App Service, AWS ECS/App Runner or GCP Cloud Run) |
| Infrastructure | Terraform or Bicep (one environment per stage: dev, staging, prod) |

---

## 3. V-model levels and agents

| Level | Left side (specification) | Agents | Right side (test) | Agents |
|---|---|---|---|---|
| 1 | Requirements analysis | requirements-engineer | Acceptance testing / UAT | validation-engineer |
| 2 | System architecture | system-architect | System testing (E2E, load, security) | verification-engineer, security-engineer |
| 3 | Component & data design | system-architect, database-engineer | Integration testing (API + DB, contracts) | verification-engineer |
| 4 | Module design (TDD specs) | backend-developer, frontend-developer | Unit testing | developers (run the tests); verification-engineer (audits them) |
| — | **Implementation** (bottom of the V) | backend-developer, frontend-developer, database-engineer, code-reviewer | | |
| ✱ | Cross-cutting, all levels | orchestrator, devops-engineer, docs-writer, security-engineer | | |

---

## 4. Agent catalogue

Each agent is a file `.claude/agents/<name>.md`. The frontmatter holds `name`, `description`, `tools` and `model`. The prompt below it has the sections **Role · Inputs · Outputs · Rules · Definition of Done · Report format**.

| Agent | Model | May write to | Main outputs |
|---|---|---|---|
| **orchestrator** (main session, `CLAUDE.md`) | Opus | `project/sprints`, `project/hitl` | Sprint plan, task briefs, gate requests, status summaries |
| requirements-engineer | Opus | `project/backlog` | Epics, user stories, acceptance criteria (Given/When/Then), NFRs |
| system-architect | Opus | `project/architecture`, `project/interfaces` | Component model, OpenAPI spec, ADRs, deployment topology, NFR budgets |
| database-engineer | Sonnet | `app/models`, `migrations`, `project/architecture/data` | ERD, SQLAlchemy models, Alembic migrations, seed data, index/query review |
| backend-developer | Sonnet | `app/` (not `app/templates`), `tests/unit` | Blueprints, services, validation, unit tests (TDD) |
| frontend-developer | Sonnet | `app/templates`, `app/static`, `tests/unit/ui` | Jinja/HTMX views or SPA, forms, accessibility, unit tests |
| code-reviewer | Sonnet (read-only) | `project/sprints/reviews` | Review findings per change: correctness, readability, layering |
| verification-engineer | Sonnet | `tests/integration`, `tests/system`, `tests/contract` | Test cases derived from acceptance criteria, coverage report, bug list |
| security-engineer | Sonnet | `tests/security`, `project/architecture/security` | Threat model (STRIDE), OWASP Top 10 checks, dependency audit |
| validation-engineer | Opus | `tests/acceptance`, `project/sprints` | Gherkin scenarios, UAT runs on staging, validation report |
| devops-engineer | Sonnet | `.github/workflows`, `infra/`, `Dockerfile`, `docker-compose.yml` | CI/CD pipeline, environments, secrets wiring, deployment |
| docs-writer | Haiku/Sonnet | `docs/`, `project/traceability.csv` | API reference, user/admin guides, changelog, traceability matrix |

**Standard report block**, returned by every subagent:

```
STATUS: done | partial | blocked
CHANGED: <files>
TRACE: <IDs touched, e.g. US-012, AC-012.3, IF-004, TC-031>
QUESTIONS:
  - id: Q-<n>
    question: ...
    options: [A: ..., B: ..., C: ...]
    recommendation: A, because ...
    blocking: yes/no
NEXT: <suggested next step>
```

---

## 5. Repository layout (template)

```
<product>/
├── CLAUDE.md                      # Orchestrator role, v-sprint process, gates, ID rules
├── .claude/
│   ├── agents/                    # 11 subagent definitions
│   ├── skills/                    # /sprint-start, /sprint-status, /gate, /trace, /release
│   └── settings.json              # hooks (write-guards, id-lint, notify) + permissions
├── .github/                       # Copilot port + CI
│   ├── copilot-instructions.md
│   ├── agents/*.agent.md
│   ├── prompts/*.prompt.md
│   ├── instructions/*.instructions.md
│   └── workflows/ci.yml, deploy.yml
├── project/
│   ├── vision.md                  # human-owned: problem, users, goals, constraints
│   ├── backlog/                   # EPIC-xx.md, US-xxx.md (with AC-xxx.y), NFR-xxx.md
│   ├── architecture/              # components.md, data/, security/, ADR-xxx.md
│   ├── interfaces/openapi.yaml
│   ├── sprints/                   # sprint-N.md (plan, status, reviews, retro)
│   ├── traceability.csv           # US ↔ AC ↔ IF ↔ module ↔ TC ↔ VAL
│   └── hitl/                      # questions.md, decisions.md, status.md
├── app/                           # Flask package: __init__ (factory), blueprints/, services/, models/, templates/, static/
├── migrations/                    # Alembic
├── tests/                         # unit/ integration/ contract/ system/ security/ acceptance/
├── infra/                         # Terraform / Bicep
├── docs/
├── tools/                         # id_lint.py, trace_check.py, status_report.py
├── Dockerfile, docker-compose.yml, pyproject.toml
```

---

## 6. One v-sprint

| Step | Agent(s) | Gate |
|---|---|---|
| 1. `/sprint-start <goal>`: read vision, backlog and the last retro, then draft `sprint-N.md` | orchestrator | — |
| 2. Stories, acceptance criteria, NFRs | requirements-engineer | **G1 Scope**: the human approves the stories |
| 3. Architecture deltas, OpenAPI changes, ADRs, data model | system-architect, database-engineer, security-engineer (threat model) | **G2 Design**: the human approves contract and schema changes |
| 4. Acceptance scenarios drafted *before* the code is written | validation-engineer | — |
| 5. TDD implementation, in parallel | backend-developer, frontend-developer, database-engineer | Blocking questions go to the human straight away (**Ask**) |
| 6. Code review | code-reviewer → developers fix findings | — |
| 7. CI: lint, type check, unit, integration (Postgres), contract | devops-engineer (pipeline), verification-engineer (tests) | Max 3 fix loops, then escalate |
| 8. Deploy to staging; E2E, load and security scan | devops-engineer, verification-engineer, security-engineer | — |
| 9. Acceptance testing on staging | validation-engineer | **G3 V&V review**: the human sees results and any backlog changes |
| 10. Docs, changelog, traceability (`trace_check` must pass) | docs-writer | — |
| 11. Release to prod | devops-engineer | **G4 Release sign-off**: the human approves the prod deploy |

---

## 7. Phased implementation

| Phase | Content | Done when | Effort |
|---|---|---|---|
| **0 Foundation** | Repo template, ID scheme, `project/` templates, `tools/id_lint.py`, `tools/trace_check.py`, a sample `vision.md` (a small demo app such as "team task tracker") | Templates exist; both tools run on sample data | 1–2 days |
| **1 Orchestrator + left side** | `CLAUDE.md`, requirements-engineer, system-architect, database-engineer; skills `/sprint-start`, `/gate`, `/sprint-status` | `/sprint-start` produces approved stories, an OpenAPI spec and an ERD, and passes G1 and G2 | 2–3 days |
| **2 Implementation** | backend-, frontend-developer, code-reviewer; Flask skeleton (factory, config, health endpoint, auth); docker-compose with Postgres | One story runs end to end locally, with its unit tests green and its review findings closed | 3–4 days |
| **3 Right side** | verification-, security-, validation-engineer; write-guard hooks; fix-loop cap | An injected bug is caught at the correct level; an ambiguous AC is caught at acceptance and goes back to the backlog | 3–4 days |
| **4 DevOps + docs** | devops-engineer, docs-writer; GitHub Actions; staging + prod infrastructure; secrets in the cloud key vault | CI/CD is green; the app is deployed to staging; `trace_check` shows 100% AC coverage | 3–4 days |
| **5 Pilot sprints** | 2 sprints on the demo app (e.g. "user registration + login", then "task CRUD with sharing") | Metrics recorded: questions per gate, fix loops, token cost, rule breaks; prompts tuned | 3–4 days |
| **6 Copilot port** | `.github/agents/*.agent.md` with `handoffs`, prompt files, `applyTo` instructions; CI-based path guards replace hooks | Sprint 3 runs in Copilot on the same `project/` artifacts | 2–3 days |
| **7 Template release** | Package as a repo template or `cookiecutter`; write "how to start a new product" | A new product is bootstrapped in under 30 minutes | 1 day |

**Total:** about 3–4 weeks of part-time work.

---

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Orchestrator context fills up | Subagents return short reports and the detail lives on disk; one session per sprint phase; `/sprint-status` rebuilds the context from files |
| Agents edit tests until they pass | Folder write-guards (hooks / CI path rules); tests are derived from the acceptance criteria, not from the code |
| Schema drift or destructive migrations | Only the database-engineer writes migrations; CI runs `alembic upgrade` and `downgrade` on a fresh Postgres; destructive changes need G2 approval |
| Secrets leak into the repo or prompts | `.env` is never read by agents (permission deny rule); secrets live in the cloud key vault and CI secrets; a gitleaks step runs in CI |
| Too many questions to the human | Every question must come with options and a recommendation; non-blocking questions are batched per gate; the question count is tracked |
| Cost | Opus only where judgment matters (orchestrator, requirements, architecture, validation); fix loops are capped |
| Prod deploys without a human | Prod deploy needs G4 plus a GitHub environment protection rule (manual approval) |

---

## 9. Open decisions

1. Primary tool: Claude Code first, then Copilot (recommended), or both from the start?
2. UI approach: server-rendered Jinja + HTMX (recommended for simplicity), or a separate SPA?
3. Cloud target: Azure, AWS or GCP?
4. Demo product for the pilot sprints, or a real product idea straight away?
