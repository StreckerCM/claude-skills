# Orchestration reference

How to build sub-agent prompts, route findings between phases, and record
results. Load this during Phase 2 of `SKILL.md`.

## Why prompts must be self-contained

Each sub-agent starts with fresh context and no access to this skill's
directory. It cannot read `references/agents/reviewer.md`, and it cannot see the
profile you loaded. Everything the persona needs must be inside the `prompt`
string you pass to the Agent tool.

A prompt that says "read your criteria from `references/profiles/...`" produces
a sub-agent that reviews nothing.

## Phase 2: reviewer prompts

For each reviewer in the rotation:

1. Read `references/agents/<persona>.md`. Note the `model` field in its
   frontmatter.
2. From the profile you already loaded, extract that persona's criteria section,
   such as `## Implementer Criteria`.
3. If an overlay is active, extract the same section from the overlay profile.
4. Replace the `{{STACK_CRITERIA}}` placeholder with the criteria from step 2.
5. Assemble the prompt below.

The three `--fable` lenses skip steps 2 through 4. Their templates carry no
placeholder and take no stack criteria.

```
You are performing a persona review on branch: <branch>
PR: #<pr-number>            (omit this line if there is no PR)
Build command: <build_command>
Test command: <test_command>

<full text of the agent template, with {{STACK_CRITERIA}} replaced>

## Additional criteria (<overlay> overlay)
<overlay criteria for this persona>
                            (omit this section if no overlay is active)

## Instructions
1. Run `git diff main...HEAD` to see every change on this branch.
2. Review the changes against your criteria above.
3. Run the build command and confirm the project builds.
4. Run the test command, if one is defined.
5. Post your review: `gh pr comment <pr-number> --body "<your review>"`.
   If there is no PR, return the review as your final text instead.
6. End your response with the FINDINGS block. This is required. The Project
   Manager cannot act on findings that are not in it.

You are read-only. Do not edit files, do not commit, do not push. Propose every
change as a finding.
```

Do not give a reviewer another reviewer's findings. They run blind on purpose,
and this matters most for the `--fable` lenses, whose value is the perspective
the standard rotation lacks.

## Phase 3: Project Manager prompt

One agent, after every reviewer finishes.

```
<full text of references/agents/project-manager.md, {{STACK_CRITERIA}} replaced>

## Reviewer findings

### From IMPLEMENTER
<that agent's verbatim FINDINGS block>

### From REVIEWER
<...>

(one section per reviewer that ran, including any --fable lens)

### Missing
<persona names that failed or were not in the rotation>

## Instructions
1. Run `git diff main...HEAD` for context.
2. Merge and de-duplicate the findings above.
3. Assign a file scope and a group number to every fix item. Items sharing any
   file must share a group.
4. Post the PR comment, then emit the FIX PLAN block.

You are read-only. Do not edit files, do not commit, do not push.
```

## Phase 4: Implementer prompts

Skip unless the user opted in with `--fix` or by answering the Phase 3 prompt.

**Check the groups first.** Collect every `scope` per group and confirm no file
appears in two groups. If one does, the plan is wrong: merge those groups into
one and run them with a single agent. Never launch parallel agents over an
overlapping scope.

Record the base commit before launching: `git rev-parse HEAD`.

One agent per group, launched concurrently:

```
You are applying fixes on branch: <branch>
Build command: <build_command>
Test command: <test_command>

<full text of references/agents/implementer-fixer.md, with {{FIX_GROUP}}
 replaced by this group's fix items, verbatim from the FIX PLAN>

Other Implementer agents are working on other groups right now. Their file
scopes do not overlap yours. You cannot see their work, so search before you add
any new method, helper, constant, or type.
```

Give each agent only its own group. Handing it the whole plan invites it to work
outside its scope.

## Phase 4b: Consolidator prompt

Only when two or more Implementers ran. One group means no cross-agent
duplication is possible.

```
<full text of references/agents/consolidator.md>

Base commit before the fixes: <sha>

## What the Implementers reported

### Group 1
<that agent's verbatim FIX RESULT and OUT OF SCOPE blocks>

### Group 2
<...>

## Instructions
1. Run `git diff <sha>...HEAD` to see everything the Implementers changed.
2. Compare the new-shared entries across groups. That is where two agents
   writing the same thing twice shows up.
3. Consolidate real duplicates. Report near-misses you deliberately kept.
4. Build and test. Both must pass before you finish.
```

## Data formats

Three blocks move between phases. Pass them through verbatim; do not summarize
or reformat them, because the next agent parses the field names.

| Block | Emitted by | Consumed by |
|---|---|---|
| `### FINDINGS` | every reviewer | Project Manager |
| `### FIX PLAN` | Project Manager | Implementer, orchestrator |
| `### FIX RESULT` | each Implementer | Consolidator, orchestrator |

Reviewer id prefixes: `IMPL`, `REV`, `TEST`, `SEC`, `UIUX`, and for the deep
lenses `ARCH`, `ADV`, `SKEP`.

If an agent returns no parsable block, record it as missing and continue. Do not
invent findings on its behalf, and do not treat a missing block as a clean pass.

## Review record

After printing the summary, write `.claude/memory/review_<branch-slug>_<YYYYMMDD-HHmm>.md`
in the project being reviewed. Slugify the branch by replacing `/` and other
non-alphanumeric characters with `-`.

```markdown
---
name: persona-review-<branch>
description: Persona review results for <branch> (PR #<number>) on <YYYY-MM-DD>
type: project
---

## Persona review: <branch>

**Date:** <YYYY-MM-DD>
**PR:** #<number>
**Stack:** <stack>
**Reviewers:** <list, noting whether --fable ran>
**Recommendation:** <merge recommendation>

### Findings

<N> raw findings merged into <M> fix items, <B> blocking.

| Persona | Findings | Highest severity |
|---------|----------|------------------|

### Applied

| Fix | Status | Commit |
|-----|--------|--------|

Consolidation: <duplicates merged, or none>
Build: <pass/fail>  Tests: <pass/fail/not-run>

### Outstanding

- <unapplied item, and why>
```

Then append one line to `.claude/memory/MEMORY.md`, creating the file if it does
not exist:

```
- [Review: <branch>](review_<branch-slug>_<YYYYMMDD-HHmm>.md) — <recommendation>, <YYYY-MM-DD>
```
