#!/usr/bin/env python3
"""forge.py - Tracker operations for persona-review on GitHub or Gitea.

Usage:
  forge.py detect   <repo>
  forge.py pr       <repo> <branch>
  forge.py issues   <repo> [--label <name>]
  forge.py labels   <repo> <name>:<hex> [<name>:<hex> ...]
  forge.py create   <repo> --title <t> --body-file <path> [--label <name> ...]
  forge.py comment  <repo> <number> --body-file <path>

Every command prints one JSON document on stdout and exits 0 on success.
Errors print {"error": "..."} and exit 1.

`detect` works for any remote. The other commands are for Gitea (and
Forgejo, which serves the same API). On GitHub, use `gh`, which is already
authenticated and handles pagination.

Gitea auth, first match wins:
  1. GITEA_TOKEN in the environment.
  2. The tea CLI's config.yml, using the login whose url matches the remote
     host. The tea binary itself is never run: it can block on a version
     check or a prompt.
The token is never printed.

Standard library only. Runs on Windows (Git Bash or PowerShell), macOS, Linux.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TIMEOUT = 30


class ForgeError(Exception):
    pass


# --- remote ---------------------------------------------------------------

def remote_url(repo: str) -> str:
    repo = repo.replace("\\", "/")
    try:
        out = subprocess.run(
            ["git", "-C", repo, "remote", "get-url", "origin"],
            capture_output=True, text=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ForgeError(f"no 'origin' remote in {repo}") from exc
    return out.stdout.strip()


def parse_remote(url: str) -> tuple[str, str, str]:
    """Return (host, owner, name) for https, ssh:// and scp-style remotes."""
    m = re.match(r"^[a-z+]+://(?:[^@/]+@)?([^/:]+)(?::\d+)?/(.+?)(?:\.git)?/?$", url)
    if not m:
        m = re.match(r"^(?:[^@]+@)?([^:/]+):(.+?)(?:\.git)?/?$", url)
    if not m:
        raise ForgeError(f"cannot parse remote url: {url}")
    host, path = m.group(1), m.group(2)
    parts = path.strip("/").split("/")
    if len(parts) < 2:
        raise ForgeError(f"remote path has no owner/name: {url}")
    return host.lower(), parts[-2], parts[-1]


def http_json(url: str, method: str = "GET", token: str | None = None, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Accept": "application/json", "User-Agent": "persona-review"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        return exc.code, {"message": detail}


def detect(repo: str) -> dict:
    url = remote_url(repo)
    host, owner, name = parse_remote(url)
    result = {"host": host, "owner": owner, "name": name, "slug": f"{owner}/{name}"}
    if host == "github.com":
        return {**result, "forge": "github"}
    try:
        status, body = http_json(f"https://{host}/api/v1/version")
    except (urllib.error.URLError, OSError, ValueError):
        status, body = 0, None
    if status == 200 and isinstance(body, dict) and "version" in body:
        return {**result, "forge": "gitea", "api": f"https://{host}/api/v1",
                "version": body["version"]}
    return {**result, "forge": "unknown"}


# --- gitea auth -----------------------------------------------------------

def tea_config_paths() -> list[Path]:
    home = Path.home()
    paths = []
    if os.environ.get("LOCALAPPDATA"):
        paths.append(Path(os.environ["LOCALAPPDATA"]) / "tea" / "config.yml")
    if os.environ.get("APPDATA"):
        paths.append(Path(os.environ["APPDATA"]) / "tea" / "config.yml")
    if os.environ.get("XDG_CONFIG_HOME"):
        paths.append(Path(os.environ["XDG_CONFIG_HOME"]) / "tea" / "config.yml")
    paths += [
        home / "AppData" / "Local" / "tea" / "config.yml",
        home / ".config" / "tea" / "config.yml",
        home / "Library" / "Application Support" / "tea" / "config.yml",
    ]
    return paths


def token_for(host: str) -> str:
    env = os.environ.get("GITEA_TOKEN")
    if env:
        return env
    for path in tea_config_paths():
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        # Each login is a "- name:" block; read url and token from the same block.
        for block in re.split(r"\n\s*-\s+name:", text):
            url = re.search(r"^\s*url:\s*(\S+)", block, re.M)
            tok = re.search(r"^\s*token:\s*(\S+)", block, re.M)
            if url and tok and urllib.parse.urlparse(url.group(1)).hostname == host:
                return tok.group(1).strip("'\"")
    raise ForgeError(
        f"no Gitea token for {host}: set GITEA_TOKEN or add a tea login for it")


class Gitea:
    def __init__(self, repo: str):
        info = detect(repo)
        if info["forge"] != "gitea":
            raise ForgeError(f"remote is {info['forge']}, not gitea; use gh for github")
        self.api = info["api"]
        self.slug = info["slug"]
        self.token = token_for(info["host"])

    def call(self, method: str, path: str, body=None):
        status, data = http_json(self.api + path, method, self.token, body)
        if status not in (200, 201, 204):
            msg = data.get("message") if isinstance(data, dict) else data
            raise ForgeError(f"{method} {path} -> {status}: {msg}")
        return data

    def paged(self, path: str) -> list:
        sep = "&" if "?" in path else "?"
        out, page = [], 1
        while True:
            batch = self.call("GET", f"{path}{sep}limit=50&page={page}")
            if not batch:
                return out
            out += batch
            if len(batch) < 50:
                return out
            page += 1

    def label_ids(self) -> dict[str, int]:
        return {l["name"]: l["id"] for l in self.paged(f"/repos/{self.slug}/labels")}


# --- commands -------------------------------------------------------------

def cmd_pr(g: Gitea, branch: str) -> dict:
    for pr in g.paged(f"/repos/{g.slug}/pulls?state=open"):
        if pr.get("head", {}).get("ref") == branch:
            return {"number": pr["number"], "url": pr.get("html_url")}
    return {"number": None}


def cmd_issues(g: Gitea, label: str | None) -> list:
    q = "&labels=" + urllib.parse.quote(label) if label else ""
    issues = g.paged(f"/repos/{g.slug}/issues?state=all&type=issues{q}")
    return [{"number": i["number"], "title": i["title"], "state": i["state"],
             "body": i.get("body") or ""} for i in issues]


def cmd_labels(g: Gitea, specs: list[str]) -> dict:
    have = g.label_ids()
    created = []
    for spec in specs:
        name, _, color = spec.rpartition(":")
        if not name or not re.fullmatch(r"[0-9a-fA-F]{6}", color):
            raise ForgeError(f"label spec must be name:rrggbb, got {spec!r}")
        if name not in have:
            lab = g.call("POST", f"/repos/{g.slug}/labels",
                         {"name": name, "color": "#" + color})
            have[name] = lab["id"]
            created.append(name)
    return {"created": created, "labels": sorted(have)}


def cmd_create(g: Gitea, title: str, body_file: str, labels: list[str]) -> dict:
    body = Path(body_file).read_text(encoding="utf-8")
    have = g.label_ids()
    missing = [l for l in labels if l not in have]
    if missing:
        raise ForgeError(f"labels do not exist, run 'labels' first: {missing}")
    issue = g.call("POST", f"/repos/{g.slug}/issues",
                   {"title": title, "body": body, "labels": [have[l] for l in labels]})
    return {"number": issue["number"], "url": issue.get("html_url")}


def cmd_comment(g: Gitea, number: int, body_file: str) -> dict:
    body = Path(body_file).read_text(encoding="utf-8")
    c = g.call("POST", f"/repos/{g.slug}/issues/{number}/comments", {"body": body})
    return {"id": c["id"], "url": c.get("html_url")}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="forge.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("detect"); s.add_argument("repo")
    s = sub.add_parser("pr"); s.add_argument("repo"); s.add_argument("branch")
    s = sub.add_parser("issues"); s.add_argument("repo"); s.add_argument("--label")
    s = sub.add_parser("labels"); s.add_argument("repo"); s.add_argument("specs", nargs="+")
    s = sub.add_parser("create"); s.add_argument("repo")
    s.add_argument("--title", required=True); s.add_argument("--body-file", required=True)
    s.add_argument("--label", action="append", default=[])
    s = sub.add_parser("comment"); s.add_argument("repo"); s.add_argument("number", type=int)
    s.add_argument("--body-file", required=True)
    a = p.parse_args(argv)
    try:
        if a.cmd == "detect":
            out = detect(a.repo)
        else:
            g = Gitea(a.repo)
            if a.cmd == "pr":
                out = cmd_pr(g, a.branch)
            elif a.cmd == "issues":
                out = cmd_issues(g, a.label)
            elif a.cmd == "labels":
                out = cmd_labels(g, a.specs)
            elif a.cmd == "create":
                out = cmd_create(g, a.title, a.body_file, a.label)
            else:
                out = cmd_comment(g, a.number, a.body_file)
    except (ForgeError, OSError, urllib.error.URLError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
