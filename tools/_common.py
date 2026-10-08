"""Shared helpers for the kit tools (stdlib only)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

ID_PATTERNS: dict[str, str] = {
    "EPIC": r"EPIC-\d{2}",
    "US": r"US-\d{3}",
    "AC": r"AC-\d{3}\.\d+",
    "NFR": r"NFR-\d{3}",
    "ADR": r"ADR-\d{3}",
    "IF": r"IF-\d{3}",
    "TC": r"TC-\d{3}",
    "VAL": r"VAL-\d{3}",
    "BUG": r"BUG-\d{3}",
    "Q": r"Q-\d{3}",
}
# Any token that looks like one of our IDs, well-formed or not.
ANY_ID = re.compile(r"(?<![\w-])(EPIC|US|AC|NFR|ADR|IF|TC|VAL|BUG|Q)-(\d+(?:\.\d+)?)(?![\w-])")
WELL_FORMED = {k: re.compile(rf"^{v}$") for k, v in ID_PATTERNS.items()}

TEXT_SUFFIXES = {".md", ".py", ".feature", ".yaml", ".yml", ".csv", ".html", ".txt", ".json", ".toml"}
SKIP_DIRS = {"__pycache__", ".venv", "venv", "node_modules", ".git", ".pytest_cache"}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def iter_files(*dirs: str, suffixes: set[str] | None = None):
    suffixes = suffixes or TEXT_SUFFIXES
    for d in dirs:
        base = ROOT / d
        if not base.exists():
            continue
        for p in sorted(base.rglob("*")):
            if p.is_file() and p.suffix in suffixes and not (SKIP_DIRS & set(p.parts)):
                yield p


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def front_matter(text: str) -> dict[str, str]:
    """Parse a minimal `---` YAML front matter block: top-level `key: value` lines only."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    data: dict[str, str] = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            value = re.split(r"\s+#", m.group(2), maxsplit=1)[0].strip()
            data[m.group(1)] = value.strip("\"'")
    return data


def as_list(value: str) -> list[str]:
    """Turn '[A, B]' or 'A, B' into ['A', 'B']."""
    value = value.strip().strip("[]")
    return [v.strip().strip("\"'") for v in value.split(",") if v.strip()]


AC_LINE = re.compile(r"^\s*[-*]\s+\*\*(AC-(\d{3})\.(\d+))\*\*")
IF_DEF = re.compile(r"x-id:\s*[\"']?(IF-\d{3})")
TC_DEF = re.compile(r"\btc\(\s*[\"'](TC-\d{3})[\"']")
VAL_DEF = re.compile(r"@(VAL-\d{3})\b")
Q_DEF = re.compile(r"^#{2,3}\s+(Q-\d{3})\b", re.M)


def collect_definitions() -> tuple[dict[str, list[str]], list[str]]:
    """Return ({id: [where defined, ...]}, [problems])."""
    defs: dict[str, list[str]] = {}
    problems: list[str] = []

    def add(id_: str, where: str) -> None:
        defs.setdefault(id_, []).append(where)

    for p in iter_files("project", suffixes={".md"}):
        text = read_text(p)
        fm = front_matter(text)
        r = rel(p)
        if fm.get("id"):
            id_ = fm["id"]
            add(id_, r)
            if not p.name.startswith(id_):
                problems.append(f"{r}: front matter id {id_} does not match file name")
        if p.name.startswith("US-"):
            story = fm.get("id", p.name[:6])
            for line in text.splitlines():
                m = AC_LINE.match(line)
                if m:
                    add(m.group(1), r)
                    if f"US-{m.group(2)}" != story:
                        problems.append(f"{r}: {m.group(1)} does not belong to {story}")
        if p.name == "questions.md":
            for m in Q_DEF.finditer(text):
                add(m.group(1), r)

    for p in iter_files("project", suffixes={".yaml", ".yml"}):
        for m in IF_DEF.finditer(read_text(p)):
            add(m.group(1), rel(p))
    for p in iter_files("tests", suffixes={".py"}):
        for m in TC_DEF.finditer(read_text(p)):
            add(m.group(1), rel(p))
    for p in iter_files("tests", suffixes={".feature"}):
        for m in VAL_DEF.finditer(read_text(p)):
            add(m.group(1), rel(p))
    return defs, problems
