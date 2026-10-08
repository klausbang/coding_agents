---
description: "Run the release part of the v-sprint - final checks, docs and changelog, gate G4 with the human, then production deploy by the devops-engineer and the sprint retro. Never deploys without explicit G4 approval."
agent: orchestrator
---

<!-- Generated from .claude/skills/release/SKILL.md by tools/build_copilot.py. Edit the source, not this file. -->

# Release the current sprint

1. **Preconditions.** All of these must hold. If one fails, stop and report which.
   - The sprint is in `phase: release`, which means G3 was approved.
   - There are no open **high** or **critical** bugs, except ones the human accepted at G3 (check `decisions.md`).
   - `python tools/trace_check.py --sprint N --strict` passes.
   - The CI pipeline on `main` is green: `gh run list --branch main --limit 3`.
2. **Docs.** Brief the `docs-writer` to update the changelog, the release notes (in the sprint file), the API reference and the guides.
3. **Release package.** Brief the `devops-engineer`. It reports, without deploying:
   - the staging image digest;
   - the migrations that will run;
   - the rollback plan;
   - the infrastructure changes (`terraform plan` summary).
4. **Gate G4.** Run `/gate G4` with that package.
5. **Deploy, only after "Approve".** Brief the `devops-engineer`:
   ```
   TASK: Deploy image <digest> to production. G4 approved on <date> (see decisions.md).
   OUTPUT: deploy report — digest, migrations result, /health result, smoke test result.
   ```
   If production needs a manual approval in the GitHub environment, tell the human to approve the waiting deployment.
6. **Close.**
   - Tag the release (`git tag v<version>` after the human confirms the version).
   - Write the retro in the sprint file: what went well, what to improve, metrics (number of questions to the human, fix loops, rule breaks).
   - Set `phase: closed` and update `status.md`.
7. **Kit feedback.** If the retro shows that an agent's instructions should change, propose the edit and offer `/kit-sync push`.
