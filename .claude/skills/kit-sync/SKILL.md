---
name: kit-sync
description: Keep this project's agent kit in sync with the shared coding_agents repository - show status, pull kit updates into the project, or push agent/skill/tool improvements made here back upstream as a pull request.
argument-hint: status | pull | push ["description of the improvement"]
disable-model-invocation: true
---

# Kit sync: $ARGUMENTS

The shared kit lives in the repository named in `kit.json` (`upstream`). The kit-owned paths are listed in `kit.json` → `kit_paths`. Everything else belongs to this project and never leaves it.

## status (default)
Run `python tools/kit.py status` and explain the result in 2–4 lines: the kit version, how many upstream updates are waiting, and which local kit changes have not been contributed yet.

## pull
1. Run `git status`. If the working tree is not clean, offer to commit first (show what would be committed).
2. Run `python tools/kit.py pull`.
3. If there are conflicts:
   - in kit paths, normally take the upstream version: `git checkout --theirs <file>`;
   - in project files, keep the project version.
   Explain each conflict to the human before resolving it, then commit.
4. Run `python tools/build_copilot.py --check` and `python tools/id_lint.py`.
5. Summarize what changed in the agents and skills, so the human knows about any new behaviour.

## push
1. Make sure the kit changes are committed. Show `git diff kit/main -- <kit paths>` in summary form, about one line per file.
2. Review the changes before they leave the project:
   - **No product-specific content in kit files.** Product names, domain terms, URLs and customer data belong in `project/`. Generalize anything you find, or drop it.
   - Run `python tools/build_copilot.py`; the generated Copilot files must be current.
   - If the change alters agent behaviour, bump `version` in `kit.json` (minor version for new behaviour, patch version for fixes) and add an entry to `docs/kit/CHANGELOG.md`.
3. Run a dry run: `python tools/kit.py push -m "<summary>"`.
4. Ask the human with `AskUserQuestion`: **Open PR upstream (Recommended)** / **Push directly to main** / **Cancel**.
5. Run `python tools/kit.py push -m "<summary>" --yes`, adding `--direct` if the human chose that. Report the PR URL.
6. Remind the human: after the PR is merged, run `/kit-sync pull` in this and in other projects.
