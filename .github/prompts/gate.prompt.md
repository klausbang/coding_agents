---
description: "Run a human-in-the-loop gate (G1 Scope, G2 Design, G3 V&V review, G4 Release) - assemble the gate package, ask the human to approve/change/reject, and log the decision."
agent: orchestrator
---

<!-- Generated from .claude/skills/gate/SKILL.md by tools/build_copilot.py. Edit the source, not this file. -->

# Gate ${input:args}

Find the current sprint: it is the newest `project/sprints/sprint-N.md`.

## 1. Build the gate package (show it as text, about 25 lines or fewer)

| Gate | Show |
|---|---|
| **G1 Scope** | Each story: `US-NNN` title, persona, AC count, size, priority. The linked NFRs. What is explicitly out of scope. |
| **G2 Design** | The OpenAPI changes (new or changed `IF-NNN`, any breaking changes), the new or changed ADRs, the ERD changes and migrations (**flag destructive ones**), the top threats and mitigations from the threat model, and any deviation from the reference stack. |
| **G3 V&V review** | The verification report (TC pass/fail, coverage, load against budget), the security report (findings by severity), the validation report (scenario results, findings, the validation-engineer's recommendation), open bugs, and `python tools/trace_check.py --sprint N` output. |
| **G4 Release** | The image digest on staging, the changelog and release notes, the migrations to run, the rollback plan, the open risks the human accepted at G3, and `trace_check --strict` (it must pass). |

Add the open **non-blocking questions** collected since the last gate.

## 2. Ask

Use `AskUserQuestion`:
- Question 1, "Gate <G>: approve?". The options are **Approve (Recommended)**, or whichever option you actually recommend first, **Approve with changes** and **Reject**.
- Questions 2–4: the most important open questions, each with the agent's options and the recommended one first. If there are more, ask them in a second round.

## 3. Record

- Append to `project/hitl/decisions.md`:
  ```
  ### <YYYY-MM-DD> <G> sprint-N — <Approved | Approved with changes | Rejected>
  - Scope: <IDs>
  - Conditions/changes: <...>
  - Answers: Q-NNN → <answer>, ...
  ```
- Mark the answered questions in `project/hitl/questions.md` (`- status: answered`, `- answer: ...`).
- Add a line to the sprint file's gate log.

## 4. Continue

- **Approved.** Move the sprint `phase:` forward: after G1 to design, G2 to build, G3 to release, G4 to closed (after the deploy and the retro). Then continue with the next step.
- **Approved with changes.** Brief the owning agent(s) with the changes, then re-run this gate in short form, showing only the deltas.
- **Rejected.** Ask what has to change if it is not clear, route the work back, and keep the phase as it is.

Never approve on the human's behalf, and never treat silence as approval.
