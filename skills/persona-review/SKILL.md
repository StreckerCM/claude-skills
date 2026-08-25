---
name: persona-review
description: Run a technology-aware persona code review. Auto-detects the project's tech stack and launches specialized sub-agent reviewers (Implementer, Reviewer, Tester, UI/UX Designer, Security Auditor, Project Manager), then optionally applies the fixes. Use when asked to review code, run a persona review, or launch sub-agent reviewers.
---

# Persona review

Detect the project's tech stack, load the matching review profile, and run
independent sub-agent personas over the branch.

**Reviewers report. Only the Implementer writes code.** Every persona except the
Implementer is read-only. The Project Manager merges their findings into one
de-duplicated fix plan, and the Implementer applies it. This separation is not
optional: parallel agents editing the same files produce conflicts and duplicate
implementations.

## Skill root

This skill's bundled files live in `~/.claude/skills/persona-review/`. Paths in
this document are relative to that directory. When you pass one to a shell
command, expand it to the full path.

If the skill was installed into a project's `.claude/skills/` instead, use that
directory as the root.

## Arguments

All are optional.

| Argument | Effect |
|---|---|
| `<branch>` | Review this branch. Default: the current branch. |
| `--repo <path>` | Review this repository. Default: the working directory. |
| `--stack <stack>` | Skip detection and use this stack. |
| `--overlay <overlay>` | Add overlay criteria on top of the detected stack. |
| `--rotation <size>` | Run this many reviewers instead of the profile default. |
| `--fable` | Add three deep-review lenses on Fable. Opt-in only. |
| `--fix` | Run Phase 4 and apply the fix plan. |
| `--no-fix` | Stop after the fix plan. Report only. |

Valid stacks: `dotnet-desktop`, `dotnet-library`, `aspnet-web`, `nodejs-api`,
`static-site`, `salesforce`, `python-tools`. Valid overlay:
`scientific-computing`.

Never infer `--fable`. Run it only when the user passes the flag or asks for a
deep or Fable review in words.

## Phase 1: Detect and load

1. **Resolve the repository.** Use `--repo <path>` if given, otherwise the
   working directory. Everything below runs against it, so use `git -C <repo>`
   rather than changing directory. Confirm it is a git repository before going
   further.

   Pass the absolute repository path into every sub-agent prompt. Sub-agents do
   not inherit your working directory, and a reviewer that runs `git diff` in
   the wrong place reports a clean pass on an empty diff.

2. **Resolve the branch.** Use the branch argument if given, otherwise
   `git -C <repo> branch --show-current`. Get the PR number with
   `gh pr list --head <branch> --json number --jq '.[0].number'`. An empty
   result means no PR exists.

3. **Resolve the base branch.** Never assume `main`:

   ```bash
   bash ~/.claude/skills/persona-review/scripts/detect-base.sh <repo>
   ```

   The script prefers the remote's declared default branch, then falls back to
   whichever of `main`, `master`, `trunk`, `develop`, or `development` exists. A
   wrong base produces an empty diff, and an empty diff reads as a clean review.

   If it prints `unknown`, or if `git -C <repo> diff --name-only <base>...HEAD`
   is empty, stop and ask the user for the base branch. Do not review nothing
   and call it clean.

4. **Detect the stack.** If `--stack` was given, use it. Otherwise run:

   ```bash
   bash ~/.claude/skills/persona-review/scripts/detect-stack.sh <repo>
   ```

   The script prints one line, such as `dotnet-desktop` or
   `dotnet-library+scientific-computing`. Split on `+` to separate the base
   stack from the overlay. A `--overlay` argument adds to whatever the script
   detected.

   If the script prints `unknown`, stop and ask the user to pass `--stack`.

5. **Load the profile.** Read `references/profiles/<base-stack>.md`, and
   `references/profiles/<overlay>.md` if an overlay is active. The YAML
   frontmatter gives you `personas`, `rotation_size`, `build_command`, and
   `test_command`.

6. **Resolve the rotation.** Start from the profile's `personas` list. If
   `--rotation <n>` was given, drop reviewers from the **end of this priority
   order** until the list is `n` long:

   ```
   ui-ux-designer  →  tester  →  security-auditor  →  reviewer  →  implementer
   ```

   Drop `ui-ux-designer` first. The Project Manager is not in any profile's
   `personas` list and does not count toward `rotation_size`. It always runs in
   Phase 3, because without it there is no fix plan.

7. **Announce the plan** before launching anything:

   ```
   Starting persona review
   Repository: <absolute repo path>
   Branch: <branch>  (base: <base-branch>)
   Detected stack: <stack> (+ <overlay>)
   Profile: <display_name>
   Reviewers: <list>
   Deep lenses: Architect, Adversary, Skeptic     (only with --fable)
   Build: <build_command>
   Tests: <test_command>
   Fix phase: enabled / report only
   ```

## Phase 2: Review, in parallel, read-only

Sub-agents get fresh context and **cannot read this skill's files**. You must
read each agent template yourself and inject its full text into the Agent tool's
`prompt`. A prompt that tells the sub-agent to go read a file will fail.

Read `references/orchestration.md` for the prompt template and the substitution
steps. Follow it literally.

Launch every reviewer in the rotation concurrently: send them as multiple tool
calls in one message. With `--fable`, launch the three deep lenses in the same
message. They must not receive the standard reviewers' findings, because seeing
that list anchors them to what was already caught.

| Round 2 agents | Template | Model |
|---|---|---|
| Implementer | `references/agents/implementer.md` | sonnet |
| Reviewer | `references/agents/reviewer.md` | opus |
| Tester | `references/agents/tester.md` | sonnet |
| UI/UX Designer | `references/agents/ui-ux-designer.md` | sonnet |
| Security Auditor | `references/agents/security-auditor.md` | opus |
| Architect (`--fable`) | `references/agents/fable-architect.md` | fable |
| Adversary (`--fable`) | `references/agents/fable-adversary.md` | fable |
| Skeptic (`--fable`) | `references/agents/fable-skeptic.md` | fable |

The deep lenses take no `{{STACK_CRITERIA}}` substitution, but every template,
theirs included, needs `{{BASE_BRANCH}}` replaced.

Collect each agent's `### FINDINGS` block. If an agent returns no parsable
block, note it and continue.

## Phase 3: Merge into a fix plan

Launch the Project Manager alone, after every reviewer has finished. Inject
`references/agents/project-manager.md` plus **every findings block from Phase
2**, verbatim, labeled by persona.

It returns a `### FIX PLAN`: findings de-duplicated into fix items, each with a
`scope` of files and a `group` number. Items sharing a file share a group.

Print the summary table, then follow `--fix` or `--no-fix`. With neither flag,
stop here, show the plan, and ask whether to apply it. Do not apply a fix plan
the user has not seen.

## Phase 4: Apply the fixes

Only when the user opted in.

1. **Verify the groups are disjoint.** Two groups sharing a file is a planning
   error. Merge them rather than running them in parallel.
2. **Record the base commit** with `git -C <repo> rev-parse HEAD`. Phase 4's consolidation
   step needs it.
3. **Launch one Implementer per group**, concurrently, using
   `references/agents/implementer-fixer.md` with `{{FIX_GROUP}}` replaced by
   that group's items. One group means one agent and no consolidation.
4. **Consolidate.** If two or more Implementers ran, launch the Consolidator
   from `references/agents/consolidator.md`, giving it the base commit and every
   Implementer's result block including its `new-shared` list. Parallel agents
   cannot see each other, so this is what catches two of them writing the same
   method twice.
5. **Verify.** Run the build and test commands yourself. Report the result
   honestly, including failure.

Nothing is pushed. Leave the commits local for the user to review.

## Phase 5: Report

Print a summary:

```markdown
## Persona review complete

| Persona | Model | Findings | Highest severity |
|---------|-------|----------|------------------|

**Fix plan:** <N> findings merged into <M> items, <B> blocking
**Applied:** <A> of <M>    (only when Phase 4 ran)
**Build:** pass / fail     **Tests:** pass / fail / not-run

**Stack:** <stack>  **Branch:** <branch>  **PR:** #<number>
```

State plainly whether the branch is ready or which items are outstanding. Report
failures and skipped items explicitly; do not describe a partial run as
complete.

Then write the review record to project memory, following the template in
`references/orchestration.md`.

## Error handling

- Stack detection returns `unknown`: ask for `--stack`. Do not guess.
- Base detection returns `unknown`, or the diff is empty: stop and ask. An empty
  diff is not a clean review.
- No PR for the branch: skip every `gh pr comment` step and have each persona
  return its review as text. The findings blocks work the same way.
- A reviewer fails: report which one, continue with the rest, and tell the
  Project Manager that persona is missing.
- The Project Manager fails: show the raw findings and stop. Never build a fix
  plan yourself and never run Phase 4 without one.
- An Implementer fails: keep the other groups' commits, report the failed items
  as unapplied. Do not retry into a dirty tree.
- The build fails in Phase 2: run every review anyway, and flag it at the top of
  the summary.
