---
name: trace
description: Check traceability from user stories and acceptance criteria to interfaces, verification tests and acceptance scenarios; write project/traceability.csv and route gaps to the owning agents.
argument-hint: [sprint number]
---

# Traceability check

1. Run `python tools/id_lint.py`. If it reports problems, list them and route each one to the owner of the file it is in (see `tools/agent_roles.json`).
2. Run `python tools/trace_check.py --write` with `--sprint $ARGUMENTS` if a sprint number was given.
3. Summarize the result for the human: the number of AC that are covered, partial and missing, plus the list of gaps.
4. For each gap, propose the fix and its owner:
   - no verification test → `verification-engineer`
   - no acceptance scenario → `validation-engineer`
   - a test references an unknown AC → the test's owner fixes the reference, or the `requirements-engineer` adds the missing AC
   - a story without `interfaces:` → `system-architect` supplies the mapping, then `requirements-engineer` fills it in
5. Ask the human whether to dispatch the fixes now. If the answer is yes, brief the agents in parallel.
