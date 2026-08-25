#!/usr/bin/env bash
# detect-base.sh - Determine the base branch to diff a review branch against
# Usage: detect-base.sh [repo-dir]
# Output: branch name (e.g. "main", "master", "development"), or "unknown"
#
# Never assume main. Repositories on master, or with a long-lived integration
# branch, produce an empty diff when the base is wrong, and an empty diff reads
# as a clean review.

set -euo pipefail

REPO_DIR="${1:-.}"
REPO_DIR="${REPO_DIR//\\//}"

git_in() {
  git -C "$REPO_DIR" "$@" 2>/dev/null
}

has_branch() {
  git_in rev-parse --verify --quiet "refs/heads/$1" >/dev/null
}

CURRENT="$(git_in rev-parse --abbrev-ref HEAD || true)"

# 1. The remote's declared default branch is the most reliable signal.
DEFAULT="$(git_in symbolic-ref --quiet --short refs/remotes/origin/HEAD || true)"
DEFAULT="${DEFAULT#origin/}"

# 2. Fall back to whichever conventional branch actually exists.
if [ -z "$DEFAULT" ]; then
  for candidate in main master trunk develop development; do
    if has_branch "$candidate"; then
      DEFAULT="$candidate"
      break
    fi
  done
fi

if [ -z "$DEFAULT" ]; then
  echo "unknown"
  exit 0
fi

# 3. Reviewing the default branch itself means diffing against it is empty.
#    Prefer a parent integration branch when one exists and has a real diff.
if [ -n "$CURRENT" ] && [ "$CURRENT" = "$DEFAULT" ]; then
  for candidate in main master trunk; do
    if [ "$candidate" != "$DEFAULT" ] && has_branch "$candidate"; then
      echo "$candidate"
      exit 0
    fi
  done
fi

echo "$DEFAULT"
