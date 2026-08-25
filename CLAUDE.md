# Claude Code Configuration for claude-skills

## Project overview

This repository holds personal Claude Code skills. Each skill is a directory
under `skills/`, installed into `~/.claude/skills/` by `install.ps1` or
`install.sh`.

These are personal skills, not plugins. There is no `.claude-plugin/` manifest
and no marketplace. The plugin packaging was removed on 2026-08-24 because it
was never installable in practice.

## Repository layout

```
claude-skills/
  skills/<skill-name>/
    SKILL.md              Entry point: frontmatter and the workflow
    references/           Depth loaded on demand
    scripts/              Bundled shell scripts
  install.ps1
  install.sh
```

## Development rules

### Paths

`${CLAUDE_SKILL_DIR}` is a plugin variable and is **undefined** in a personal
skill. Never use it here. Instead:

- Reference bundled files by a path relative to the skill directory, such as
  `references/profiles/dotnet-library.md`.
- In shell commands, write the full path:
  `~/.claude/skills/<skill-name>/scripts/foo.sh`.
- State the skill root once near the top of `SKILL.md` so both forms are
  unambiguous.

### SKILL.md

- Frontmatter carries `name` and `description` only. The `description` decides
  when the skill activates, so write it as trigger conditions.
- Keep `SKILL.md` short. It loads on every session, so put depth in
  `references/` and say when to load each file.
- Leave `paths` unset unless the skill genuinely applies to one file type.

### Shell scripts

- Must run in Git Bash on Windows. No GNU-only extensions.
- Use forward slashes, and normalize Windows-style paths when accepting input.

### Sub-agents

- Sub-agents get fresh context and cannot read the skill's files. The
  orchestrator must read reference files and inject their content into the Agent
  tool's `prompt`.
- Keep agent templates in `references/agents/`. A directory named `agents/` at
  the root gets auto-discovered and the templates load as broken standalone
  agents.
- Include a `model` hint per agent: opus for judgment, sonnet for bulk work,
  haiku for bookkeeping.

### Profiles

- Markdown with YAML frontmatter for metadata.
- Overlays are additive. They append to the base profile and never replace it.
- Profile content is stack-specific review criteria, not a full persona
  redefinition.

## Testing

- Run `install.sh --dry-run` before a real install.
- Test detection scripts against known project directories.
- Verify the correct persona set is selected per stack, and that overlay merging
  produces the combined criteria.
