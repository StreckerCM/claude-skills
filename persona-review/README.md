# persona-review

Technology-aware rotating persona review skill for Claude Code. Detects your project's tech stack and launches tailored code reviews through independent sub-agent personas.

## Installation

### Quick (per-session, no install)
```bash
claude --plugin-dir "C:/GitHub/claude-skills/persona-review"
```

### Persistent (local marketplace)
```
/plugin marketplace add C:/GitHub/claude-skills
/plugin install persona-review@strecker-skills
```

### Persistent (from GitHub)

Add to your project's `.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "strecker-skills": {
      "source": {
        "source": "github",
        "repo": "StreckerCM/claude-skills"
      }
    }
  },
  "enabledPlugins": {
    "persona-review@strecker-skills": true
  }
}
```

Or interactively:
```
/plugin marketplace add StreckerCM/claude-skills
/plugin install persona-review@strecker-skills
```

## Usage

```
/persona-review feature/123-feature-name                              # auto-detect stack
/persona-review feature/123-feature-name --stack dotnet-desktop       # explicit stack
/persona-review feature/123-feature-name --overlay scientific-computing
/persona-review feature/123-feature-name --rotation 4                 # compact rotation
```

## How It Works

1. **Detects** your project's technology stack from project files (`.sln`, `package.json`, `sfdx-project.json`, etc.)
2. **Loads** a technology-specific profile with tailored review criteria per persona
3. **Launches** each persona as an independent sub-agent with fresh context
4. **Parallelizes** where possible (Implementer, Reviewer, Tester, Security run concurrently)
5. **Project Manager** runs last to summarize all findings

## Supported Stacks

| Stack | Detection Signal | Default Rotation |
|-------|-----------------|-----------------|
| `dotnet-desktop` | `.sln` + `.xaml` files | 6 personas |
| `dotnet-library` | `.sln` + `.nupkg`/`.nuspec` | 4 personas |
| `aspnet-web` | `.sln` + `web.config`/`WebApplication` | 6 personas |
| `nodejs-api` | `package.json` + `express` dep | 4 personas |
| `static-site` | `astro.config.*` or `eleventy.config.*` | 4 personas |
| `salesforce` | `sfdx-project.json` or `force-app/` | 6 personas |
| `python-tools` | `*.py` + `requirements.txt`/`pyproject.toml` | 4 personas |
| `scientific-computing` | Math namespaces, geo/mag keywords | Overlay (additive) |

## Personas

| Persona | Model | Role |
|---------|-------|------|
| Implementer | Sonnet | Code quality, pattern compliance, task completion |
| Reviewer | Opus | Bug detection, code review, maintainability |
| Tester | Sonnet | Test coverage, edge cases, test quality |
| UI/UX Designer | Sonnet | Interface design, accessibility, usability |
| Security Auditor | Opus | Vulnerability detection, input validation, secrets |
| Project Manager | Haiku | Requirements tracking, progress, risk assessment |

## Profiles

Each profile defines:
- Which personas are included in the rotation
- Stack-specific review criteria per persona
- Build/test commands
- Framework-specific patterns to check

See `profiles/` for all profile definitions.
