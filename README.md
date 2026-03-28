# Claude Skills

A collection of custom Claude Code skills for AI-assisted software development.

## Skills

### [persona-review](persona-review/)

Technology-aware rotating persona review system. Auto-detects your project's technology stack and runs tailored code reviews through specialized sub-agent personas (Implementer, Reviewer, Tester, UI/UX Designer, Security Auditor, Project Manager).

**Supported stacks:**
- .NET Desktop (WPF/WinForms)
- .NET Libraries/NuGet
- ASP.NET Web
- Node.js/Express API
- Static Sites (Astro/Eleventy)
- Salesforce (Apex/LWC)
- Python Tools
- Scientific Computing (overlay)

**Usage:**
```
/persona-review feature/123-feature-name                              # auto-detect stack
/persona-review feature/123-feature-name --stack dotnet-desktop       # explicit stack
/persona-review feature/123-feature-name --overlay scientific-computing
```

## Installation

### Option 1: Quick development (per-session)

Load a skill directly without installing, for testing or development:
```bash
claude --plugin-dir "C:/GitHub/claude-skills/persona-review"
```

### Option 2: Local marketplace (persistent)

Register this repo as a local marketplace, then install skills from it:
```
/plugin marketplace add C:/GitHub/claude-skills
/plugin install persona-review@strecker-skills
```

### Option 3: From GitHub (persistent)

Add the marketplace from GitHub in your project's `.claude/settings.json`:
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

## Adding New Skills

Create a new directory at the repo root with:
```
<skill-name>/
  .claude-plugin/plugin.json
  commands/<skill-name>.md
  README.md
```

See [persona-review/](persona-review/) for a complete example.

## License

MIT
