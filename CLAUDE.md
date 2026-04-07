# Claude Code Configuration for claude-skills

## Project Overview
This repo contains custom Claude Code skills (plugins). Each skill lives in its own top-level directory with a `.claude-plugin/plugin.json` manifest.

## Repository Structure
```
claude-skills/
  <plugin-name>/
    .claude-plugin/plugin.json            # Plugin manifest (name, version, description)
    skills/<skill-name>/SKILL.md          # Skill entry point (frontmatter + orchestration)
    skills/<skill-name>/scripts/          # Shell scripts bundled with the skill
    skills/<skill-name>/references/       # Supporting files (agent templates, profiles, etc.)
    README.md                             # Plugin-specific documentation
```

## Development Rules

### Shell Scripts
- All scripts must run in Git Bash on Windows (no GNU-only extensions)
- Use forward slashes in paths
- Handle Windows-style paths gracefully (convert `C:\` to `/c/` when needed)

### Skills
- Skills use `SKILL.md` with YAML frontmatter (`name`, `description`, `argument-hint`)
- Follow the phased workflow pattern: detect context, load configuration, execute
- Use `${CLAUDE_SKILL_DIR}` for all file path references (never hardcode relative paths)
- Use sub-agents for isolated, parallelizable work

### Sub-Agents
- Each agent gets fresh context (no state bleed between agents, no access to plugin files)
- The orchestrator must READ reference files and INJECT content into Agent tool prompts
- Include model hints in agent frontmatter (opus for judgment, sonnet for bulk work, haiku for bookkeeping)
- Agents post structured output (PR comments, summaries) in consistent markdown format
- Agent templates with placeholders (e.g., `{{STACK_CRITERIA}}`) go in `references/agents/`, NOT at plugin root

### Profiles
- Profiles use markdown with YAML frontmatter for metadata
- Overlays are additive (append to base profile, never replace)
- Profile customizations are stack-specific review criteria, not full persona redefinitions

## Testing
- Test detection scripts against known project directories
- Verify correct persona selection per stack
- Confirm overlay merging produces expected combined criteria
