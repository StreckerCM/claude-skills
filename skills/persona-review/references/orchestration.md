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
5. Replace every `{{BASE_BRANCH}}` placeholder with the base branch resolved in
   Phase 1. Templates carry the placeholder rather than a literal `main`,
   because a wrong base yields an empty diff that looks like a clean review.
6. Assemble the prompt below.

The three `--fable` lenses skip steps 2 through 4: they take no stack criteria.
They still need step 5, because they diff the branch like every other reviewer.

```
You are performing a persona review.
Repository: <absolute repo path> — run every git and build command against it.
Branch: <branch>
Base branch: <base-branch>
PR: #<pr-number>            (omit this line if there is no PR)
Build command: <build_command>
Test command: <test_command>

<full text of the agent template, with {{STACK_CRITERIA}} replaced>

## Additional criteria (<overlay> overlay)
<overlay criteria for this persona>
                            (omit this section if no overlay is active)

## Instructions
1. Run `git diff <base-branch>...HEAD` to see every change on this branch.
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
1. Run `git diff <base-branch>...HEAD` for context.
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
You are applying fixes.
Repository: <absolute repo path> — run every git and build command against it.
Branch: <branch>
Base branch: <base-branch>
Build command: <build_command>
Test command: <test_command>

<full text of references/agents/implementer-fixer.md, with {{FIX_GROUP}}
 replaced by this group's fix items, verbatim from the FIX PLAN>

Other Implementer agents are working on other groups right now. Their file
scopes do not overlap yours. You cannot see their work, so search before you add
any new method, helper, constant, or type.
```

When Phase 3b filed an issue for an item, add its number to that item's block in
`{{FIX_GROUP}}` as `issue: #<number>`, so the commit can reference it.

Give each agent only its own group. Handing it the whole plan invites it to work
outside its scope.

## Phase 4b: Consolidator prompt

Only when two or more Implementers ran. One group means no cross-agent
duplication is possible.

```
<full text of references/agents/consolidator.md>

Repository: <absolute repo path>
Base commit before the fixes: <sha>

## What the Implementers reported

### Group 1
<that agent's verbatim FIX RESULT and OUT OF SCOPE blocks>

### Group 2
<...>

## Instructions
1. Run `git diff <sha>...HEAD` in the repository to see everything the
   Implementers changed.
2. Compare the new-shared entries across groups. That is where two agents
   writing the same thing twice shows up.
3. Consolidate real duplicates. Report near-misses you deliberately kept.
4. Build and test. Both must pass before you finish.
```

## Phase 3b: File the issues

Skip entirely unless the user passed `--issues`. Filing into someone's tracker
is outward-facing and cannot be cleanly undone: an issue can be closed but not
deleted. The flag is the authorization. Never infer it.

You file, not the Project Manager. It decides *what* becomes an issue; the loop
belongs here, where a partial failure can be retried without re-running triage.

### Before you file

1. **Confirm the remote.** `git -C <repo> remote get-url origin`. No GitHub
   remote means no issues: say so and continue to Phase 5.
2. **Confirm auth.** `gh auth status`. If it fails, stop and tell the user
   rather than half-filing.
3. **List what is already there**, so a second review of the same branch does
   not duplicate the first:

   ```bash
   gh issue list --repo <slug> --label persona-review --state all      --limit 200 --json number,title,body
   ```

4. **Create any missing labels.** Ignore "already exists" errors.

   | Label | Colour | Purpose |
   |---|---|---|
   | `persona-review` | `5319e7` | Provenance: raised by an automated review |
   | `severity:high` | `d93f0b` | Fix before merge |
   | `severity:medium` | `fbca04` | Fix soon |
   | `severity:low` | `c2e0c6` | Optional polish |
   | `blocking` | `b60205` | Must be resolved before merge |

   Map `critical` onto `severity:high`; the tracker does not need a fourth tier.

### Deduplication

Every body carries a stable key on its first line:

```
<!-- persona-review-key: <branch>/<slug of title> -->
```

Slug the title by lowercasing, replacing every run of non-alphanumerics with a
hyphen, and trimming to 60 characters. The key is derived from the branch and
the title, never from the `FIX-N` id, because ids are renumbered on every run.

Before creating an item, look for its key in the bodies you listed in step 3.

- **Key found, issue open:** do not create. Record the existing number and
  report it as already tracked.
- **Key found, issue closed:** do not reopen. Report it, and let the user decide
  whether the defect returned.
- **Key absent:** create it.

### Filing

File `blocking: true` items first, then the rest in fix-plan order, so the
lowest issue numbers are the ones that matter most. Skip every item marked
`issue: no`.

Compose each body from the fix plan's own fields. Do not rewrite them: the
Project Manager wrote them for a reader who was not in the review.

```markdown
<!-- persona-review-key: <branch>/<slug> -->
> Raised by an automated persona review of `<branch>` on <YYYY-MM-DD>.
> Fix plan item **<FIX-N>**, group <n>.

| | |
|---|---|
| **Severity** | <severity> |
| **Blocking** | yes, fix before merge / no |
| **Scope** | `<file>` `<file>` |
| **Reported by** | <sources> |

## What is wrong

<detail>

## Proposed fix

<fix>

---

<sub>Generated by the `persona-review` skill. Reviewers report; they do not
change code. Findings from every persona were merged and de-duplicated by the
Project Manager into <M> fix items. Verify before acting.</sub>
```

Title each issue `<FIX-N>: <title>`. Labels: `persona-review`, the severity
label, and `blocking` when the item is blocking.

Write the body to a file and pass `--body-file`. Bodies contain backticks,
quotes, and code fences that shell quoting mangles.

```bash
gh issue create --repo <slug> --title "<title>"   --body-file <path> --label "persona-review,severity:high,blocking"
```

### Afterwards

Record each created number against its fix item. Phase 4 injects it so the
Implementer can write `refs #<number>` in its commits, and Phase 5 lists the
numbers in the review record.

If a create fails partway, report exactly which items were filed and which were
not. A half-filed tracker described as complete is worse than a failed run.

## Data formats

Three blocks move between phases. Pass them through verbatim; do not summarize
or reformat them, because the next agent parses the field names.

| Block | Emitted by | Consumed by |
|---|---|---|
| `### FINDINGS` | every reviewer | Project Manager |
| `### FIX PLAN` | Project Manager | Implementer, issue filing, orchestrator |
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
Issues filed: <#numbers, or "none, --issues not passed">

| Persona | Findings | Highest severity |
|---------|----------|------------------|

### Applied

| Fix | Issue | Status | Commit |
|-----|-------|--------|--------|

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
