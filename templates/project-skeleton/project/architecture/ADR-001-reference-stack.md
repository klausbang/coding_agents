---
id: ADR-001
title: Reference technology stack
status: accepted
date: 2026-10-08
---

# ADR-001 — Reference technology stack

## Context
The project is built by an AI agent team using the coding_agents kit. A known, boring and well-documented stack keeps the agents consistent and keeps the human's reviews cheap.

## Decision
| Concern | Choice |
|---|---|
| Language / framework | Python 3.12, Flask 3 (app factory + blueprints) |
| Database / ORM | PostgreSQL 16, SQLAlchemy 2 (typed models), Alembic via Flask-Migrate |
| API contract | OpenAPI 3.1 in `project/interfaces/openapi.yaml`; errors as RFC 9457 problem details |
| UI | Server-rendered Jinja2 + HTMX |
| Tests | pytest, Flask test client, factory-boy; schemathesis (contract); Playwright (E2E); pytest-bdd (acceptance); locust (load) |
| Quality / security | ruff, mypy, bandit, pip-audit, gitleaks, OWASP ZAP baseline |
| Runtime | Docker image (python:3.12-slim, non-root), gunicorn |
| CI/CD | GitHub Actions → GHCR → cloud container service; production deploy behind a manual approval |
| Infrastructure | Terraform (or Bicep on Azure), one stack per environment |

## Consequences
- Any deviation needs a new ADR approved at gate G2.
- The cloud provider is chosen in the vision constraints. The system-architect records the concrete services in `components.md`.
