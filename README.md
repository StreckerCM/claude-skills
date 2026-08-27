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
Salesforce (Apex, LWC, Flow), and Python tools. Four overlays add criteria on top of a
detected stack, and more than one can apply at once:

| Overlay | Fires on |
|---|---|
| `entity-framework` | a `DbContext` in the source |
| `blazor` | `.razor` components |
| `scientific-computing` | numerical libraries, domain terms, or non-system native interop |
| `experience-cloud` | Salesforce `experiences/` or `networks/` metadata |
| `accessibility` | not detected: loaded whenever the rotation includes UI/UX |

### Build and test commands

A profile's `build_command` and `test_command` are the usual case for a
stack, not a promise about a given project. Phase 1 checks each one resolves
before handing it to a reviewer, and tells the personas to skip the step when
it does not. A plain Node service, for instance, often has `start` and `test`
and no `build` — passing `npm run build` anyway makes every reviewer open its
review with a build failure that is not real.

### Project conventions

Before launching anything, the skill reads the repository's own `CLAUDE.md`,
`AGENTS.md` or `CONTRIBUTING.md` and injects it verbatim into every persona.
Those files record decisions the project has already made, and they outrank
the review criteria.

This was added after a real run reported a deliberately-removed navigation
link as a silent regression and restored it. The repository's `CLAUDE.md` had
said "do not re-add it" for six weeks. No persona had been told to look.

### Cross-repository dependencies

Phase 1 also looks for the services the code talks to — named in the
conventions file, sitting in a sibling directory, or implied by a `_URL`
environment variable or a `proxy_pass` — and tells every persona which ones
are readable locally.

Reviewers may then read a counterpart to check an assumption, but not to
review it: findings stay about the repository under review. The rule is that
any claim about what something across a network boundary does must either be
checked there or be marked unverified.

This came from a real run. Three reviewers reported a form proxy as having no
rate limit and recommended adding one. The limit existed in the API's own
repository, and the proxy had silently defeated it by rewriting a header, so
every visitor shared one bucket. The recommended fix would have hidden the
breakage rather than repairing it.

### Accessibility

Any profile whose rotation includes `ui-ux-designer` also loads the
`accessibility` overlay, targeting **WCAG 2.2 AA**. Findings cite the success
criterion, so they can be looked up and survive a disagreement.

It leads with the two things reviewers get wrong. Automated tools catch roughly
a third of WCAG failures, so a clean axe or Lighthouse run is a floor and never
a pass — it cannot tell whether alt text is meaningful, whether focus order
matches the visual order, or whether an error is announced. And the first rule
of ARIA is not to use ARIA: incorrect ARIA is worse than none, because it
overrides semantics the browser already had. Stack notes cover web, XAML and
Salesforce separately.

```
/persona-review feature/123-my-branch
/persona-review feature/123-my-branch --stack dotnet-desktop
/persona-review feature/123-my-branch --overlay scientific-computing
/persona-review feature/123-my-branch --rotation 4
/persona-review feature/123-my-branch --fable      # add three deep lenses
/persona-review feature/123-my-branch --issues     # file an issue per fix item
/persona-review feature/123-my-branch --fix        # apply the fix plan
/persona-review feature/123-my-branch --fix --rounds 3   # review, fix, repeat
/persona-review --repo E:/GitHub/OtherProject      # review a different repo
/persona-review --base HEAD~3                      # review the last 3 commits
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
| 3b | Orchestrator files one issue per fix item (`--issues`) | tracker |
| 4 | Implementer, one per non-overlapping file group | **write** |
| 4b | Consolidator, when several Implementers ran | **write** |

Phases 3b and 4 run only when you opt in. Nothing is pushed.

### Rounds

`--rounds n` repeats review and fix up to `n` times, capped at 3. It requires
`--fix`, since re-reviewing unchanged code returns the same findings.

**It never loops until the findings reach zero.** Reviewers are told to report a
finding even when the fix is trivial, and `low` severity covers style and
naming, so that supply never runs out. Each round's fixes are also new code the
next round reviews, so the finding count is not guaranteed to fall. The loop
converges on **no blocking items**, which is the only criterion that can be met.

Any one of these ends it early:

| Stop | Meaning |
|---|---|
| No blocking items | Converged. The success case. |
| No attempted blocking item was resolved | No progress; another round will not help. |
| Build or tests red | Never iterate on your own breakage. |
| A fix has been applied and come back twice | Oscillation: two criteria are in conflict. |
| New blocking items outnumber resolved ones | The loop is generating more work than it clears. |
| An Implementer or the Consolidator failed | The tree is in an unknown state. |

Blocking items are **classified, never just counted**. A second review pass
normally finds pre-existing defects the first one missed, which raises the count
on a branch that is converging. Only items a previous fix failed to resolve, or
caused, count against the loop.

Between rounds the orchestrator carries a **decision ledger** into the next
Project Manager: what was applied, what was rejected, and why. Every agent runs
with fresh context, so without it round 2 reverses round 1's arbitration and the
loop argues with itself while looking productive.

### Issues

`--issues` files one tracker issue per fix item, after triage. The de-duplicated
plan is the right unit: filing per reviewer opens the same defect once per
persona that found it. Issues are keyed by branch and title, so re-reviewing a
branch updates the picture instead of duplicating it, and blocking items are
filed first so they take the lowest numbers. Phase 4 writes `refs #<number>` in
its commits and never `Closes`, so an agent-applied fix cannot silently close a
real defect.

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
