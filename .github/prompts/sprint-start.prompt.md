---
description: "Start a new Agile V-model sprint for a goal - creates project/sprints/sprint-N.md, has the requirements-engineer draft stories and acceptance criteria, and runs gate G1 with the human."
agent: orchestrator
---

<!-- Generated from .claude/skills/sprint-start/SKILL.md by tools/build_copilot.py. Edit the source, not this file. -->

# Start a v-sprint

Sprint goal: **${input:args}**

If no goal was given, ask the human for one with `AskUserQuestion`. Offer 2–3 candidates taken from the highest-priority `draft` or `approved` stories in `project/backlog/`, if there are any.

## Steps

1. **Pre-checks.**
   - `project/vision.md` must exist and must not be the unfilled template. If it is a template, run `/kit-init` first.
   - The previous sprint must have `phase: closed`. If it is not closed, ask the human whether to close it or continue it.
2. **Create the sprint file.** N is the highest existing `sprint-N.md` number plus one. Copy `templates/artifacts/sprint.md` to `project/sprints/sprint-N.md` and fill in `sprint`, `goal`, `phase: planning`, `started` (today) and the Plan section.
3. **Requirements (L1).** Brief the `requirements-engineer` subagent:
   ```
   SPRINT: N — <goal>
   TASK: Draft or refine the epics, user stories (status: draft, sprint: N), acceptance criteria and NFRs needed for this goal.
   SCOPE: new stories plus related existing ones: <IDs if known>
   INPUTS: project/vision.md, project/backlog/, the last retro in project/sprints/
   OUTPUT: backlog files; standard report block
   ```
4. **Handle the report.** Log questions as described in the orchestrator rules. Ask blocking ones right away. Keep non-blocking ones for the gate.
5. **Gate G1 Scope.** Run the `/gate G1` procedure:
   - Present each story as `US-NNN title`, its AC count, its size and its priority, plus the NFRs and the non-blocking questions.
   - Ask with `AskUserQuestion`.
   - On approval: have the requirements-engineer set the approved stories to `status: approved`, then record the decision.
6. Add the approved story IDs to the sprint file's `stories:` field. Set `phase: design`. Update `project/hitl/status.md`.
7. Tell the human the next step: design, done by the system-architect, then the database-engineer and the security-engineer, ending at gate G2. Continue straight away unless the human wants to pause.
