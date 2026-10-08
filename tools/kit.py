#!/usr/bin/env python3
"""coding_agents kit manager.

The kit (agents, skills, hooks, tools, templates) lives in the upstream repo
named in kit.json. A product project is a copy of the kit plus its own files.
Kit-owned paths are listed in kit.json -> "kit_paths"; everything else belongs
to the project.

Commands
  init    Turn a fresh copy of the kit into a new project (run once).
  status  Show kit version, pending upstream updates and local kit changes.
  pull    Merge the latest kit from upstream into this project.
  push    Contribute this project's kit changes back upstream (branch + PR).

Examples
  python tools/kit.py init --name "Team Tasks" --origin https://github.com/me/team-tasks.git
  python tools/kit.py status
  python tools/kit.py pull
  python tools/kit.py push -m "verification-engineer: add mutation testing step"          # dry run
  python tools/kit.py push -m "verification-engineer: add mutation testing step" --yes    # do it
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_FILE = ROOT / "kit.json"
STATE_FILE = ROOT / ".kit" / "state.json"
SKELETON = ROOT / "templates" / "project-skeleton"
KIT_REMOTE = "kit"
for _stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")
TEXT_SUFFIXES = {".md", ".py", ".txt", ".toml", ".yaml", ".yml", ".json", ".html", ".cfg", ".ini",
                 ".csv", ".feature", ".example", ".j2", ".css", ".js", ""}


# --------------------------------------------------------------------------- helpers
def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def git(*args: str, cwd: Path = ROOT, check: bool = True) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        die(f"git {' '.join(args)} failed:\n{(r.stderr or r.stdout).strip()}")
    return r.stdout.strip()


def git_ok(*args: str, cwd: Path = ROOT) -> bool:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True).returncode == 0


def manifest() -> dict:
    if not MANIFEST_FILE.exists():
        die("kit.json not found — run this from a coding_agents kit or project.")
    data = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    data["upstream"] = os.environ.get("KIT_UPSTREAM", data["upstream"])
    return data


def state() -> dict | None:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return None


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "app"


def same_repo(a: str, b: str) -> bool:
    def norm(u: str) -> str:
        u = u.strip().rstrip("/").lower()
        u = re.sub(r"\.git$", "", u)
        u = re.sub(r"^git@github\.com:", "https://github.com/", u)
        return u.replace("\\", "/")
    return norm(a) == norm(b)


def remotes() -> dict[str, str]:
    out = {}
    for line in git("remote", "-v", check=False).splitlines():
        parts = line.split()
        if len(parts) >= 2:
            out[parts[0]] = parts[1]
    return out


def ensure_kit_remote(m: dict) -> None:
    rs = remotes()
    if KIT_REMOTE not in rs:
        git("remote", "add", KIT_REMOTE, m["upstream"])
    elif not same_repo(rs[KIT_REMOTE], m["upstream"]):
        git("remote", "set-url", KIT_REMOTE, m["upstream"])
    git("config", "merge.ours.driver", "true")


def fetch_kit(m: dict) -> bool:
    ok = git_ok("fetch", "--quiet", KIT_REMOTE, m["branch"])
    if not ok:
        print(f"warning: could not fetch {m['upstream']} ({m['branch']}); continuing offline.")
    return ok


def kit_ref(m: dict) -> str:
    return f"{KIT_REMOTE}/{m['branch']}"


def require_clean(paths: list[str] | None = None) -> None:
    args = ["status", "--porcelain"] + (["--", *paths] if paths else [])
    dirty = git(*args)
    if dirty:
        die("uncommitted changes" + (" in kit paths" if paths else "") +
            ":\n" + dirty + "\nCommit or stash them first.")


def is_text(path: Path) -> bool:
    if path.suffix not in TEXT_SUFFIXES:
        return False
    try:
        path.read_text(encoding="utf-8")
        return True
    except UnicodeDecodeError:
        return False


def rmtree(path: Path) -> None:
    def onexc(func, p, _exc):  # Windows: .git objects are read-only
        os.chmod(p, stat.S_IWRITE)
        func(p)
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=onexc)
    else:  # pragma: no cover
        shutil.rmtree(path, onerror=lambda f, p, e: onexc(f, p, e))


# --------------------------------------------------------------------------- init
def cmd_init(args: argparse.Namespace) -> None:
    m = manifest()
    if state() and not args.force:
        die(f"this project is already initialized ({STATE_FILE.relative_to(ROOT)}). Use --force to re-run.")
    if not SKELETON.exists():
        die(f"skeleton not found: {SKELETON}")

    name = args.name.strip()
    slug = args.slug or slugify(name)
    values = {"name": name, "slug": slug}
    replacements = {ph: values[key] for ph, key in m.get("placeholders", {}).items()}
    replace = set(m.get("replace_on_init", []))

    created, skipped = [], []
    for src in sorted(SKELETON.rglob("*")):
        if not src.is_file() or "__pycache__" in src.parts:
            continue
        relp = src.relative_to(SKELETON).as_posix()
        dest = ROOT / relp
        if dest.exists() and relp not in replace and not args.force:
            skipped.append(relp)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        if is_text(src):
            text = src.read_text(encoding="utf-8")
            for ph, val in replacements.items():
                text = text.replace(ph, val)
            dest.write_text(text, encoding="utf-8", newline="\n")
        else:
            shutil.copy2(src, dest)
        created.append(relp)

    # git setup
    fresh_repo = not (ROOT / ".git").exists()
    if fresh_repo:
        git("init", "-b", "main")
    rs = remotes()
    if "origin" in rs and same_repo(rs["origin"], m["upstream"]):
        git("remote", "rename", "origin", KIT_REMOTE)
    ensure_kit_remote(m)
    if args.origin:
        if "origin" in remotes():
            git("remote", "set-url", "origin", args.origin)
        else:
            git("remote", "add", "origin", args.origin)

    fetched = fetch_kit(m)
    kit_commit = git("rev-parse", kit_ref(m), check=False) if fetched else ""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({
        "project_name": name,
        "slug": slug,
        "kit_version": m["version"],
        "kit_commit": kit_commit,
        "initialized": dt.date.today().isoformat(),
    }, indent=2) + "\n", encoding="utf-8")

    git("add", "-A")
    git("commit", "-q", "-m", f"Initialize {name} from coding_agents kit v{m['version']}")

    # Projects created from a zip download or a GitHub template have no shared
    # history with the kit; adopt it once so later `pull`s merge cleanly.
    if fetched and not git_ok("merge-base", "HEAD", kit_ref(m)):
        drift = git("diff", "--stat", kit_ref(m), "HEAD", "--", *m["kit_paths"], check=False)
        if drift:
            print("warning: your kit files differ from the current upstream kit:\n" + drift +
                  "\nThey are kept as-is; run `kit.py status` to review.")
        git("merge", "-q", "-s", "ours", "--allow-unrelated-histories", "--no-edit",
            "-m", "Adopt coding_agents kit history", kit_ref(m))

    print(f"\nInitialized project '{name}' (slug: {slug}) from kit v{m['version']}.")
    print(f"  created/updated {len(created)} files" + (f", kept {len(skipped)} existing" if skipped else ""))
    print(f"  remotes: {', '.join(f'{k} -> {v}' for k, v in remotes().items())}")
    print("\nNext steps:")
    print("  1. Describe the product in project/vision.md (or run /kit-init in Claude Code to be interviewed).")
    if not args.origin:
        print("  2. Create the project repo on GitHub and run: git remote add origin <url>")
    print("  3. git push -u origin main")
    print("  4. In Claude Code:  /sprint-start <first goal>")


# --------------------------------------------------------------------------- status
def cmd_status(args: argparse.Namespace) -> None:
    m = manifest()
    st = state()
    if not st:
        print(f"This is the kit itself (coding_agents v{m['version']}) — not an initialized project.")
        print("Develop the kit here directly, commit and push to its origin.")
        return
    ensure_kit_remote(m)
    online = fetch_kit(m) if not args.offline else False
    print(f"Project:  {st['project_name']} ({st['slug']})")
    print(f"Kit:      v{m['version']} from {m['upstream']} ({m['branch']})")
    if not git_ok("rev-parse", "--verify", "--quiet", kit_ref(m)):
        print("Upstream: unknown (never fetched)")
        return
    behind = git("rev-list", "--count", f"HEAD..{kit_ref(m)}")
    print(f"Upstream: {behind} new kit commit(s) not yet merged" + ("" if online else " (cached)") +
          ("  →  run `kit.py pull`" if behind != "0" else ""))
    local = git("diff", "--stat", kit_ref(m), "HEAD", "--", *m["kit_paths"], check=False)
    if behind == "0" and local:
        print("Local kit changes not yet contributed upstream (`kit.py push`):\n" + local)
    elif local:
        print("Kit paths differ from upstream (includes upstream changes you have not pulled yet):\n" + local)
    uncommitted = git("status", "--porcelain", "--", *m["kit_paths"])
    if uncommitted:
        print("Uncommitted changes in kit paths:\n" + uncommitted)


# --------------------------------------------------------------------------- pull
def cmd_pull(args: argparse.Namespace) -> None:
    m = manifest()
    if not state():
        die("this is the kit itself; use `git pull` instead.")
    require_clean()
    ensure_kit_remote(m)
    if not fetch_kit(m):
        die("cannot reach the kit upstream.")
    if not git_ok("merge-base", "HEAD", kit_ref(m)):
        git("merge", "-q", "-s", "ours", "--allow-unrelated-histories", "--no-edit",
            "-m", "Adopt coding_agents kit history", kit_ref(m))
        print("Adopted kit history (first pull after a zip/template start). Nothing else merged.")
        return
    before = git("rev-parse", "HEAD")
    r = subprocess.run(["git", "merge", "--no-edit", "-m",
                        f"Merge coding_agents kit ({m['branch']})", kit_ref(m)],
                       cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        conflicts = git("diff", "--name-only", "--diff-filter=U", check=False)
        print(r.stdout + r.stderr)
        die("merge conflicts in:\n" + conflicts +
            "\nResolve them (kit paths: usually take the kit version; your own files: keep yours), "
            "then `git add` + `git commit`. Or abort with `git merge --abort`.")
    if git("rev-parse", "HEAD") == before:
        print("Already up to date with the kit.")
        return
    new_version = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))["version"]
    st = state() or {}
    st["kit_version"] = new_version
    st["kit_commit"] = git("rev-parse", kit_ref(m))
    STATE_FILE.write_text(json.dumps(st, indent=2) + "\n", encoding="utf-8")
    git("add", str(STATE_FILE.relative_to(ROOT)))
    git("commit", "-q", "-m", f"Record kit v{new_version}", check=False)
    print(f"Merged kit v{new_version}. Changed files:")
    print(git("diff", "--stat", before, "HEAD"))


# --------------------------------------------------------------------------- push
def cmd_push(args: argparse.Namespace) -> None:
    m = manifest()
    st = state()
    if not st:
        die("this is the kit itself; commit and `git push` directly.")
    paths = m["kit_paths"]
    require_clean(paths)
    ensure_kit_remote(m)
    if not fetch_kit(m):
        die("cannot reach the kit upstream.")
    if not git_ok("merge-base", "--is-ancestor", kit_ref(m), "HEAD"):
        die("upstream kit has changes you have not merged. Run `kit.py pull` first, then push.")

    changes = git("diff", "--name-status", kit_ref(m), "HEAD", "--", *paths)
    if not changes:
        print("No kit changes to contribute.")
        return
    print("Kit changes to contribute upstream:\n" + changes)
    if not args.yes:
        print("\nDry run. Re-run with --yes to create the upstream branch/PR.")
        return

    patch = subprocess.run(["git", "diff", "--binary", kit_ref(m), "HEAD", "--", *paths],
                           cwd=ROOT, capture_output=True).stdout
    tmp = Path(tempfile.mkdtemp(prefix="kit-push-"))
    try:
        clone = tmp / "kit"
        git("clone", "--quiet", "--branch", m["branch"], m["upstream"], str(clone), cwd=tmp)
        patch_file = tmp / "kit.patch"
        patch_file.write_bytes(patch)
        git("apply", "--index", "--whitespace=nowarn", str(patch_file), cwd=clone)
        message = args.message or "Kit improvements"
        body = f"{message}\n\nContributed from project: {st['project_name']} ({st['slug']})"
        git("commit", "-q", "-m", body, cwd=clone)
        if args.direct:
            branch = m["branch"]
        else:
            branch = args.branch or f"contrib/{st['slug']}-{dt.datetime.now():%Y%m%d-%H%M}"
            git("checkout", "-q", "-b", branch, cwd=clone)
        git("push", "--quiet", "origin", f"HEAD:{branch}", cwd=clone)
        print(f"Pushed to {m['upstream']} branch '{branch}'.")

        gh_repo = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$", m["upstream"])
        if not args.direct and gh_repo and shutil.which("gh") and not args.no_pr:
            r = subprocess.run(["gh", "pr", "create", "--repo", gh_repo.group(1), "--base", m["branch"],
                                "--head", branch, "--title", message,
                                "--body", f"Contributed from project **{st['project_name']}**.\n\n"
                                          f"```\n{changes}\n```"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            print(r.stdout.strip() or r.stderr.strip())
        print("After it is merged upstream, run `python tools/kit.py pull` here "
              "(and in other projects) to stay in sync.")
    finally:
        rmtree(tmp)


# --------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="turn this kit copy into a new project")
    p.add_argument("--name", required=True, help="human-readable project name")
    p.add_argument("--slug", help="package/repo slug (default: derived from name)")
    p.add_argument("--origin", help="git URL of the new project's own repository")
    p.add_argument("--force", action="store_true", help="re-run init and overwrite skeleton files")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("status", help="show kit version and pending changes")
    p.add_argument("--offline", action="store_true", help="do not fetch upstream")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("pull", help="merge the latest kit into this project")
    p.set_defaults(func=cmd_pull)

    p = sub.add_parser("push", help="contribute kit changes upstream (dry run without --yes)")
    p.add_argument("-m", "--message", help="commit / PR title")
    p.add_argument("--branch", help="upstream branch name (default: contrib/<slug>-<timestamp>)")
    p.add_argument("--direct", action="store_true", help="push straight to the upstream default branch")
    p.add_argument("--no-pr", action="store_true", help="push the branch but do not open a PR")
    p.add_argument("--yes", action="store_true", help="actually push (otherwise dry run)")
    p.set_defaults(func=cmd_push)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
