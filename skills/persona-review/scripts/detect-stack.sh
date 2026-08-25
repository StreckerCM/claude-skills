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

has_file() {
  local pattern="$1"
  find_pruned 3 -name "$pattern" -print -quit | grep -q .
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
  find "$PROJECT_DIR" -mindepth 1 -maxdepth 3 \( "${PRUNE[@]}" \) -prune -o \
    -iname "$pattern" -print -quit 2>/dev/null | grep -q .
}

has_dir() {
  local dir="$1"
  [ -d "$PROJECT_DIR/$dir" ]
}

file_contains() {
  local pattern="$1"
  local glob="$2"
  find_pruned 3 -name "$glob" -exec grep -l "$pattern" {} + | head -1 | grep -q .
}

# Windows system libraries. P/Invoke into these is ordinary desktop plumbing:
# console windows, window handles, the registry. It says nothing about the
# domain. Only interop with a non-system library suggests a native
# computational core, which is what the overlay is trying to find.
SYSTEM_DLLS='kernel32|user32|advapi32|shell32|gdi32|oleaut32|ole32|comctl32|comdlg32|ws2_32|winmm|dwmapi|uxtheme|psapi|version|crypt32|secur32|setupapi|iphlpapi|netapi32|wintrust|userenv|winspool|imm32|dbghelp|ntdll|msvcrt'

has_nonsystem_interop() {
  local glob="$1" pattern="$2"
  find_pruned 3 -name "$glob" -exec grep -h "$pattern" {} + 2>/dev/null \
    | grep -viE "\"($SYSTEM_DLLS)" | grep -q .
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
OVERLAY=""

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
    OVERLAY="scientific-computing"
  fi
fi

# --- Output ---

if [ -n "$OVERLAY" ]; then
  echo "${STACK}+${OVERLAY}"
else
  echo "$STACK"
fi
