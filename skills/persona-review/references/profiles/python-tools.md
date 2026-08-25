---
name: python-tools
display_name: "Python Tools / Scripts"
build_command: ""
test_command: "pytest"
rotation_size: 4
personas: [implementer, reviewer, tester, security-auditor]
---

# Python Tools Review Profile

## Implementer Criteria
- Type hints on all function signatures and return types
- Use pathlib.Path for file paths, not os.path string manipulation
- Virtual environment management: requirements.txt or pyproject.toml is up to date
- Subprocess security: use shell=False (list form), never shell=True with user input
- Proper error handling for external tool calls (FFmpeg, yt-dlp, etc.)
- Use logging module, not print() for operational output
- Argparse or click for CLI argument parsing (not sys.argv slicing)
- Follow PEP 8 style conventions

## Reviewer Criteria
- Dependency pinning: versions pinned in requirements.txt (not floating)
- Error handling for external tools: check return codes, handle stderr
- Code organization: separate concerns (CLI entry point, business logic, I/O)
- Resource cleanup: use context managers (with statement) for files, connections
- No bare except clauses: catch specific exceptions
- Check for Python version compatibility with target environment
- Avoid mutable default arguments (def f(x=[]) anti-pattern)

## Tester Criteria
- pytest patterns: use fixtures, parametrize for edge cases
- Mock filesystem and network calls (unittest.mock, pytest-mock)
- Parametrized tests for boundary values and edge cases
- Test CLI argument parsing (valid, invalid, missing args)
- Test error handling paths (file not found, permission denied, network timeout)
- Use tmp_path fixture for file system tests
- Test with different OS path separators if cross-platform

## Security Auditor Criteria
- Subprocess injection: verify no user input passed to shell=True
- File path traversal: validate user-supplied paths don't escape intended directory
- Credential handling: no hardcoded API keys, tokens, or passwords
- Dependency vulnerabilities: check for known CVEs in pinned versions
- Pickle/eval: no deserialization of untrusted data
- Temporary files: use tempfile module with proper permissions
- YAML loading: use yaml.safe_load, never yaml.load without Loader
