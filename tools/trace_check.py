#!/usr/bin/env python3
"""Build the traceability matrix: story -> AC -> interfaces -> tests -> acceptance scenarios.

An acceptance criterion is *covered* when it has at least one verification test
(pytest test function marked/annotated with the AC id outside tests/acceptance)
AND at least one acceptance scenario (Gherkin scenario tagged @AC-NNN.N).

Usage:
  python tools/trace_check.py                     # summary for all non-draft stories
  python tools/trace_check.py --sprint 3          # only stories with `sprint: 3`
  python tools/trace_check.py --write             # also write project/traceability.csv
  python tools/trace_check.py --strict            # exit 1 if any in-scope AC is not covered
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import AC_LINE, ROOT, as_list, front_matter, iter_files, read_text, rel  # noqa: E402

AC_REF = re.compile(r"AC-\d{3}\.\d+")
TC_REF = re.compile(r"TC-\d{3}")
TEST_DEF = re.compile(r"^\s*(?:async\s+)?def\s+(test_\w+)")
SCENARIO = re.compile(r"^\s*Scenario(?: Outline)?:\s*(.+)$")
IN_SCOPE_STATUSES = {"approved", "in-progress", "done"}


@dataclass
class Criterion:
    story: str
    ac: str
    status: str
    sprint: str
    interfaces: list[str]
    tests: list[str] = field(default_factory=list)
    tcs: list[str] = field(default_factory=list)
    scenarios: list[str] = field(default_factory=list)

    @property
    def coverage(self) -> str:
        if self.tests and self.scenarios:
            return "covered"
        if self.tests or self.scenarios:
            return "partial"
        return "missing"


def load_criteria() -> dict[str, Criterion]:
    out: dict[str, Criterion] = {}
    for p in iter_files("project/backlog", suffixes={".md"}):
        if not p.name.startswith("US-"):
            continue
        text = read_text(p)
        fm = front_matter(text)
        story = fm.get("id", p.name[:6])
        for line in text.splitlines():
            m = AC_LINE.match(line)
            if m:
                out[m.group(1)] = Criterion(
                    story=story, ac=m.group(1), status=fm.get("status", "draft"),
                    sprint=fm.get("sprint", ""), interfaces=as_list(fm.get("interfaces", "")),
                )
    return out


def scan_python_tests(criteria: dict[str, Criterion], unknown: list[str]) -> None:
    for p in iter_files("tests", suffixes={".py"}):
        if "acceptance" in p.relative_to(ROOT).parts:
            continue
        pending_acs: list[str] = []
        pending_tcs: list[str] = []
        lines = read_text(p).splitlines()
        for i, line in enumerate(lines):
            m = TEST_DEF.match(line)
            if m:
                # markers above the def plus the docstring/first lines of the body
                body = " ".join(lines[i + 1:i + 4])
                acs = pending_acs + AC_REF.findall(line + body)
                tcs = pending_tcs + TC_REF.findall(line + body)
                for ac in dict.fromkeys(acs):
                    target = f"{rel(p)}::{m.group(1)}"
                    if ac in criteria:
                        criteria[ac].tests.append(target)
                        criteria[ac].tcs.extend(t for t in tcs if t not in criteria[ac].tcs)
                    else:
                        unknown.append(f"{target} references unknown {ac}")
                pending_acs, pending_tcs = [], []
            elif line.lstrip().startswith(("@", "#")):
                pending_acs += AC_REF.findall(line)
                pending_tcs += TC_REF.findall(line)
            elif line.strip() and not line.startswith((" ", "\t")):
                pending_acs, pending_tcs = [], []


def scan_features(criteria: dict[str, Criterion], unknown: list[str]) -> None:
    for p in iter_files("tests", suffixes={".feature"}):
        tags: list[str] = []
        for line in read_text(p).splitlines():
            stripped = line.strip()
            if stripped.startswith("@"):
                tags += stripped.split()
                continue
            m = SCENARIO.match(line)
            if m:
                vals = [t[1:] for t in tags if t.startswith("@VAL-")]
                label = f"{rel(p)}: {vals[0] if vals else m.group(1).strip()}"
                for t in tags:
                    ac = t[1:]
                    if AC_REF.fullmatch(ac):
                        if ac in criteria:
                            criteria[ac].scenarios.append(label)
                        else:
                            unknown.append(f"{label} references unknown {ac}")
            if stripped and not stripped.startswith("#"):
                tags = []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sprint", help="only stories planned for this sprint number")
    ap.add_argument("--write", action="store_true", help="write project/traceability.csv")
    ap.add_argument("--strict", action="store_true", help="exit 1 when an in-scope AC is not fully covered")
    args = ap.parse_args()

    criteria = load_criteria()
    unknown: list[str] = []
    scan_python_tests(criteria, unknown)
    scan_features(criteria, unknown)

    if args.sprint:
        scope = [c for c in criteria.values() if c.sprint == str(args.sprint)]
    else:
        scope = [c for c in criteria.values() if c.status in IN_SCOPE_STATUSES]

    if args.write:
        out = ROOT / "project" / "traceability.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["story", "ac", "status", "sprint", "interfaces",
                        "verification_tests", "tc_ids", "acceptance_scenarios", "coverage"])
            for c in sorted(criteria.values(), key=lambda c: (c.story, c.ac)):
                w.writerow([c.story, c.ac, c.status, c.sprint, " ".join(c.interfaces),
                            " | ".join(c.tests), " ".join(c.tcs), " | ".join(c.scenarios), c.coverage])
        print(f"wrote {rel(out)}")

    counts = {k: sum(1 for c in scope if c.coverage == k) for k in ("covered", "partial", "missing")}
    label = f"sprint {args.sprint}" if args.sprint else "approved/in-progress/done stories"
    print(f"trace_check ({label}): {len(scope)} AC — "
          f"{counts['covered']} covered, {counts['partial']} partial, {counts['missing']} missing")
    for c in sorted(scope, key=lambda c: c.ac):
        if c.coverage != "covered":
            gaps = []
            if not c.tests:
                gaps.append("no verification test")
            if not c.scenarios:
                gaps.append("no acceptance scenario")
            print(f"  - {c.ac} ({c.story}): {', '.join(gaps)}")
    for u in unknown:
        print(f"  ! {u}")

    if args.strict and (counts["partial"] or counts["missing"] or unknown):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
