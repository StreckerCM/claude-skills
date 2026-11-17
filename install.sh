#!/usr/bin/env bash
#
# Install this repository's skills into the Claude Code configuration directory.
#
# Copies every directory under skills/ into ~/.claude/skills/, creating the
# target directory if it does not exist. Existing skills are replaced.
#
# Usage:
#   ./install.sh
#   ./install.sh --destination /path/to/project/.claude
#   ./install.sh --dry-run

set -euo pipefail

usage() {
    cat <<'EOF'
Install the claude-skills skills for Claude Code.

Usage: install.sh [options]

Options:
  -d, --destination DIR  Claude configuration directory. Default: ~/.claude
  -n, --dry-run          Show what would be copied without copying anything.
  -h, --help             Show this message.
EOF
}

destination="${HOME}/.claude"
dry_run=0

while [ $# -gt 0 ]; do
    case "$1" in
        -d|--destination)
            [ $# -ge 2 ] || { echo "Error: $1 requires a directory." >&2; exit 2; }
            destination="$2"
            shift 2
            ;;
        --destination=*)
            destination="${1#*=}"
            shift
            ;;
        -n|--dry-run)
            dry_run=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Error: unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skills_source="${source_dir}/skills"

if [ ! -d "$skills_source" ]; then
    echo "Error: source not found: $skills_source. Run this script from the repository root." >&2
    exit 1
fi

skills_target="${destination}/skills"

run() {
    if [ "$dry_run" -eq 1 ]; then
        echo "What if: $*"
    else
        "$@"
    fi
}

[ -d "$skills_target" ] || run mkdir -p "$skills_target"

installed=()
for skill in "$skills_source"/*/; do
    [ -f "${skill}SKILL.md" ] || continue
    name="$(basename "$skill")"
    run rm -rf "${skills_target:?}/${name}"
    run cp -R "${skill%/}" "${skills_target}/${name}"
    installed+=("$name")
done

if [ "${#installed[@]}" -eq 0 ]; then
    echo "Error: no skills found under $skills_source." >&2
    exit 1
fi

if [ "$dry_run" -eq 1 ]; then
    exit 0
fi

echo "Installed to ${destination}/skills"
for name in "${installed[@]}"; do
    echo "  ${name}/"
done
cat <<'EOF'

Next: restart Claude Code if ~/.claude/skills/ did not exist before, then run
/skills to confirm. No other activation is needed.
EOF
