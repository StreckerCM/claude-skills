---
name: dotnet-library
display_name: ".NET Library / NuGet Package"
build_command: "dotnet build *.sln"
test_command: "dotnet test *.sln"
rotation_size: 4
personas: [implementer, reviewer, tester, project-manager]
---

# .NET Library Review Profile

## Implementer Criteria
- Public API surface design: intuitive naming, consistent patterns
- Backward compatibility: no breaking changes without major version bump
- XML doc comments on all public types and members
- Strong naming if required by downstream consumers
- Proper exception hierarchy (use standard .NET exception types where appropriate)
- Follow .NET library design guidelines (IDisposable pattern, async naming, etc.)
- Ensure netstandard/multi-targeting is correct for intended consumers

## Reviewer Criteria
- Breaking change detection: check removed/renamed public members, changed signatures
- Nullable reference type annotations on all public APIs
- Performance-sensitive code paths: avoid unnecessary allocations, use Span<T> where appropriate
- API consistency: similar operations should have similar signatures
- Check for proper use of readonly, sealed, and internal access modifiers
- Verify exception messages are helpful and include parameter names
- Check that default parameter values are sensible

## Tester Criteria
- Known-answer tests for algorithmic code
- Boundary value testing (int.MaxValue, empty collections, null inputs)
- Cross-platform compatibility tests if targeting multiple runtimes
- NuGet packaging validation (correct dependencies, metadata)
- Test public API contracts, not internal implementation
- Verify backward compatibility with previous test baselines
- Performance regression tests for critical paths

## Project Manager Criteria
- SemVer compliance: major for breaking, minor for features, patch for fixes
- Changelog/release notes updated
- NuGet metadata (description, tags, license, repository URL) is current
- README examples are up to date with API changes
- Verify dependency versions are appropriate (not unnecessarily bleeding edge)
