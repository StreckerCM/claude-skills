#!/usr/bin/env python3
"""hotspots.py - Build the hotspot map for a focused review.

Usage:
  hotspots.py --repo <path> --out <run-dir>/hotspots.md
              [--preset <name> ...] [--pattern <regex> ...]
              [--path <pathspec> ...]

Reads the `hotspots:` list from each preset in references/focus/<name>.md
(beside this script's parent), adds any --pattern given, and searches the
tracked files under the --path pathspecs (default: the whole repository).
Vendored, generated and binary files are skipped, as are tests/ unless a
--path names them.

Writes a Markdown index to --out: per pattern, the hit count and every
file:line with the matching line, plus a per-file total. Prints a one-line
summary. Patterns are Python regular expressions, so lookarounds work.

Standard library only.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
SKIP_PARTS = {"node_modules", "dist", "build", "bin", "obj", "vendor", ".venv", "venv",
              "__pycache__", "site-packages", "docs"}
SKIP_SUFFIXES = {".min.js", ".lock", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico",
                 ".pdf", ".zip", ".npy", ".db", ".sqlite", ".pyc", ".woff", ".woff2"}
SOURCE_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".cs", ".sql", ".sh", ".ps1",
                   ".html", ".cls", ".trigger", ".go", ".rs", ".java", ".kt", ".rb", ".php"}
MAX_LINE = 160


def preset_patterns(name: str) -> list[str]:
    path = SKILL_ROOT / "references" / "focus" / f"{name}.md"
    if not path.is_file():
        sys.exit(f"no focus preset named {name!r} (looked for {path})")
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^---\n(.*?)\n---", text, re.S | re.M)
    if not m:
        return []
    out, in_list = [], False
    for line in m.group(1).splitlines():
        if line.startswith("hotspots:"):
            in_list = True
            continue
        if in_list:
            item = re.match(r"^\s+-\s+(.*)$", line)
            if not item:
                break
            value = item.group(1).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                value = value[1:-1].replace("''", "'")
            out.append(value)
    return out


def tracked_files(repo: str, pathspecs: list[str]) -> list[str]:
    r = subprocess.run(["git", "-C", repo, "ls-files", "--", *pathspecs],
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        sys.exit(f"git ls-files failed: {r.stderr.strip()}")
    files = []
    explicit_tests = any(p.startswith("tests") or "/tests" in p for p in pathspecs)
    for f in r.stdout.splitlines():
        parts = set(Path(f).parts)
        low = f.lower()
        if parts & SKIP_PARTS or any(low.endswith(s) for s in SKIP_SUFFIXES):
            continue
        if not explicit_tests and (f.startswith("tests/") or "/tests/" in f):
            continue
        if Path(f).suffix.lower() not in SOURCE_SUFFIXES:
            continue
        files.append(f)
    return files


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="hotspots.py")
    p.add_argument("--repo", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--preset", action="append", default=[])
    p.add_argument("--pattern", action="append", default=[])
    p.add_argument("--pattern-file", action="append", default=[],
                   help="file with one regex per line (# comments allowed). Prefer this "
                        "over --pattern for regexes containing |: a Windows python.bat "
                        "shim splits such arguments.")
    p.add_argument("--path", action="append", default=[])
    a = p.parse_args(argv)

    repo = a.repo.replace("\\", "/")
    patterns: list[str] = []
    for name in a.preset:
        patterns += preset_patterns(name)
    patterns += a.pattern
    for pf in a.pattern_file:
        for line in Path(pf.replace("\\", "/")).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    if not patterns:
        sys.exit("no patterns: pass --preset, --pattern or --pattern-file")
    compiled = []
    for pat in dict.fromkeys(patterns):
        try:
            compiled.append((pat, re.compile(pat)))
        except re.error as exc:
            sys.exit(f"bad pattern {pat!r}: {exc}")

    files = tracked_files(repo, a.path or ["."])
    hits: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    per_file: Counter = Counter()
    for rel in files:
        try:
            text = (Path(repo) / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for pat, rx in compiled:
                if rx.search(line):
                    snippet = line.strip()
                    if len(snippet) > MAX_LINE:
                        snippet = snippet[:MAX_LINE] + "..."
                    hits[pat].append((rel, n, snippet))
                    per_file[rel] += 1

    lines = [
        "# Hotspot map",
        "",
        f"Presets: {', '.join(a.preset) or 'none'}. Extra patterns: {len(a.pattern)}.",
        f"Searched {len(files)} tracked source files"
        f"{' under ' + ', '.join(a.path) if a.path else ''}. Tests are excluded unless a path names them.",
        "",
        "A line can match several patterns. Read every hit's whole function and its callers;",
        "say in your review which hits you read in full.",
        "",
        "## Hits per file",
        "",
        "| File | Hits |",
        "|---|---|",
    ]
    lines += [f"| {f} | {c} |" for f, c in per_file.most_common()]
    for pat, _ in compiled:
        found = hits.get(pat, [])
        lines += ["", f"## `{pat}` ({len(found)} hits)", ""]
        lines += [f"- {f}:{n}: `{s.replace('`', chr(39))}`" for f, n, s in found] or ["- none"]
    out = Path(a.out.replace("\\", "/"))
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    total = sum(len(v) for v in hits.values())
    print(f"{total} hits across {len(per_file)} of {len(files)} files, {len(compiled)} patterns -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
