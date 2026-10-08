# coding_agents kit — changelog

## 0.1.0 — 2026-10-08
- First release.
- Orchestrator plus 11 subagents: requirements-engineer, system-architect, database-engineer, security-engineer, backend-developer, frontend-developer, code-reviewer, verification-engineer, validation-engineer, devops-engineer, docs-writer.
- Shared protocol: traceability IDs, file ownership, report block, question rules.
- Skills: sprint-start, sprint-status, gate, trace, release, kit-init, kit-sync.
- Hooks: write_guard (enforces file ownership), id_lint (post-edit ID check).
- Tools: kit.py (init/status/pull/push), id_lint, trace_check, status_report, build_copilot.
- Templates: artifact templates, and a Flask + PostgreSQL project skeleton with CI, Docker and deploy scaffolding.
- Copilot custom agents and prompt files generated from the Claude sources.
