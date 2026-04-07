#!/usr/bin/env bash
# detect-stack.sh - Auto-detect project technology stack
# Usage: detect-stack.sh [project-dir]
# Output: stack identifier (e.g., "dotnet-desktop", "dotnet-library+scientific-computing")

set -euo pipefail

PROJECT_DIR="${1:-.}"

# Normalize Windows paths to Unix-style
PROJECT_DIR="${PROJECT_DIR//\\//}"

# --- Helper functions ---

has_file() {
  local pattern="$1"
  # Use find with maxdepth to avoid deep traversal
  find "$PROJECT_DIR" -maxdepth 3 -name "$pattern" -print -quit 2>/dev/null | grep -q .
}

has_file_shallow() {
  local pattern="$1"
  find "$PROJECT_DIR" -maxdepth 1 -name "$pattern" -print -quit 2>/dev/null | grep -q .
}

has_dir() {
  local dir="$1"
  [ -d "$PROJECT_DIR/$dir" ]
}

file_contains() {
  local pattern="$1"
  local glob="$2"
  find "$PROJECT_DIR" -maxdepth 3 -name "$glob" -exec grep -l "$pattern" {} + 2>/dev/null | head -1 | grep -q .
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

  # Check for geospatial/scientific keywords in file names
  if ! $SCIENTIFIC; then
    if has_file "*geo*" || has_file "*mag*" || has_file "*survey*" || \
       has_file "*trajectory*" || has_file "*coordinate*" || has_file "*projection*"; then
      SCIENTIFIC=true
    fi
  fi

  # Check for native interop (common in scientific computing)
  if ! $SCIENTIFIC; then
    if file_contains "DllImport" "*.cs" 2>/dev/null || \
       file_contains "ctypes" "*.py" 2>/dev/null; then
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
