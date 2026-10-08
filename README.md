# coding_agents: Agile V-model AI agent team for Flask web apps

A reusable kit of **AI agents, skills, hooks, tools and templates** for developing cloud-hosted **Python Flask + PostgreSQL** web applications with **Claude Code** (primary) or **GitHub Copilot in VS Code**. The work follows the **Agile V-model**. Every left-side specification level has an independent right-side test level, and a human approves the work at four gates.

```
 L1 Requirements ─ requirements-engineer               validation-engineer ─ R1 Acceptance
   L2 Architecture ─ system-architect, security     verification, security ─ R2 System test
     L3 Component/data ─ system-architect, database    verification ─ R3 Integration
       L4 Module design ─ backend/frontend-dev    dev + verification audit ─ R4 Unit test
                    Implementation ─ backend, frontend, database, code-reviewer
          cross-cutting: orchestrator (main session) · devops-engineer · docs-writer
```

The full illustrated overview is in [`docs/kit/agent-setup.html`](docs/kit/agent-setup.html), and the rollout plan in [`docs/kit/PLAN.md`](docs/kit/PLAN.md).

---

## Start a new project

**Prerequisites:** Git, Python 3.12+, Claude Code (and/or VS Code with Copilot). Optional: Docker, the GitHub CLI `gh`.

```bash
git clone https://github.com/klausbang/coding_agents.git my-app
cd my-app
python tools/kit.py init --name "My App" --origin https://github.com/<you>/my-app.git
git push -u origin main
```

`init`:
- copies `templates/project-skeleton/` into the project: a Flask app skeleton, `project/` state files, CI, Docker, `CLAUDE.md` and `README.md`;
- renames the kit remote from `origin` to `kit` and records the kit version in `.kit/state.json`;
- makes the first commit.

Downloaded a zip, or used "Use this template" on GitHub? That works too. `init` connects the kit history so later updates merge cleanly.

Then open the folder in Claude Code:

```
/kit-init                 # interview → writes project/vision.md
/sprint-start "Sign-up and sign-in"
```

## Daily use (Claude Code)

| Command | Purpose |
|---|---|
| `/sprint-start <goal>` | Create the sprint, draft stories and AC, run gate **G1 Scope** |
| `/sprint-status` | Where are we, and what is waiting for the human? |
| `/gate G1\|G2\|G3\|G4` | Run a human approval gate and log the decision |
| `/trace [sprint]` | Traceability from stories → AC → interfaces → tests → acceptance scenarios |
| `/release` | Final checks, gate **G4**, production deploy, retro |
| `/kit-init` | Initialize a project and write the vision (once) |
| `/kit-sync status\|pull\|push` | Keep the kit in sync with this repository |

The main session acts as the **orchestrator**. It delegates to 11 subagents in `.claude/agents/`, and it is the only one that talks to you. Progress is written to `project/hitl/status.md`, questions to `project/hitl/questions.md`, and decisions to `project/hitl/decisions.md`.

## Using GitHub Copilot instead

The Copilot files are generated from the same sources:

| Copilot | Generated from |
|---|---|
| `.github/agents/*.agent.md` (custom agents with handoffs) | `.claude/agents/*.md`, `.claude/orchestrator.md` |
| `.github/prompts/*.prompt.md` (`/sprint-start` etc.) | `.claude/skills/*/SKILL.md` |
| `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md` | hand-written, kit-owned |

In VS Code Chat, select the **orchestrator** agent, or use a specialist agent and its handoff buttons. Copilot has no hooks, so file ownership is advisory there. CI still checks the IDs and the traceability.

## Keeping projects and the kit in sync

The files in `kit.json` → `kit_paths` belong to the **kit**: agents, skills, hooks, tools, templates, Copilot files and `docs/kit/`. Everything else belongs to the **project**.

```
coding_agents (this repo) ──clone + kit.py init──▶ my-app (own repo, remote "kit" = this repo)
        ▲                                                │
        └──── kit.py push (branch + PR) ◀─ improve agents in the project
        └──── kit.py pull (merge) ────────▶ get kit updates
```

| Task | Command |
|---|---|
| See the kit version, pending updates and local kit changes | `python tools/kit.py status` |
| Get the latest agents into a project | `python tools/kit.py pull` |
| Send agent improvements from a project back here | `python tools/kit.py push -m "what changed"`, which is a dry run; add `--yes` to open a PR (or `--direct` to push to main) |

`push` only ever sends kit paths. Product code, `project/` and the project's `README.md` and `CLAUDE.md` never leave the project. Merge the PR here, then `pull` in every project.

You can also improve the kit directly in this repository: edit, run `python tools/build_copilot.py`, commit and push.

## Repository layout

```
.claude/
  orchestrator.md        main-session role (imported by the project's CLAUDE.md)
  protocol.md            shared rules for all subagents: IDs, ownership, report block, questions
  agents/                11 subagents
  skills/                sprint-start, sprint-status, gate, trace, release, kit-init, kit-sync
  hooks/write_guard.py   blocks subagents from writing outside their own paths
  settings.json          hooks + permissions
.github/
  copilot-instructions.md, instructions/   Copilot guidance
  agents/, prompts/                        GENERATED by tools/build_copilot.py
  workflows/kit-check.yml                  kit self-check (runs in projects too)
tools/
  kit.py                 init / status / pull / push
  agent_roles.json       who may write where (used by write_guard)
  id_lint.py             ID format, duplicate and dangling-reference checks (also a hook)
  trace_check.py         traceability matrix → project/traceability.csv
  status_report.py       facts for /sprint-status
  build_copilot.py       Claude sources → Copilot agents and prompts
templates/
  artifacts/             US, EPIC, NFR, ADR, sprint, bug, review, validation report
  project-skeleton/      what `kit.py init` copies into a new project
docs/kit/                agent-setup.html, PLAN.md, CHANGELOG.md, origin-chat.md
```

## Kit development rules

1. Keep everything **product-agnostic**. Product facts belong in a project's `project/` folder, never in agent prompts.
2. Edit the sources in `.claude/`, then run `python tools/build_copilot.py`. CI fails if the generated files are stale.
3. If you change who owns which files, update both `tools/agent_roles.json` and the agent's *May write* section.
4. Bump `version` in `kit.json` and add an entry to `docs/kit/CHANGELOG.md`.

## Known limitations

- The write guard checks the Edit and Write tools. A subagent with Bash could still write files through the shell. The protocol forbids this and the code-reviewer checks for it, but nothing technically prevents it.
- The Copilot tool names in `tools/build_copilot.py` (`TOOL_MAP`) differ between VS Code versions. Adjust them if Copilot reports unknown tools.
- The skeleton's `deploy.yml` deliberately fails until the devops-engineer has implemented the cloud-specific deploy step.
