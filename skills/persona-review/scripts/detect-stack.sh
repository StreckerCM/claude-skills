#!/usr/bin/env bash
# detect-stack.sh - Auto-detect project technology stack
# Usage: detect-stack.sh [project-dir]
# Output: stack identifier (e.g., "dotnet-desktop", "dotnet-library+scientific-computing")

set -euo pipefail

PROJECT_DIR="${1:-.}"

# Normalize Windows paths to Unix-style
PROJECT_DIR="${PROJECT_DIR//\\//}"

# --- Helper functions ---

# Directories that hold code the project did not write. Scanning them produces
# false positives: numpy inside .venv/Lib/site-packages is a transitive
# dependency of half the Python ecosystem, not evidence of scientific computing.
PRUNE=(
  -name .git -o -name .venv -o -name venv -o -name env
  -o -name node_modules -o -name site-packages -o -name __pycache__
  -o -name .tox -o -name .mypy_cache -o -name .pytest_cache
  -o -name bin -o -name obj -o -name dist -o -name build
  -o -name packages -o -name vendor -o -name .superpowers
)

# find, with vendor directories pruned before any test is applied.
find_pruned() {
  local depth="$1"; shift
  find "$PROJECT_DIR" -maxdepth "$depth" \( "${PRUNE[@]}" \) -prune -o "$@" 2>/dev/null
}

# Depth 5 reaches src/<Project>/<Area>/<Sub>/file.ext, which is the common .NET
# and Salesforce layout. Depth 3 stopped at the project directory and missed it.
# Measured cost of the extra two levels is about 60ms per repository, against a
# review that then spawns several opus agents.
has_file() {
  local pattern="$1" out
  out=$(find_pruned 5 -name "$pattern" -print -quit 2>/dev/null || true)
  [ -n "$out" ]
}

has_file_shallow() {
  local pattern="$1"
  find "$PROJECT_DIR" -maxdepth 1 -name "$pattern" -print -quit 2>/dev/null | grep -q .
}

# Case-insensitive name probe. .NET and Salesforce use PascalCase, so a
# case-sensitive -name misses Coordinate.cs and Projections/ entirely, which
# made the filename rules below dead for those stacks.
#
# -mindepth 1 keeps the repository's own directory out of the match: a repo
# checked out into a folder called Survey should not be classified by that.
has_file_iname() {
  local pattern="$1"
  local out
  out=$(find "$PROJECT_DIR" -mindepth 1 -maxdepth 5 \( "${PRUNE[@]}" \) -prune -o \
    -iname "$pattern" -print -quit 2>/dev/null || true)
  [ -n "$out" ]
}

has_dir() {
  local dir="$1"
  [ -d "$PROJECT_DIR/$dir" ]
}

# Salesforce metadata directories sit under force-app/main/default and other
# package directories, so their depth varies by project layout.
has_dir_anywhere() {
  local dir="$1" out
  out=$(find_pruned 6 -type d -name "$dir" -print -quit 2>/dev/null || true)
  [ -n "$out" ]
}

# These probes capture output instead of piping into head or grep -q.
#
# Under `set -o pipefail`, a downstream reader that closes the pipe early
# sends SIGPIPE to grep, and the pipeline reports failure even though the
# match succeeded. The failure is size-dependent: with few files grep finishes
# before the reader closes and the probe works, so it passes on small
# repositories and silently returns false on large ones.
file_contains() {
  local pattern="$1" glob="$2" out
  out=$(find_pruned 5 -name "$glob" -exec grep -l "$pattern" {} + 2>/dev/null || true)
  [ -n "$out" ]
}

# Windows system libraries. P/Invoke into these is ordinary desktop plumbing:
# console windows, window handles, the registry. It says nothing about the
# domain. Only interop with a non-system library suggests a native
# computational core, which is what the overlay is trying to find.
SYSTEM_DLLS='kernel32|user32|advapi32|shell32|gdi32|oleaut32|ole32|comctl32|comdlg32|ws2_32|winmm|dwmapi|uxtheme|psapi|version|crypt32|secur32|setupapi|iphlpapi|netapi32|wintrust|userenv|winspool|imm32|dbghelp|ntdll|msvcrt'

has_nonsystem_interop() {
  local glob="$1" pattern="$2" hits
  hits=$(find_pruned 5 -name "$glob" -exec grep -h "$pattern" {} + 2>/dev/null || true)
  [ -n "$hits" ] || return 1
  printf "%s" "$hits" | grep -qviE "\"($SYSTEM_DLLS)"
}

package_has_dep() {
  local dep="$1"
  local pkg="$PROJECT_DIR/package.json"
  if [ -f "$pkg" ]; then
    grep -q "\"$dep\"" "$pkg" 2>/dev/null
  else
    return 1
  fi
}

# --- Stack detection (priority order) ---

STACK=""
OVERLAYS=""

add_overlay() {
  case " $OVERLAYS " in
    *" $1 "*) ;;
    *) OVERLAYS="${OVERLAYS:+$OVERLAYS }$1" ;;
  esac
}

# Salesforce (check early - very distinctive signals)
if has_file_shallow "sfdx-project.json" || has_dir "force-app"; then
  STACK="salesforce"

# .NET projects (check for .sln or .csproj)
elif has_file "*.sln" || has_file "*.csproj"; then

  # ASP.NET Web - check for web indicators
  if has_file "web.config" || has_file "*.cshtml" || \
     file_contains "WebApplication" "Program.cs" || \
     file_contains "WebApplication" "Startup.cs" || \
     file_contains "Microsoft.AspNetCore" "*.csproj"; then
    STACK="aspnet-web"

  # .NET Desktop - check for XAML (WPF) or WinForms indicators
  elif has_file "*.xaml" || \
       file_contains "System.Windows.Forms" "*.csproj" || \
       file_contains "Microsoft.WindowsDesktop.App" "*.csproj" || \
       file_contains "UseWPF" "*.csproj" || \
       file_contains "UseWindowsForms" "*.csproj"; then
    STACK="dotnet-desktop"

  # .NET Library - no UI, likely a library/NuGet package
  else
    STACK="dotnet-library"
  fi

# Node.js / JavaScript projects
elif has_file_shallow "package.json"; then

  # Astro static site
  if has_file_shallow "astro.config.*"; then
    STACK="static-site"

  # Eleventy static site
  elif has_file_shallow ".eleventy.js" || has_file_shallow "eleventy.config.*"; then
    STACK="static-site"

  # Express API
  elif package_has_dep "express"; then
    STACK="nodejs-api"

  # Generic Node.js - default to static-site if no server framework
  else
    STACK="nodejs-api"
  fi

# Python projects
elif has_file_shallow "requirements.txt" || has_file_shallow "pyproject.toml" || \
     has_file_shallow "setup.py" || has_file_shallow "Pipfile"; then
  STACK="python-tools"

# Fallback
else
  STACK="unknown"
fi

# --- Experience Cloud overlay detection (Salesforce only) ---

# An Experience Cloud site puts org data on the public internet, so it carries
# a security surface no internal-only org has. Detect it rather than taxing
# every Salesforce review with guest-user criteria that do not apply.
if [ "$STACK" = "salesforce" ]; then
  if has_dir_anywhere "experiences" || has_dir_anywhere "networks"; then
    add_overlay "experience-cloud"
  fi
fi

# --- .NET overlay detection ---

# Entity Framework and Blazor are large enough surfaces to review in their own
# right, and neither is tied to one stack: a desktop app can use EF, and Blazor
# can be hosted from more than one project type. Detect them rather than
# taxing every WebForms or MVC review with criteria that do not apply.
case "$STACK" in
  aspnet-web|dotnet-desktop|dotnet-library)
    if file_contains "DbContext" "*.cs"; then
      add_overlay "entity-framework"
    fi
    if has_file "*.razor"; then
      add_overlay "blazor"
    fi
    ;;
esac

# --- Scientific computing overlay detection ---

if [ "$STACK" != "unknown" ] && [ "$STACK" != "salesforce" ] && [ "$STACK" != "static-site" ]; then
  SCIENTIFIC=false

  # Check for math/science namespaces
  if file_contains "System.Numerics" "*.cs" 2>/dev/null || \
     file_contains "numpy" "*.py" 2>/dev/null || \
     file_contains "scipy" "*.py" 2>/dev/null; then
    SCIENTIFIC=true
  fi

  # Check for geospatial and scientific domain terms in file names.
  #
  # These are deliberately specific. Bare *geo* and *mag* look reasonable and
  # are not: *mag* matches images, og-image.png, and image-loader.js, so every
  # web project with an assets folder was classified as scientific computing.
  if ! $SCIENTIFIC; then
    for term in geomag magnetic geodetic geodes survey trajectory \
                coordinate projection ellipsoid datum; do
      if has_file_iname "*${term}*"; then
        SCIENTIFIC=true
        break
      fi
    done
  fi

  # Check for native interop into a non-system library. A bare DllImport is
  # not a signal: kernel32 and user32 appear in ordinary Windows apps that
  # have nothing to do with scientific computing.
  if ! $SCIENTIFIC; then
    if has_nonsystem_interop "*.cs" "DllImport" || \
       has_nonsystem_interop "*.py" "ctypes"; then
      SCIENTIFIC=true
    fi
  fi

  if $SCIENTIFIC; then
    add_overlay "scientific-computing"
  fi
fi

# --- Output ---

if [ -n "$OVERLAYS" ]; then
  echo "${STACK}+$(echo "$OVERLAYS" | tr ' ' '+')"
else
  echo "$STACK"
fi
