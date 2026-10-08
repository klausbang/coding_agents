#!/usr/bin/env python3
"""Print a factual project status snapshot (markdown) for the orchestrator.

Covers: current sprint and phase, story counts by status, open questions,
open bugs, and traceability coverage. The orchestrator turns this into the
narrative project/hitl/status.md.

Usage: python tools/status_report.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import ROOT, front_matter, iter_files, read_text, rel  # noqa: E402


def latest_sprint() -> tuple[str, dict[str, str]] | None:
    sprints = []
    for p in iter_files("project/sprints", suffixes={".md"}):
        m = re.fullmatch(r"sprint-(\d+)\.md", p.name)
        if m:
            sprints.append((int(m.group(1)), p))
    if not sprints:
        return None
    _, path = max(sprints)
    return rel(path), front_matter(read_text(path))


def main() -> int:
    if not (ROOT / "project").exists():
        print("No project/ folder yet. Run `python tools/kit.py init --name \"<Project>\"` first.")
        return 0

    print("## Project status (facts)\n")
    sprint = latest_sprint()
    if sprint:
        path, fm = sprint
        print(f"- **Current sprint:** {fm.get('sprint', '?')} — {fm.get('goal', '(no goal)')} "
              f"— phase `{fm.get('phase', '?')}` ({path})")
    else:
        print("- **Current sprint:** none started (use /sprint-start)")

    statuses: Counter[str] = Counter()
    for p in iter_files("project/backlog", suffixes={".md"}):
        if p.name.startswith("US-"):
            statuses[front_matter(read_text(p)).get("status", "draft")] += 1
    if statuses:
        print("- **Stories:** " + ", ".join(f"{n} {s}" for s, n in sorted(statuses.items())))
    else:
        print("- **Stories:** none yet")

    qfile = ROOT / "project" / "hitl" / "questions.md"
    open_q = []
    if qfile.exists():
        text = re.sub(r"<!--.*?-->", "", read_text(qfile), flags=re.S)
        blocks = re.split(r"(?m)^#{2,3}\s+", text)[1:]
        open_q = [b.splitlines()[0] for b in blocks if re.search(r"status:\s*open", b)]
    print(f"- **Open questions:** {len(open_q)}" + "".join(f"\n  - {q}" for q in open_q))

    open_bugs = []
    for p in iter_files("project/sprints/bugs", suffixes={".md"}):
        fm = front_matter(read_text(p))
        if fm.get("status", "open") not in {"closed", "fixed", "wontfix"}:
            open_bugs.append(f"{fm.get('id', p.stem)} [{fm.get('severity', '?')}] {fm.get('title', '')}")
    print(f"- **Open bugs:** {len(open_bugs)}" + "".join(f"\n  - {b}" for b in open_bugs))

    trace = subprocess.run([sys.executable, str(ROOT / "tools" / "trace_check.py")],
                           capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    lines = trace.stdout.strip().splitlines()
    print(f"- **Traceability:** {lines[0] if lines else 'n/a'}")
    for line in lines[1:8]:
        print(f"  {line.strip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
