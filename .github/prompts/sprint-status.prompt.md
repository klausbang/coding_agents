---
description: "Summarize where the project and current sprint stand - phase, stories, open questions, bugs, traceability - and refresh project/hitl/status.md. Use at the start of a session or when the human asks for progress."
agent: orchestrator
---

<!-- Generated from .claude/skills/sprint-status/SKILL.md by tools/build_copilot.py. Edit the source, not this file. -->

# Sprint status

1. Run `python tools/status_report.py` and read the newest `project/sprints/sprint-N.md`. Read its progress log and gate log.
2. Overwrite `project/hitl/status.md` using the status format in the orchestrator rules.
3. Reply to the human in at most 8 lines:
   - the sprint, goal and phase;
   - what was done since the last update;
   - **what is waiting for the human**: the gates and open questions with their IDs;
   - risks and blockers, such as open high-severity bugs, traceability gaps or fix loops at their limit;
   - the next step you propose.
4. If questions are open, offer to go through them now with `AskUserQuestion` (at most 4 at a time).
