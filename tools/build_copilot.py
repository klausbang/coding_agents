#!/usr/bin/env python3
"""Generate GitHub Copilot files from the Claude Code sources (single source of truth).

  .claude/agents/<name>.md        -> .github/agents/<name>.agent.md
  .claude/orchestrator.md          -> .github/agents/orchestrator.agent.md
  .claude/skills/<name>/SKILL.md   -> .github/prompts/<name>.prompt.md

Never edit the generated files by hand. Edit the sources and re-run:
  python tools/build_copilot.py           # (re)generate
  python tools/build_copilot.py --check   # exit 1 if generated files are stale (used in CI)

Copilot tool names differ between VS Code versions; adjust TOOL_MAP if your
version reports unknown tools.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ROOT, front_matter, read_text, rel  # noqa: E402

TOOL_MAP = {
    "Read": ["read", "search"],
    "Grep": ["search"],
    "Glob": ["search"],
    "Edit": ["edit"],
    "Write": ["edit"],
    "MultiEdit": ["edit"],
    "Bash": ["execute"],
    "WebFetch": ["web"],
    "WebSearch": ["web"],
}
BASE_TOOLS = ["todo"]

# Copilot "handoffs": buttons that pass the work to the next agent in the V.
HANDOFFS: dict[str, list[tuple[str, str, str]]] = {
    "orchestrator": [
        ("Draft stories", "requirements-engineer", "Draft user stories and acceptance criteria for the sprint goal above."),
    ],
    "requirements-engineer": [
        ("Design architecture", "system-architect", "Design the contract and components for the approved stories above."),
        ("Write acceptance scenarios", "validation-engineer", "Mode A: write Gherkin scenarios for the approved acceptance criteria above."),
    ],
    "system-architect": [
        ("Design data model", "database-engineer", "Design the data model and migrations for the architecture above."),
        ("Threat model", "security-engineer", "Mode A: threat-model the design above."),
    ],
    "database-engineer": [
        ("Implement backend", "backend-developer", "Implement the services and endpoints on top of the models above (TDD)."),
    ],
    "backend-developer": [
        ("Build UI", "frontend-developer", "Build the views for the endpoints implemented above."),
        ("Review", "code-reviewer", "Review the change set above."),
    ],
    "frontend-developer": [
        ("Review", "code-reviewer", "Review the change set above."),
    ],
    "code-reviewer": [
        ("Verify", "verification-engineer", "Verify the reviewed change set above against its acceptance criteria."),
    ],
    "verification-engineer": [
        ("Security test", "security-engineer", "Mode B: security-test the verified build above."),
        ("Validate", "validation-engineer", "Mode B: run acceptance testing for the verified build above."),
    ],
    "security-engineer": [
        ("Verify", "verification-engineer", "Turn the mitigations above into verification tests."),
    ],
    "validation-engineer": [
        ("Update docs", "docs-writer", "Update docs, changelog and traceability for this sprint."),
        ("Rework stories", "requirements-engineer", "Rework the backlog based on the validation findings above."),
    ],
    "devops-engineer": [
        ("Verify on staging", "verification-engineer", "Run system tests against the staging deployment above."),
    ],
    "docs-writer": [
        ("Back to orchestrator", "orchestrator", "Docs and traceability are updated; prepare the release gate."),
    ],
}

COPILOT_NOTE = """> **Copilot adaptation** (generated from `{src}` by `tools/build_copilot.py`. Edit the source, not this file.)
> - "Agent tool / subagent" means: use the handoff buttons below, or `#runSubagent` with the named agent.
> - "AskUserQuestion" means: ask the human in chat, with numbered options and your recommendation, then stop and wait.
> - Copilot has no hooks. Enforce the file ownership in `tools/agent_roles.json` yourself; CI checks the IDs and traceability.
"""


def split_source(path: Path) -> tuple[dict[str, str], str]:
    text = read_text(path)
    fm = front_matter(text)
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        body = text[end + 4:].lstrip("\n")
    return fm, body


def yaml_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)  # JSON strings are valid YAML scalars


def tools_for(fm: dict[str, str], extra: list[str] | None = None) -> list[str]:
    tools: list[str] = []
    for t in [x.strip() for x in fm.get("tools", "").split(",") if x.strip()]:
        tools += TOOL_MAP.get(t, [])
    tools += BASE_TOOLS + (extra or [])
    return list(dict.fromkeys(tools))


def agent_file(name: str, description: str, tools: list[str], body: str, src: Path) -> str:
    lines = ["---", f"name: {name}", f"description: {yaml_str(description)}",
             "tools: [" + ", ".join(yaml_str(t) for t in tools) + "]"]
    if HANDOFFS.get(name):
        lines.append("handoffs:")
        for label, agent, prompt in HANDOFFS[name]:
            lines += [f"  - label: {yaml_str(label)}", f"    agent: {agent}",
                      f"    prompt: {yaml_str(prompt)}", "    send: false"]
    lines.append("---")
    return "\n".join(lines) + "\n\n" + COPILOT_NOTE.format(src=rel(src)) + "\n" + body.rstrip() + "\n"


def prompt_file(fm: dict[str, str], body: str, src: Path) -> str:
    body = body.replace("$ARGUMENTS", "${input:args}")
    lines = ["---", f"description: {yaml_str(fm.get('description', ''))}", "agent: orchestrator", "---"]
    note = f"<!-- Generated from {rel(src)} by tools/build_copilot.py. Edit the source, not this file. -->"
    return "\n".join(lines) + "\n\n" + note + "\n\n" + body.rstrip() + "\n"


def build() -> dict[Path, str]:
    out: dict[Path, str] = {}
    for src in sorted((ROOT / ".claude" / "agents").glob("*.md")):
        fm, body = split_source(src)
        name = fm.get("name", src.stem)
        out[ROOT / ".github" / "agents" / f"{name}.agent.md"] = agent_file(
            name, fm.get("description", ""), tools_for(fm), body, src)

    orch = ROOT / ".claude" / "orchestrator.md"
    if orch.exists():
        _, body = split_source(orch)
        out[ROOT / ".github" / "agents" / "orchestrator.agent.md"] = agent_file(
            "orchestrator",
            "Runs Agile V-model sprints for this Flask + PostgreSQL app: plans, delegates to the "
            "specialist agents, runs the human gates G1-G4 and keeps project/ state current.",
            ["read", "search", "edit", "execute", "todo", "agent"], body, orch)

    for src in sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md")):
        fm, body = split_source(src)
        name = fm.get("name", src.parent.name)
        out[ROOT / ".github" / "prompts" / f"{name}.prompt.md"] = prompt_file(fm, body, src)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="only check that generated files are up to date")
    args = ap.parse_args()

    files = build()
    targets_dirs = [ROOT / ".github" / "agents", ROOT / ".github" / "prompts"]
    stale_existing = [p for d in targets_dirs if d.exists() for p in d.glob("*.md") if p not in files]

    if args.check:
        stale = [p for p, c in files.items()
                 if not p.exists() or p.read_text(encoding="utf-8").replace("\r\n", "\n") != c]
        stale += stale_existing
        if stale:
            print("Copilot files are out of date (run `python tools/build_copilot.py`):")
            for p in stale:
                print(f"  - {rel(p)}")
            return 1
        print(f"build_copilot: {len(files)} generated files up to date")
        return 0

    for p in stale_existing:
        p.unlink()
        print(f"removed {rel(p)}")
    for p, content in files.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists() or p.read_text(encoding="utf-8").replace("\r\n", "\n") != content:
            p.write_text(content, encoding="utf-8", newline="\n")
            print(f"wrote {rel(p)}")
    print(f"build_copilot: {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
