# Claude Skills

Custom skills for Claude Code. Each skill installs into `~/.claude/skills/` and
activates automatically when its description matches the task.

## Skills

### persona-review

Technology-aware rotating persona review. Detects the project's technology stack
and runs a tailored code review through independent sub-agent personas:
Implementer, Reviewer, Tester, UI/UX Designer, Security Auditor, and Project
Manager.

Supported stacks: .NET Desktop (WPF, WinForms), .NET libraries and NuGet
packages, ASP.NET web, Node.js and Express APIs, static sites (Astro, Eleventy),
Salesforce (Apex, LWC), and Python tools. Scientific computing is available as
an overlay on top of any of those.

```
/persona-review feature/123-my-branch
/persona-review feature/123-my-branch --stack dotnet-desktop
/persona-review feature/123-my-branch --overlay scientific-computing
/persona-review feature/123-my-branch --rotation 4
```

Every argument is optional. With none, the skill reviews the current branch and
detects the stack itself.

## Install

Run the installer for your platform from the repository root:

```powershell
./install.ps1
```

```bash
./install.sh
```

Both copy every skill under `skills/` into `~/.claude/skills/`, replacing any
earlier copy. Pass `-Destination` or `--destination` to install into a project's
`.claude/` directory instead, and `-WhatIf` or `--dry-run` to preview.

If `~/.claude/skills/` did not exist before you ran the installer, restart
Claude Code once so it starts watching the directory. Later edits are picked up
without a restart. Confirm with `/skills`.

This repository is the source of truth. Do not edit the copies under
`~/.claude/skills/`, because the next install overwrites them.

## Repository layout

```
claude-skills/
  skills/<skill-name>/
    SKILL.md              Entry point: frontmatter and the workflow
    references/           Depth loaded on demand, not at startup
    scripts/              Bundled shell scripts
  install.ps1
  install.sh
```

## License

MIT
