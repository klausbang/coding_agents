---
name: kit-init
description: Set up a new product project from the coding_agents kit - run tools/kit.py init if needed, connect the project's own GitHub repo, and interview the human to write project/vision.md.
argument-hint: [project name]
disable-model-invocation: true
---

# Initialize a new project from the kit

## 1. Initialize (skip if `.kit/state.json` already exists)

1. Ask for anything missing, using `AskUserQuestion` for choices:
   - the project name (`$ARGUMENTS` if given);
   - the project's own GitHub repository: an existing URL, "create a new private repo with gh", or "later".
2. If the human chose to create a repo: `gh repo create <owner>/<slug> --private` (confirm the name first).
3. Run `python tools/kit.py init --name "<name>" [--origin <url>]` and show the output.
4. If an origin is set: `git push -u origin main`.

## 2. Vision interview

Fill in `project/vision.md` (template already in place) by interviewing the human. Ask in **at most 3 rounds**, with no more than 4 questions per round, and offer options wherever sensible:

1. **Problem and users:** what problem, for whom (2–3 personas with goals), and how they solve it today.
2. **Goals and scope:** success metrics (measurable), must-have capabilities for a first release, explicit non-goals.
3. **Constraints:**
   - cloud provider (Azure / AWS / GCP);
   - UI approach: Jinja + HTMX (recommended) or an SPA;
   - authentication: local accounts or an OIDC provider;
   - data sensitivity and GDPR, budget, deadlines, compliance needs.

Write the vision file in the user's own terms, and add a glossary of the domain words they used. Show it, ask for corrections, and commit it: `git add project/vision.md && git commit -m "Add product vision"`.

Record the constraint choices as decisions in `project/hitl/decisions.md`. If they differ from ADR-001, note that the system-architect must update ADR-001 in sprint 1.

## 3. Next

Suggest a first sprint goal: usually a "walking skeleton" (sign-up and sign-in plus one core object, deployed to staging). Then offer to run `/sprint-start`.
