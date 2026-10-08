#!/usr/bin/env python3
"""PreToolUse hook: block subagents from writing outside the paths they own.

Usage (from a subagent's frontmatter hook):
    python "$CLAUDE_PROJECT_DIR/.claude/hooks/write_guard.py" <role>

Without a role argument the role is taken from the hook input's
``agent_type`` field (set when the tool call comes from a subagent).
Calls from the main session, or from roles not listed in
tools/agent_roles.json, are allowed.

Exit 0 = allow, exit 2 = block (stderr is shown to the agent).
"""
from __future__ import annotations

import json
import os
import re
import sys
from functools import lru_cache
from pathlib import Path

PATH_KEYS = ("file_path", "notebook_path", "path")


@lru_cache(maxsize=None)
def _glob_regex(pattern: str) -> re.Pattern[str]:
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def matches(rel_path: str, patterns: list[str]) -> bool:
    """True if rel_path matches a pattern and no '!'-prefixed exception."""
    hit = any(_glob_regex(p).match(rel_path) for p in patterns if not p.startswith("!"))
    return hit and not any(_glob_regex(p[1:]).match(rel_path) for p in patterns if p.startswith("!"))


def project_root(payload: dict) -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env).resolve()
    if payload.get("cwd"):
        return Path(payload["cwd"]).resolve()
    return Path(__file__).resolve().parents[2]


def check(role: str, rel_path: str, rules: dict) -> str | None:
    """Return a reason string if the write must be blocked, else None."""
    if rel_path.startswith("../"):
        return f"'{rel_path}' is outside the project."
    if matches(rel_path, rules.get("global_deny", [])):
        return f"'{rel_path}' is protected for all subagents (kit files, secrets, orchestrator state)."
    role_rules = rules.get("roles", {}).get(role)
    if role_rules is None:
        return None  # unknown role (e.g. built-in Explore/general-purpose): not guarded
    if matches(rel_path, role_rules.get("deny", [])):
        return f"'{rel_path}' is explicitly owned by another agent."
    if not matches(rel_path, role_rules.get("allow", [])):
        allowed = ", ".join(role_rules.get("allow", [])) or "nothing"
        return f"'{rel_path}' is not in the paths owned by {role} ({allowed})."
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    role = sys.argv[1] if len(sys.argv) > 1 else (payload.get("agent_type") or "")
    if not role:
        return 0  # main session

    tool_input = payload.get("tool_input") or {}
    raw = next((tool_input[k] for k in PATH_KEYS if tool_input.get(k)), None)
    if not raw:
        return 0

    root = project_root(payload)
    target = Path(raw)
    if not target.is_absolute():
        target = Path(payload.get("cwd") or root) / target
    try:
        rel = target.resolve().relative_to(root).as_posix()
    except ValueError:
        rel = "../" + target.name

    rules_file = root / "tools" / "agent_roles.json"
    try:
        rules = json.loads(rules_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"write_guard: cannot read {rules_file}: {exc}", file=sys.stderr)
        return 2

    reason = check(role, rel, rules)
    if reason:
        print(
            f"BLOCKED by write_guard: {reason}\n"
            "Do not work around this with shell commands. Describe the needed change "
            "under NEXT: in your report so the owning agent can make it.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
