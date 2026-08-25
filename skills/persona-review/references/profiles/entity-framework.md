---
name: entity-framework
display_name: "Entity Framework (Overlay)"
type: overlay
applies_to: [aspnet-web, dotnet-desktop, dotnet-library]
---

# Entity Framework Review Overlay

This is an **additive overlay**, not a standalone profile. These criteria are
appended to the base stack profile's criteria for each persona.

It applies when the project references `DbContext`. EF failures are usually not
compile errors or exceptions. They are a page that works on a developer's
50-row table and times out on production's two million, or a migration that
silently drops a column. Review it for what happens at scale, not for whether
it runs.

## Implementer Criteria (additional)

- `AsNoTracking()` on every read-only query. The change tracker is pure overhead
  when nothing will be saved, and it grows with the result set
- No `SaveChanges` inside a loop. Batch the changes and save once, so the work
  is one round trip and one transaction
- Projection with `Select` to only the columns the caller needs. Materialising a
  whole entity to read two fields pulls every column across the wire
- Explicit `Include` for the data you need. Lazy loading turns one query into
  one per row, and the symptom appears only under load
- `DbContext` is not thread-safe and must not be shared across concurrent work.
  In desktop code that means one context per unit of work, not one per window
- Async EF methods (`ToListAsync`, `SaveChangesAsync`) on any I/O path

## Reviewer Criteria (additional)

- **N+1 queries.** A query inside a loop over a previous query's results. This
  is the single most common EF defect and it is invisible in a code review that
  reads one method at a time
- Client-side evaluation: a `Where` or `OrderBy` that EF cannot translate pulls
  the whole table into memory first. Check anything calling a local method or a
  custom function inside a query
- Tracking behaviour matches intent: entities read for display should not be
  tracked, entities read for update must be
- Query filters and soft-delete: verify a global query filter is not being
  bypassed accidentally, or applied twice
- `FromSqlRaw` and `ExecuteSqlRaw` use interpolated parameters, never string
  concatenation
- Transactions: multi-step writes that must succeed together are in one
  `SaveChanges` or an explicit transaction
- Connection resiliency and retry policy configured for a remote database
- Pagination on any query whose result set can grow unbounded

## Tester Criteria (additional)

- Test against a real provider, not only the in-memory provider. The in-memory
  provider does not enforce relational constraints, so it passes on data a real
  database rejects. SQLite in-memory or a container is closer to the truth
- Migrations apply cleanly from an empty database **and** from the previous
  released schema. Only the second catches a broken upgrade path
- Concurrency: a test that exercises the optimistic-concurrency path when the
  model uses a rowversion or concurrency token
- Seed data runs idempotently, so a second deploy does not duplicate it

## Security Auditor Criteria (additional)

- Raw SQL: every `FromSqlRaw` / `ExecuteSqlRaw` call site uses parameters. String
  interpolation into these is SQL injection with extra steps
- Mass assignment: binding a request model straight onto an entity lets a caller
  set fields the form never showed, including keys and audit columns
- Connection strings come from configuration or a secret store, never from
  source, and never appear in an exception surfaced to a user
- Row-level access: verify a query filtered by the current user cannot be
  widened by a caller-supplied predicate or id
- Sensitive-data logging is off in production. EF logs parameter values when it
  is enabled, which puts real data in the log

## Project Manager Criteria (additional)

- Every migration in the change is reversible, or its irreversibility is stated
  deliberately with a plan
- Data-loss check: a migration dropping a column or narrowing a type needs an
  explicit decision, not a generated default
- Migration and deployment order relative to the application, so the running
  version tolerates the new schema during rollout
- Long-running migrations against a production-sized table are a maintenance
  window, not a deploy step
