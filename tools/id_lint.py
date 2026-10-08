#!/usr/bin/env python3
"""Check traceability IDs across project/, tests/ and app/.

Errors:
  * malformed IDs (e.g. US-14 instead of US-014)
  * duplicate definitions (same ID defined in two places)
  * references to IDs that are never defined (EPIC, US, AC, NFR, ADR, IF)
  * front matter id not matching the file name, AC not matching its story

Usage:
  python tools/id_lint.py           # human-readable report, exit 1 on errors
  python tools/id_lint.py --hook    # Claude Code PostToolUse hook mode (exit 2 on errors)
See .claude/protocol.md for the ID scheme.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ANY_ID, ROOT, WELL_FORMED, collect_definitions, iter_files, read_text, rel  # noqa: E402

# References to these kinds must resolve to a definition.
MUST_RESOLVE = {"EPIC", "US", "AC", "NFR", "ADR", "IF"}
# BUG files and Q headings are also definitions; TC/VAL are defined where used.
DUPLICATE_OK = {"TC", "VAL"}  # a TC/VAL id may appear on several lines of the same test/feature


def lint() -> list[str]:
    errors: list[str] = []
    defs, problems = collect_definitions()
    errors.extend(problems)

    for id_, places in sorted(defs.items()):
        kind = id_.split("-")[0]
        unique_places = sorted(set(places))
        if kind in DUPLICATE_OK:
            if len(unique_places) > 1:
                errors.append(f"{id_} defined in several files: {', '.join(unique_places)}")
        elif len(places) > 1:
            errors.append(f"{id_} defined more than once: {', '.join(places)}")

    for p in iter_files("project", "tests", "app"):
        text = read_text(p)
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in ANY_ID.finditer(line):
                kind, token = m.group(1), m.group(0)
                where = f"{rel(p)}:{lineno}"
                if not WELL_FORMED[kind].match(token):
                    errors.append(f"{where}: malformed ID '{token}'")
                elif kind in MUST_RESOLVE and token not in defs:
                    errors.append(f"{where}: reference to undefined {token}")
    # de-duplicate while keeping order
    return list(dict.fromkeys(errors))


def hook_mode() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    path = (payload.get("tool_input") or {}).get("file_path", "")
    try:
        relpath = Path(path).resolve().relative_to(ROOT).as_posix()
    except (ValueError, OSError):
        return 0
    if not relpath.startswith(("project/", "tests/")):
        return 0
    errors = lint()
    if errors:
        shown = "\n".join(f"  - {e}" for e in errors[:15])
        more = f"\n  … and {len(errors) - 15} more" if len(errors) > 15 else ""
        print(f"id_lint found traceability ID problems:\n{shown}{more}\n"
              "Fix the ones you introduced (see .claude/protocol.md, 'IDs and traceability').",
              file=sys.stderr)
        return 2
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hook", action="store_true", help="run as a Claude Code PostToolUse hook")
    args = ap.parse_args()
    if args.hook:
        return hook_mode()
    errors = lint()
    if errors:
        print(f"id_lint: {len(errors)} problem(s)")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("id_lint: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
