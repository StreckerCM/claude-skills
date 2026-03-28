# Claude Code Configuration for claude-skills

## Project Overview
This repo contains custom Claude Code skills (plugins). Each skill lives in its own top-level directory with a `.claude-plugin/plugin.json` manifest.

## Repository Structure
```
claude-skills/
  <skill-name>/
    .claude-plugin/plugin.json        # Plugin manifest (name, version, description)
    commands/<command>.md              # Slash commands (user-invocable skills)
    agents/<agent>.md                  # Sub-agent definitions
    profiles/                         # Configuration profiles (skill-specific)
    scripts/                          # Shell scripts (must work in Git Bash on Windows)
    README.md                         # Skill-specific documentation
```

## Development Rules

### Shell Scripts
- All scripts must run in Git Bash on Windows (no GNU-only extensions)
- Use forward slashes in paths
- Handle Windows-style paths gracefully (convert `C:\` to `/c/` when needed)

### Skill Commands
- Commands are markdown files with structured prompts
- Follow the phased workflow pattern: detect context, load configuration, execute
- Use sub-agents for isolated, parallelizable work

### Sub-Agents
- Each agent gets fresh context (no state bleed between agents)
- Include model hints in agent frontmatter (opus for judgment, sonnet for bulk work, haiku for bookkeeping)
- Agents post structured output (PR comments, summaries) in consistent markdown format

### Profiles
- Profiles use markdown with YAML frontmatter for metadata
- Overlays are additive (append to base profile, never replace)
- Profile customizations are stack-specific review criteria, not full persona redefinitions

## Testing
- Test detection scripts against known project directories
- Verify correct persona selection per stack
- Confirm overlay merging produces expected combined criteria
