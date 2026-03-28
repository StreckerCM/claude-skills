---
name: persona-review
description: "Run a technology-aware persona review on the current branch. Auto-detects stack and launches specialized sub-agent reviewers."
user_invocable: true
arguments:
  - name: branch
    description: "Branch or PR to review (default: current branch)"
    required: false
  - name: --stack
    description: "Override auto-detected stack (dotnet-desktop, dotnet-library, aspnet-web, nodejs-api, static-site, salesforce, python-tools)"
    required: false
  - name: --overlay
    description: "Add a review overlay (scientific-computing)"
    required: false
  - name: --rotation
    description: "Override rotation size (4 or 6)"
    required: false
---

# Persona Review Skill

You are the orchestrator for a technology-aware persona review. You will detect the project's tech stack, load the appropriate review profile, and launch independent sub-agent personas to review the code.

## Phase 1: Setup & Detection

### Step 1: Determine the branch
- If a branch argument was provided, use it
- Otherwise, check the current branch with `git branch --show-current`
- If the branch has a PR, get the PR number with `gh pr list --head <branch> --json number --jq '.[0].number'`

### Step 2: Detect the technology stack
- If `--stack` was provided, use it directly
- Otherwise, run the detection script:
  ```bash
  bash persona-review/scripts/detect-stack.sh .
  ```
- The script outputs a stack identifier like `dotnet-desktop` or `dotnet-library+scientific-computing`
- Parse the output: split on `+` to get base stack and optional overlay
- If `--overlay` was provided, append it to any auto-detected overlay

### Step 3: Load the profile
- Read the profile file: `persona-review/profiles/<base-stack>.md`
- If an overlay was detected/specified, also read: `persona-review/profiles/<overlay>.md`
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

Each persona runs as an **independent sub-agent** with fresh context. The sub-agent receives:
1. The base persona prompt from `persona-review/agents/<persona>.md`
2. Stack-specific criteria from the loaded profile (replacing `{{STACK_CRITERIA}}` in the agent prompt)
3. If an overlay is active, the overlay criteria are **appended** to the stack criteria
4. The branch name and PR number to review

### Parallelization Strategy

**Round 1 (parallel):** Launch these personas concurrently since they have independent review perspectives:
- Implementer
- Reviewer
- Tester (if in rotation)
- UI/UX Designer (if in rotation)
- Security Auditor (if in rotation)

**Round 2 (sequential, after Round 1 completes):** Launch last since it needs to read all other reviews:
- Project Manager (if in rotation)

### Launching Each Agent

For each persona in the rotation, use the Agent tool with:
- `description`: "Persona review: <persona-name>"
- `prompt`: Constructed from the agent definition file with `{{STACK_CRITERIA}}` replaced by the profile's criteria for that persona. Include:
  - The branch to review: `<branch>`
  - The PR number (if exists): `<pr-number>`
  - The build command: `<build_command>`
  - The test command: `<test_command>`
  - Instruction to read `git diff main...HEAD` (or appropriate base branch) for the changes
  - Instruction to post findings as a PR comment using `gh pr comment <pr-number>`
- `model`: Use the model hint from the agent's frontmatter (sonnet, opus, or haiku)

### Agent Prompt Template

When constructing the prompt for each agent, use this structure:

```
You are performing a persona review on branch: <branch>
PR: #<pr-number> (if applicable)
Build command: <build_command>
Test command: <test_command>

<contents of persona-review/agents/<persona>.md with {{STACK_CRITERIA}} replaced>

<if overlay is active>
## Additional Criteria (Scientific Computing Overlay)
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

## Error Handling

- If stack detection fails (returns "unknown"), ask the user to specify `--stack` manually
- If no PR exists for the branch, skip PR comment posting and output findings to the console instead
- If a sub-agent fails, report the failure and continue with remaining agents
- If the build fails, still run all reviews but flag the build failure prominently
