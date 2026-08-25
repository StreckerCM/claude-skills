---
name: persona-review
description: Run a technology-aware persona code review. Auto-detects the project's tech stack and launches specialized sub-agent reviewers (Implementer, Reviewer, Tester, UI/UX Designer, Security Auditor, Project Manager). Use when asked to review code, run a persona review, or launch sub-agent reviewers.
---

# Persona review

Detect the project's tech stack, load the matching review profile, and launch
independent sub-agent personas to review the code.

## Skill root

This skill's bundled files live in `~/.claude/skills/persona-review/`. Paths in
this document are relative to that directory. When you pass one to a shell
command, expand it to the full path.

If the skill was installed into a project's `.claude/skills/` instead, use that
directory as the root.

## Arguments

All are optional. The user passes them after the skill name.

| Argument | Effect |
|---|---|
| `<branch>` | Review this branch. Default: the current branch. |
| `--stack <stack>` | Skip detection and use this stack. |
| `--overlay <overlay>` | Add overlay criteria on top of the detected stack. |
| `--rotation <size>` | Run this many personas instead of the profile default. |

Valid stacks: `dotnet-desktop`, `dotnet-library`, `aspnet-web`, `nodejs-api`,
`static-site`, `salesforce`, `python-tools`. Valid overlay:
`scientific-computing`.

## Phase 1: Detect and load

1. **Resolve the branch.** Use the branch argument if given, otherwise
   `git branch --show-current`. Get the PR number with
   `gh pr list --head <branch> --json number --jq '.[0].number'`. An empty
   result means no PR exists.

2. **Detect the stack.** If `--stack` was given, use it. Otherwise run:

   ```bash
   bash ~/.claude/skills/persona-review/scripts/detect-stack.sh .
   ```

   The script prints one line, such as `dotnet-desktop` or
   `dotnet-library+scientific-computing`. Split on `+` to separate the base
   stack from the overlay. A `--overlay` argument adds to whatever the script
   detected.

   If the script prints `unknown`, stop and ask the user to pass `--stack`.

3. **Load the profile.** Read `references/profiles/<base-stack>.md`, and
   `references/profiles/<overlay>.md` if an overlay is active. The YAML
   frontmatter gives you `personas`, `rotation_size`, `build_command`, and
   `test_command`. `--rotation` overrides `rotation_size` by truncating the
   `personas` list.

4. **Announce the plan** before launching anything:

   ```
   Starting persona review on branch: <branch>
   Detected stack: <stack> (+ <overlay>)
   Profile: <display_name>
   Personas: <list>
   Build: <build_command>
   Tests: <test_command>
   ```

## Phase 2: Launch the personas

Sub-agents get fresh context and **cannot read this skill's files**. You must
read each agent template yourself and inject its full text into the Agent tool's
`prompt`. A prompt that tells the sub-agent to go read a file will fail.

Read `references/orchestration.md` for the prompt template and the exact
substitution steps. Follow it literally.

Launch order:

- **Round 1, in parallel:** Implementer, Reviewer, Tester, UI/UX Designer,
  Security Auditor — whichever are in the rotation. Send them as multiple tool
  calls in one message so they run concurrently.
- **Round 2, after Round 1 finishes:** Project Manager, if in the rotation. It
  reads the other reviews, so it cannot run in parallel with them.

## Phase 3: Report

Print a summary table:

```markdown
## Persona review complete

| Persona | Model | Status | Key findings |
|---------|-------|--------|--------------|
| Implementer | sonnet | Clean | <summary> |

**Stack:** <stack>  **Branch:** <branch>  **PR:** #<number>
```

State plainly whether the review is clean or which items are outstanding.

Then write the review record to project memory, following the template in
`references/orchestration.md`.

## Error handling

- Detection returns `unknown`: ask for `--stack`. Do not guess.
- No PR for the branch: skip the `gh pr comment` step and have each persona
  return its review as text instead.
- A sub-agent fails: report which one, continue with the rest.
- The build fails: run every review anyway, and flag the build failure at the
  top of the summary.
