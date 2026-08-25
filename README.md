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
/persona-review feature/123-my-branch --fable      # add three deep lenses
/persona-review feature/123-my-branch --fix        # apply the fix plan
```

Every argument is optional. With none, the skill reviews the current branch,
detects the stack, and stops at the fix plan for you to approve.

**Reviewers report. Only the Implementer writes code.** Every persona except the
Implementer is read-only, which keeps parallel agents from conflicting on the
same files. The flow:

| Phase | Agents | Access |
|---|---|---|
| 2 | Reviewers, in parallel | read-only |
| 3 | Project Manager: merge and de-duplicate into one fix plan | read-only |
| 4 | Implementer, one per non-overlapping file group | **write** |
| 4b | Consolidator, when several Implementers ran | **write** |

Phase 4 runs only when you opt in. Nothing is pushed.

### Deep review

`--fable` adds three lenses on Fable, aimed at what a stack checklist
structurally cannot catch. Use it when you suspect the standard rotation is
missing something.

| Lens | Asks |
|---|---|
| Architect | Is this the right shape? Wrong abstractions, misplaced responsibility, coupling |
| Adversary | What breaks this? Boundaries, partial failure, concurrency, scale |
| Skeptic | Is this the right change at all? Cause versus symptom, and what it costs |

They run blind to the standard reviewers' findings, so that list cannot anchor
them. It is opt-in and never inferred.

### Duplicate functionality

Parallel agents cannot see each other, so two of them can independently write
the same method. Three defenses: the Project Manager partitions fixes by file so
overlapping work never runs concurrently, the Reviewer carries standing
duplicate-detection criteria, and the Consolidator runs after parallel fixes to
merge anything that slipped through.

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
