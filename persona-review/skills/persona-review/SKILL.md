---
name: persona-review
description: "Run a technology-aware persona code review. Auto-detects project stack and launches specialized sub-agent reviewers (Implementer, Reviewer, Tester, UI/UX Designer, Security Auditor, Project Manager). Use when asked to review code, run persona review, or launch sub-agent reviewers."
argument-hint: "[branch] [--stack <stack>] [--overlay <overlay>] [--rotation <size>]"
---

# Persona Review Skill

Orchestrate a technology-aware persona review. Detect the project's tech stack, load the appropriate review profile, and launch independent sub-agent personas to review the code.

## Phase 1: Setup & Detection

### Step 1: Determine the branch
- If a branch argument was provided, use it
- Otherwise, check the current branch with `git branch --show-current`
- If the branch has a PR, get the PR number with `gh pr list --head <branch> --json number --jq '.[0].number'`

### Step 2: Detect the technology stack
- If `--stack` was provided, use it directly
- Otherwise, run the detection script:
  ```bash
  bash ${CLAUDE_SKILL_DIR}/scripts/detect-stack.sh .
  ```
- The script outputs a stack identifier like `dotnet-desktop` or `dotnet-library+scientific-computing`
- Parse the output: split on `+` to get base stack and optional overlay
- If `--overlay` was provided, append it to any auto-detected overlay

### Step 3: Load the profile
- Read the profile file: `${CLAUDE_SKILL_DIR}/references/profiles/<base-stack>.md`
- If an overlay was detected/specified, also read: `${CLAUDE_SKILL_DIR}/references/profiles/<overlay>.md`
- Extract from the profile YAML frontmatter:
  - `personas`: list of persona agents to launch
  - `rotation_size`: number of personas (can be overridden by `--rotation`)
  - `build_command`: build command for the project
  - `test_command`: test command for the project

### Step 4: Announce the review
Output to the user:
```
Starting persona review on branch: <branch>
Detected stack: <stack> (+ <overlay> if applicable)
Profile: <display_name>
Personas: <list of personas to run>
Build: <build_command>
Tests: <test_command>
```

## Phase 2: Launch Sub-Agent Personas

Each persona runs as an independent sub-agent via the Agent tool. Sub-agents receive fresh context with NO access to plugin files. Read all reference files and inject their content directly into the Agent tool's `prompt` parameter.

### Constructing Each Agent's Prompt

For each persona in the rotation:

1. Read the agent definition file: `${CLAUDE_SKILL_DIR}/references/agents/<persona>.md`
2. Extract this persona's criteria section from the already-loaded profile (e.g., "## Implementer Criteria" section)
3. If an overlay is active, also extract the overlay criteria for this persona
4. In the agent file content, replace `{{STACK_CRITERIA}}` with the extracted criteria
5. If overlay criteria exist, append them after the stack criteria under "## Additional Criteria (<overlay> Overlay)"
6. Construct the full prompt by prepending the context block and appending the instructions block
7. Pass this COMPLETE prompt to the Agent tool — the sub-agent must NOT need to read any plugin files

### Parallelization Strategy

**Round 1 (parallel):** Launch these personas concurrently since they have independent review perspectives:
- Implementer
- Reviewer
- Tester (if in rotation)
- UI/UX Designer (if in rotation)
- Security Auditor (if in rotation)

**Round 2 (sequential, after Round 1 completes):** Launch last since it needs to read all other reviews:
- Project Manager (if in rotation)

### Agent Tool Invocation

For each persona, invoke the Agent tool with:
- `description`: "Persona review: <persona-name>"
- `prompt`: The fully constructed prompt string (all file content embedded), structured as:
  ```
  You are performing a persona review on branch: <branch>
  PR: #<pr-number> (if applicable)
  Build command: <build_command>
  Test command: <test_command>

  <complete contents of the agent definition file with {{STACK_CRITERIA}} replaced>

  <if overlay is active>
  ## Additional Criteria (<overlay> Overlay)
  <overlay criteria for this persona>
  </if>

  ## Instructions
  1. Run `git diff main...HEAD` to see all changes on this branch
  2. Review the changes according to your criteria above
  3. Run the build command to verify the project builds
  4. Run the test command to verify tests pass (if applicable)
  5. Post your review as a PR comment: `gh pr comment <pr-number> --body "<your review>"`
  6. If you find issues that you can fix, make the fix and commit with the appropriate prefix
  ```
- `model`: Use the model hint from the agent's frontmatter (sonnet, opus, or haiku)

## Phase 3: Summary

After all sub-agents complete:

1. Collect the results from each agent
2. Output a summary table to the user:

```markdown
## Persona Review Complete

| Persona | Model | Status | Key Findings |
|---------|-------|--------|-------------|
| Implementer | sonnet | Clean/Issues | <summary> |
| Reviewer | opus | Clean/Issues | <summary> |
| ... | ... | ... | ... |

**Stack:** <detected stack>
**Branch:** <branch>
**PR:** #<pr-number>
```

3. If all personas report clean passes, indicate the review is complete
4. If any personas found issues, list the outstanding items

### Save review to memory

After outputting the summary, save a persistent record so future sessions can reference it. Write a memory file to the project's `.claude/memory/` directory:

**File:** `.claude/memory/review_<branch-name-slugified>_<YYYYMMDD-HHmm>.md`

```markdown
---
name: persona-review-<branch>
description: "Persona review results for <branch> (PR #<pr-number>) — <date>"
type: project
---

## Persona Review: <branch>
**Date:** <YYYY-MM-DD>
**PR:** #<pr-number>
**Stack:** <detected stack>
**Recommendation:** <merge recommendation>

### Results
| Persona | Status | Key Findings |
|---------|--------|-------------|
| ... | ... | ... |

### Action Items (before merge)
- <item 1>
- <item 2>

### Action Items (after merge / non-blocking)
- <item 1>
- <item 2>
```

Then add an entry to `.claude/memory/MEMORY.md` (create if it doesn't exist):
```
- [Review: <branch>](review_<branch-name-slugified>_<YYYYMMDD-HHmm>.md) — <recommendation>, <date>
```

## Error Handling

- If stack detection fails (returns "unknown"), ask the user to specify `--stack` manually
- If no PR exists for the branch, skip PR comment posting and output findings to the console instead
- If a sub-agent fails, report the failure and continue with remaining agents
- If the build fails, still run all reviews but flag the build failure prominently
