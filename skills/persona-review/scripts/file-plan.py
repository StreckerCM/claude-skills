#!/usr/bin/env python3
"""file-plan.py - File a persona-review FIX PLAN as tracker issues.

Usage:
  file-plan.py --repo <path> --plan <run-dir>/plan.md --branch <branch>
               --scope "<one-line scope>" [--date YYYY-MM-DD] [--dry-run]

Reads the `### FIX PLAN` block the Project Manager wrote, and for every item
with `issue: yes`:
  - builds the body from the template in references/orchestration.md,
  - skips it when an issue carrying the same fix key already exists,
  - files blocking items first, then the rest in plan order.

Creates any missing labels first. Works on GitHub through `gh` (already
authenticated) and on Gitea or Forgejo through forge.py beside this script.

Prints a JSON object mapping each fix id to its issue number and whether it
was created or already tracked, and writes the same object to issues.json
beside the plan. With --dry-run it files nothing and prints what it would do.

Stops at the first failed create and reports exactly what was filed, so a
retry does not duplicate anything: the filed items are then already tracked.

Standard library only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FORGE = HERE / "forge.py"

LABELS = {
    "persona-review": "5319e7",
    "severity:high": "d93f0b",
    "severity:medium": "fbca04",
    "severity:low": "c2e0c6",
    "blocking": "b60205",
}
EVIDENCE = {
    "observed": "observed - run and seen",
    "traced": "traced - followed in source",
    "asserted": "asserted - not verified",
}
REQUIRED = ("id", "title", "detail", "fix", "severity", "evidence", "scope", "group")


class FileError(Exception):
    pass


# --- plan -----------------------------------------------------------------

def parse_plan(text: str) -> list[dict]:
    """Parse '- id:' items with two-space-indented 'key: value' fields.

    A field value that wraps onto unindented-by-key continuation lines is
    joined with a space, so a plan with long wrapped lines still parses.
    """
    start = text.find("### FIX PLAN")
    if start < 0:
        raise FileError("no '### FIX PLAN' block in the plan file")
    items: list[dict] = []
    cur: dict | None = None
    last: str | None = None
    for line in text[start:].splitlines()[1:]:
        if line.startswith("### ") or line.strip() == "```":
            if items:
                break
            continue
        if line.startswith("- id:"):
            cur = {"id": line.split(":", 1)[1].strip()}
            items.append(cur)
            last = "id"
            continue
        m = re.match(r"^  (\w+):\s?(.*)$", line)
        if cur is not None and m:
            last = m.group(1)
            cur[last] = m.group(2).strip()
        elif cur is not None and last and line.strip():
            cur[last] = f"{cur[last]} {line.strip()}".strip()
    if not items:
        raise FileError("the FIX PLAN block has no items")
    bad = {i.get("id", "?"): [k for k in REQUIRED if k not in i] for i in items}
    bad = {k: v for k, v in bad.items() if v}
    if bad:
        raise FileError(f"items missing fields: {bad}")
    for i in items:
        i["blocking"] = i.get("blocking", "false").strip().lower() == "true"
        i["issue"] = i.get("issue", "yes").strip().lower().startswith("yes")
        i["severity"] = i["severity"].strip().lower()
    return items


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower())[:60].strip("-")


def fix_key(branch: str, title: str) -> str:
    return f"{branch}/{slug(title)}"


def render_body(item: dict, branch: str, scope_line: str, date: str, total: int) -> str:
    ev = re.split(r"[\s,;(]", item["evidence"].strip(), maxsplit=1)[0].lower()
    files = " ".join(f"`{f.strip()}`" for f in item["scope"].split(",") if f.strip())
    lines = [
        f"<!-- persona-review-key: {fix_key(branch, item['title'])} -->",
        f"> Raised by an automated persona review of `{branch}` on {date}.",
        f"> Scope: {scope_line}",
        f"> Fix plan item **{item['id']}**, group {item['group']}.",
        "",
        "| | |",
        "|---|---|",
        f"| **Severity** | {item['severity']} |",
        f"| **Blocking** | {'yes, fix before merge' if item['blocking'] else 'no'} |",
        f"| **Scope** | {files} |",
        f"| **Reported by** | {item.get('sources', '')} |",
        f"| **Evidence** | {EVIDENCE.get(ev, item['evidence'])} |",
        "",
        "## What is wrong",
        "",
        item["detail"],
        "",
        "## Proposed fix",
        "",
        item["fix"],
        "",
    ]
    if ev in ("traced", "asserted"):
        lines += [
            "> **The mechanism above has not been observed failing.** The problem may still",
            "> be real while this explanation of it is wrong. Reproduce it before fixing —",
            "> write the failing test first, or add a probe and watch it fire. A fix applied",
            "> to a wrong mechanism reads correctly, closes the issue, and changes nothing.",
            "",
        ]
    lines += [
        "---",
        "",
        "<sub>Generated by the `persona-review` skill. Reviewers report; they do not",
        "change code. Findings from every persona were merged and de-duplicated by the",
        f"Project Manager into {total} fix items. Verify before acting.</sub>",
    ]
    return "\n".join(lines)


def labels_for(item: dict) -> list[str]:
    sev = "high" if item["severity"] == "critical" else item["severity"]
    if f"severity:{sev}" not in LABELS:
        sev = "low"
    out = ["persona-review", f"severity:{sev}"]
    if item["blocking"]:
        out.append("blocking")
    return out


# --- trackers -------------------------------------------------------------

def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")


def forge_json(*args: str):
    r = run([sys.executable, str(FORGE), *args])
    try:
        data = json.loads(r.stdout) if r.stdout.strip() else {"error": r.stderr.strip()}
    except json.JSONDecodeError:
        data = {"error": r.stdout.strip()[:300]}
    if r.returncode != 0:
        raise FileError(f"forge.py {args[0]}: {data.get('error', data)}")
    return data


class GitHub:
    def __init__(self, slug_: str):
        self.slug = slug_
        r = run(["gh", "auth", "status"])
        if r.returncode != 0:
            raise FileError("gh auth status failed; run 'gh auth login'")

    def existing_keys(self) -> dict[str, int]:
        r = run(["gh", "issue", "list", "--repo", self.slug, "--label", "persona-review",
                 "--state", "all", "--limit", "1000", "--json", "number,body"])
        if r.returncode != 0:
            # The label may not exist yet, which means nothing is tracked.
            if "not found" in (r.stderr or "").lower():
                return {}
            raise FileError(f"gh issue list: {r.stderr.strip()}")
        return keys_from(json.loads(r.stdout or "[]"))

    def ensure_labels(self) -> None:
        for name, color in LABELS.items():
            r = run(["gh", "label", "create", name, "--color", color, "--repo", self.slug])
            if r.returncode != 0 and "already exists" not in (r.stderr or ""):
                raise FileError(f"gh label create {name}: {r.stderr.strip()}")

    def create(self, title: str, body_file: Path, labels: list[str]) -> int:
        r = run(["gh", "issue", "create", "--repo", self.slug, "--title", title,
                 "--body-file", str(body_file), "--label", ",".join(labels)])
        if r.returncode != 0:
            raise FileError(f"gh issue create: {r.stderr.strip()}")
        m = re.search(r"/issues/(\d+)", r.stdout)
        if not m:
            raise FileError(f"could not read the issue number from: {r.stdout.strip()}")
        return int(m.group(1))


class Gitea:
    def __init__(self, repo: str):
        self.repo = repo

    def existing_keys(self) -> dict[str, int]:
        return keys_from(forge_json("issues", self.repo, "--label", "persona-review"))

    def ensure_labels(self) -> None:
        forge_json("labels", self.repo, *(f"{n}:{c}" for n, c in LABELS.items()))

    def create(self, title: str, body_file: Path, labels: list[str]) -> int:
        args = ["create", self.repo, "--title", title, "--body-file", str(body_file)]
        for lab in labels:
            args += ["--label", lab]
        return int(forge_json(*args)["number"])


def keys_from(issues: list[dict]) -> dict[str, int]:
    keys: dict[str, int] = {}
    for i in issues:
        m = re.search(r"persona-review-key:\s*(\S+)", i.get("body") or "")
        if m:
            keys.setdefault(m.group(1), i["number"])
    return keys


# --- main -----------------------------------------------------------------

def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="file-plan.py")
    p.add_argument("--repo", required=True)
    p.add_argument("--plan", required=True)
    p.add_argument("--branch", required=True)
    p.add_argument("--scope", required=True, help="one line: what was reviewed")
    p.add_argument("--date", default=dt.date.today().isoformat())
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)

    repo = a.repo.replace("\\", "/")
    plan_path = Path(a.plan.replace("\\", "/"))
    try:
        items = parse_plan(plan_path.read_text(encoding="utf-8"))
        info = forge_json("detect", repo)
        if info["forge"] == "github":
            tracker = GitHub(info["slug"])
        elif info["forge"] == "gitea":
            tracker = Gitea(repo)
        else:
            raise FileError(f"remote host {info.get('host')} is neither GitHub nor Gitea")

        total = len(items)
        todo = [i for i in items if i["issue"]]
        order = sorted(todo, key=lambda i: (not i["blocking"], todo.index(i)))
        tracked = tracker.existing_keys()

        result: dict[str, dict] = {}
        pending = []
        for it in order:
            key = fix_key(a.branch, it["title"])
            if key in tracked:
                result[it["id"]] = {"issue": tracked[key], "status": "already-tracked"}
            else:
                pending.append(it)

        if a.dry_run:
            print(json.dumps({
                "forge": info["forge"], "slug": info["slug"], "items": total,
                "to_file": [i["id"] for i in pending],
                "blocking": sum(i["blocking"] for i in pending),
                "already_tracked": result,
                "not_issues": [i["id"] for i in items if not i["issue"]],
            }, indent=1))
            return 0

        if pending:
            tracker.ensure_labels()
        failed = None
        with tempfile.TemporaryDirectory() as tmp:
            for it in pending:
                body_file = Path(tmp) / f"{it['id']}.md"
                body_file.write_text(
                    render_body(it, a.branch, a.scope, a.date, total), encoding="utf-8")
                try:
                    num = tracker.create(f"{it['id']}: {it['title']}", body_file, labels_for(it))
                except FileError as exc:
                    failed = {"id": it["id"], "error": str(exc)}
                    break
                result[it["id"]] = {"issue": num, "status": "created"}
    except (FileError, OSError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1

    out = {"issues": result}
    if failed:
        out["failed"] = failed
        out["not_attempted"] = [i["id"] for i in pending if i["id"] not in result
                                and i["id"] != failed["id"]]
    (plan_path.parent / "issues.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
