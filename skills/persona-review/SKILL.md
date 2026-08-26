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
| `--base <ref>` | Diff against this ref instead of the detected base branch. |
| `--stack <stack>` | Skip detection and use this stack. |
| `--overlay <overlay>` | Add overlay criteria on top of the detected stack. |
| `--rotation <size>` | Run this many reviewers instead of the profile default. |
| `--fable` | Add three deep-review lenses on Fable. Opt-in only. |
| `--issues` | File one tracker issue per fix item after triage. Opt-in only. |
| `--fix` | Run Phase 4 and apply the fix plan. |
| `--rounds <n>` | Repeat review and fix up to `n` times. Default 1. Maximum 3. |
| `--no-fix` | Stop after the fix plan. Report only. |

Valid stacks: `dotnet-desktop`, `dotnet-library`, `aspnet-web`, `nodejs-api`,
`static-site`, `salesforce`, `python-tools`.

Valid overlays: `scientific-computing`, `entity-framework`, `blazor`, and
`experience-cloud`. More than one can apply at once. `accessibility` is also
an overlay, but it is loaded from the rotation rather than detected.

`--rounds` above 1 requires `--fix`. Reviewing unchanged code a second time
returns the same findings, so a round without a fix phase is wasted work.

Never infer `--fable` or `--issues`. Run either only when the user passes the
flag or asks for it in words. `--issues` writes to a real tracker, and an issue
can be closed but never deleted.

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

3. **Resolve the base.** If `--base <ref>` was given, use it and skip detection.
   Any git ref works: a branch, a tag, a commit sha, or `HEAD~4`. Otherwise:

   ```bash
   bash ~/.claude/skills/persona-review/scripts/detect-base.sh <repo>
   ```

   The script prefers the remote's declared default branch, then falls back to
   whichever of `main`, `master`, `trunk`, `develop`, or `development` exists. A
   wrong base produces an empty diff, and an empty diff reads as a clean review.

   Then confirm there is something to review:

   ```bash
   git -C <repo> diff --name-only <base>...HEAD
   ```

   If that is empty, or detection printed `unknown`, **stop and offer
   `--base`**. The common cause is a repository sitting on its own default
   branch with no feature branch, where the base and the branch are the same
   ref: there is no diff to review, but recent commits are still reviewable.
   Show the last few commits and suggest a concrete range, such as
   `--base HEAD~3`, rather than asking an open question. Never review nothing
   and call it clean.

4. **Detect the stack.** If `--stack` was given, use it. Otherwise run:

   ```bash
   bash ~/.claude/skills/persona-review/scripts/detect-stack.sh <repo>
   ```

   The script prints one line, such as `dotnet-desktop` or
   `aspnet-web+entity-framework+blazor`. Split on `+`: the first field is the
   base stack and **every remaining field is an overlay**. A project can carry
   several. A `--overlay` argument adds to whatever the script detected.

   If the script prints `unknown`, stop and ask the user to pass `--stack`.

5. **Read the project's own conventions.** Look for `CLAUDE.md`, `AGENTS.md`,
   `CONTRIBUTING.md` and `.cursorrules` in the repository root, and any
   `CLAUDE.md` inside a directory the diff touches. Read every one you find.

   These outrank your criteria. A profile says what good code looks like in
   general; this file says what this project has already decided. A reviewer
   without it reports deliberate choices as defects, and the fix phase then
   reverses them.

   Inject the contents into every sub-agent prompt, verbatim, and say plainly
   that it records decisions the project has already made. If no such file
   exists, say so in the prompt rather than leaving it out silently, so a
   reviewer knows the absence is real and not an omission.

6. **Load the profile.** Read `references/profiles/<base-stack>.md`, then
   `references/profiles/<overlay>.md` for each active overlay.

   Also load `references/profiles/accessibility.md` whenever
   `ui-ux-designer` is in the rotation. It is not detected from the code:
   any project with a user interface has an accessibility surface, so the
   rotation is the condition. The YAML
   frontmatter gives you `personas`, `rotation_size`, `build_command`, and
   `test_command`.

7. **Resolve the rotation.** Start from the profile's `personas` list. If
   `--rotation <n>` was given, drop reviewers from the **end of this priority
   order** until the list is `n` long:

   ```
   ui-ux-designer  →  tester  →  security-auditor  →  reviewer  →  implementer
   ```

   Drop `ui-ux-designer` first. The Project Manager is not in any profile's
   `personas` list and does not count toward `rotation_size`. It always runs in
   Phase 3, because without it there is no fix plan.

8. **Announce the plan** before launching anything:

   ```
   Starting persona review
   Repository: <absolute repo path>
   Branch: <branch>  (base: <base-branch>)
   Detected stack: <stack> (+ <overlay>)
   Profile: <display_name>
   Conventions: <files found, or "none found">
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

## Phase 3b: File the issues

Only with `--issues`. The Project Manager decides *what* becomes an issue, via
the `issue:` field on each fix item. You run the `gh` calls, because a loop that
fails halfway is retried here without re-running triage.

The fix plan is the right unit. Filing per reviewer would open the same defect
once per persona that found it.

Read `references/orchestration.md` for the body template, the deduplication key,
and the label set. Blocking items are filed first so they take the lowest
numbers. Record each issue number against its fix item: Phase 4 needs it for
`refs #<number>`, and Phase 5 lists them.

## Phase 4: Apply the fixes

Only when the user opted in.

1. **Verify the groups are disjoint.** Two groups sharing a file is a planning
   error. Merge them rather than running them in parallel.
2. **Record the base commit** with `git -C <repo> rev-parse HEAD`. The
   consolidation step needs it.
3. **Launch one Implementer per group**, concurrently, using
   `references/agents/implementer-fixer.md` with `{{FIX_GROUP}}` replaced by
   that group's items, each carrying its issue number when Phase 3b filed one.
   One group means one agent and no consolidation.
4. **Consolidate.** If two or more Implementers ran, launch the Consolidator
   from `references/agents/consolidator.md`, giving it the base commit and every
   Implementer's result block including its `new-shared` list. Parallel agents
   cannot see each other, so this is what catches two of them writing the same
   method twice.
5. **Verify.** Run the build and test commands yourself. Report the result
   honestly, including failure.

Nothing is pushed. Leave the commits local for the user to review.

## Round control

With `--rounds 1`, the default, you are done: go to Phase 5.

Above 1, repeat **Phases 2, 3, 3b and 4** against the branch as the previous
round left it. Phase 1 already resolved the repository, branch, base, stack and
rotation, and none of those change.

Append to the decision ledger after each round and inject it into the next
round's Project Manager. See `references/orchestration.md`. Without it, round 2
reverses round 1's arbitration and the loop argues with itself.

Record which items each round **attempted**, not only which it applied.
Condition 3 is unanswerable without it: an item that was never attempted
cannot be evidence that attempting things does not work.

### Stop conditions

Check every one of these after each round. **Any single condition ends the
loop.** Report which one fired.

| # | Condition | Why |
|---|---|---|
| 1 | `--rounds` reached | Hard cap. Never exceed it, and never raise it yourself. |
| 2 | No `blocking: true` items in the fix plan | Converged. This is the success case. |
| 3 | Of the blocking items the previous round **attempted**, none is now resolved | No progress. Another round will not help. |
| 4 | Build or tests failed after Phase 4 | Never iterate on your own breakage. |
| 5 | A fix key has been applied and come back **twice** | Oscillation: two criteria are in conflict. |
| 6 | Any Implementer reported `failed`, or the Consolidator failed | The tree is in an unknown state. |
| 7 | `induced` blocking items outnumber the blocking items the previous round resolved | The loop is generating more work than it clears. |

### Classify before you compare

Never compare raw blocking counts between rounds. A count that rises is not
evidence the loop is failing, and stopping on it wastes a converging branch.

The Project Manager classifies every blocking item in its `### LOOP SIGNAL`
block. Read that, not the totals:

| Class | Meaning | Counts against the loop |
|---|---|---|
| `carried` | In an earlier plan, never attempted | No |
| `discovered` | Pre-existing defect earlier rounds missed | No |
| `ineffective` | The ledger records it applied, but the defect persists | Yes |
| `induced` | Did not exist before a previous round's fix caused it | Yes |

Only `ineffective` and `induced` say anything about whether the loop is working.
`carried` items are work nobody has started. `discovered` items mean the review
got better, which is the second pass doing its job.

A real run bears this out: round 2 of the GeronimoPipe review went from 6
blocking to 7, which a raw comparison reads as failure. The classification was
three `carried`, three `discovered`, one `ineffective` and zero `induced` — a
converging branch whose review was still widening. Stopping there would have
been wrong, and the Project Manager's own recommendation was to run another
round.

**One `ineffective` item is a retry, not a stop.** A fix that did not achieve its
goal gets one more attempt with a corrected approach. Condition 5 fires only when
the same key has been applied and come back twice, which is when the retry itself
has failed and two criteria are genuinely in conflict.

**Never loop until the findings reach zero.** Reviewers are instructed to report
a finding even when the fix is trivial, and `low` severity covers style, naming
and polish, so the supply is inexhaustible. Every round's fixes are new code
that the next round reviews, so the finding count is not guaranteed to fall at
all. Blocking-empty is the only criterion that can actually be met.

### Before starting a multi-round run

State the ceiling plainly, then begin:

```
Running up to <n> rounds. Each round launches <r> reviewers plus the Project
Manager, and up to <g> Implementers. Worst case: <n * (r + 1 + g)> agents.
Stops early on: no blocking items, no progress, a red build, or a repeated fix.
```

## Phase 5: Report

Print a summary:

```markdown
## Persona review complete

| Persona | Model | Findings | Highest severity |
|---------|-------|----------|------------------|

Per round, when more than one ran:

| Round | Findings | Fix items | Blocking | Applied | Build |
|-------|----------|-----------|----------|---------|-------|

**Rounds:** <completed> of <requested>, stopped because <condition>
**Fix plan:** <N> findings merged into <M> items, <B> blocking
**Issues:** <#numbers filed>   (only when --issues ran)
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
- Base detection returns `unknown`, or the diff is empty: stop and offer
  `--base <ref>` with a concrete suggestion. An empty diff is not a clean
  review.
- `--base` names a ref that does not resolve: say so and stop. Do not fall back
  to the detected base, which would review a different range than was asked for.
- No PR for the branch: skip every `gh pr comment` step and have each persona
  return its review as text. The findings blocks work the same way.
- A reviewer fails: report which one, continue with the rest, and tell the
  Project Manager that persona is missing.
- The Project Manager fails: show the raw findings and stop. Never build a fix
  plan yourself, never run Phase 4 without one, and never file issues from raw
  findings. Untriaged findings would file the same defect once per persona.
- No GitHub remote, or `gh auth status` fails, with `--issues`: report it and
  continue. Do not half-file.
- Issue creation fails partway: say exactly which items were filed and which
  were not, and do not describe the run as complete.
- An Implementer fails: keep the other groups' commits, report the failed items
  as unapplied. Do not retry into a dirty tree, and end the loop.
- `--rounds` above 1 without `--fix`: say the combination does nothing and ask
  whether to add `--fix`. Do not silently run one round.
- `--rounds` above 3: cap it at 3, say you capped it, and continue.
- The loop stops on a condition other than converged: say which one, and do not
  describe the branch as reviewed clean.
- The build fails in Phase 2: run every review anyway, and flag it at the top of
  the summary.
