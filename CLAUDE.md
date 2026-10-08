# coding_agents kit: development instructions

This repository **is the kit itself**, not a product project. It holds reusable agents, skills, hooks, tools and templates for Agile V-model development of Flask + PostgreSQL web apps. (In a product project this file is replaced by `templates/project-skeleton/CLAUDE.md`, which imports `.claude/orchestrator.md`.)

When working here:
- Keep everything product-agnostic. Use placeholders like `<persona>` and `US-NNN`, never real product names.
- Agent sources are in `.claude/agents/*.md`, `.claude/orchestrator.md` and `.claude/skills/*/SKILL.md`. After editing any of them, run `python tools/build_copilot.py`.
- If file ownership changes, keep `tools/agent_roles.json` and the agent's *May write* section consistent.
- Tools are stdlib-only Python 3.12+. Check them with `python -m py_compile tools/*.py .claude/hooks/*.py`.
- To test `kit.py` end to end, clone this repo to a temp folder and run `init`, `status`, `pull` and `push` there, using `KIT_UPSTREAM=<path to a bare clone>` so the real upstream is never touched.
- Bump `version` in `kit.json` and add an entry to `docs/kit/CHANGELOG.md` for every behaviour change.
- The overview page `docs/kit/agent-setup.html` should match the agents. Update it when roles change.
