---
applyTo: "project/**"
---

# Project state files

- `project/` is the team's shared memory: vision, backlog, architecture, interfaces, sprints, human decisions.
- New documents start from `templates/artifacts/` (US, EPIC, NFR, ADR, sprint, bug, review, validation report).
- Front matter `id:` must match the file name prefix (e.g. `US-014-password-reset.md` has `id: US-014`). Acceptance criteria are list items `- **AC-014.1** Given …, when …, then ….`
- Get a new ID by finding the highest existing number and adding one. Never reuse IDs.
- `project/hitl/` and `project/sprints/sprint-N.md` are maintained by the orchestrator only.
- After editing, `python tools/id_lint.py` must pass.
