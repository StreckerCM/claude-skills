# Orchestration reference

How to build sub-agent prompts and record results. Load this during Phase 2 of
`SKILL.md`.

## Why prompts must be self-contained

Each sub-agent starts with fresh context and no access to this skill's
directory. It cannot read `references/agents/implementer.md`, and it cannot see
the profile you loaded. Everything the persona needs must be inside the `prompt`
string you pass to the Agent tool.

A prompt that says "read your criteria from `references/profiles/...`" produces
a sub-agent that reviews nothing.

## Building one persona's prompt

For each persona in the rotation:

1. Read `references/agents/<persona>.md`. Note the `model` field in its
   frontmatter — you pass that to the Agent tool.
2. From the profile you already loaded, extract that persona's criteria section,
   such as `## Implementer Criteria`.
3. If an overlay is active, extract the same section from the overlay profile.
4. In the agent template text, replace the `{{STACK_CRITERIA}}` placeholder with
   the criteria from step 2.
5. Assemble the final prompt using the template below.

## Prompt template

```
You are performing a persona review on branch: <branch>
PR: #<pr-number>            (omit this line if there is no PR)
Build command: <build_command>
Test command: <test_command>

<full text of references/agents/<persona>.md, with {{STACK_CRITERIA}} replaced>

## Additional criteria (<overlay> overlay)
<overlay criteria for this persona>
                            (omit this whole section if no overlay is active)

## Instructions
1. Run `git diff main...HEAD` to see every change on this branch.
2. Review the changes against your criteria above.
3. Run the build command and confirm the project builds.
4. Run the test command and confirm tests pass, if the profile defines one.
5. Post your review: `gh pr comment <pr-number> --body "<your review>"`.
   If there is no PR, return the review as your final text instead.
6. Fix any issue you can fix safely, and commit it with your persona prefix.
```

## Agent tool parameters

| Parameter | Value |
|---|---|
| `description` | `Persona review: <persona-name>` |
| `prompt` | The assembled string above, with every placeholder resolved |
| `model` | The `model` field from the agent template's frontmatter |

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
**Recommendation:** <merge recommendation>

### Results

| Persona | Status | Key findings |
|---------|--------|--------------|

### Blocking, before merge

- <item>

### Non-blocking, after merge

- <item>
```

Then append one line to `.claude/memory/MEMORY.md`, creating the file if it does
not exist:

```
- [Review: <branch>](review_<branch-slug>_<YYYYMMDD-HHmm>.md) — <recommendation>, <YYYY-MM-DD>
```
