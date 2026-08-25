---
name: dotnet-library
display_name: ".NET Library / NuGet Package"
build_command: "dotnet build *.sln"
test_command: "dotnet test *.sln"
rotation_size: 4
personas: [implementer, reviewer, tester, security-auditor]
---

# .NET Library Review Profile

## Implementer Criteria
- Public API surface design: intuitive naming, consistent patterns
- Backward compatibility: no breaking changes without major version bump
- XML doc comments on all public types and members
- Strong naming if required by downstream consumers
- Proper exception hierarchy (use standard .NET exception types where appropriate)
- Follow .NET library design guidelines (IDisposable pattern, async naming, etc.)
- `ConfigureAwait(false)` on every await in library code. Without it a
  continuation is posted back to the caller's synchronisation context, which
  deadlocks a WPF or WinForms consumer that blocks on the returned task
- Every public async method accepts a `CancellationToken`, defaulted where
  that suits the API. A caller cannot add cancellation to a library that
  does not offer it
- Ensure netstandard/multi-targeting is correct for intended consumers
- Conditional compilation across target frameworks is correct on **every**
  target, not just the one built locally. An API available on net8.0 and
  missing on netstandard2.0 inside an untested `#if` compiles on the
  developer's machine and fails in CI, or worse, ships behaving differently

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
- The test project multi-targets the same frameworks as the library. Testing
  one target leaves the conditional code on the others unexecuted
- NuGet packaging validation (correct dependencies, metadata)
- Test public API contracts, not internal implementation
- Verify backward compatibility with previous test baselines
- Performance regression tests for critical paths

## Security Auditor Criteria
- Native interop safety: validate buffer sizes and struct layouts in P/Invoke, never trust a native return length
- Deserialization of untrusted input: reject unbounded object graphs and unexpected types
- Path handling: reject traversal sequences in any API that accepts a file path
- Public API input validation: a library cannot assume its caller validated anything
- No hardcoded secrets, keys, or connection strings, including in test fixtures
- Dependency vulnerabilities: check transitive packages against known advisories
- Exception messages must not leak paths, connection details, or internal state to callers

## Project Manager Criteria
- SemVer compliance: major for breaking, minor for features, patch for fixes
- Changelog/release notes updated
- NuGet metadata (description, tags, license, repository URL) is current
- README examples are up to date with API changes
- Verify dependency versions are appropriate (not unnecessarily bleeding edge)
