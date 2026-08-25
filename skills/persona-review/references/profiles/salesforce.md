---
name: salesforce
display_name: "Salesforce (Apex / LWC / Flow)"
build_command: "sf project deploy validate"
test_command: "sf apex run test --test-level RunLocalTests"
rotation_size: 5
personas: [implementer, reviewer, tester, ui-ux-designer, security-auditor]
---

# Salesforce Review Profile

## Implementer Criteria

### Apex
- Bulk-safe patterns: no SOQL/DML inside loops
- Governor limit awareness: 100 SOQL, 150 DML, 50k query rows, 10s CPU sync
- Sharing rules: explicit `with sharing` or `without sharing` on every Apex class
- Trigger patterns: one trigger per object, handler class pattern
- Use Custom Labels for user-facing strings (i18n ready)
- Proper null checks on SObject field access
- Mixed DML: setup objects (User, Group, PermissionSet) and non-setup objects
  cannot be modified in one transaction; split with `System.runAs` or async

### Async Apex
- Pick the right mechanism: Queueable for chaining and sObject arguments, Batch
  for large data volumes, Schedulable for time-based, Platform Events for pub/sub
- Prefer Queueable over `@future`. `@future` cannot chain, cannot take sObject
  parameters, returns no job id, and is capped at 50 calls per transaction
- Callouts from async need `Database.AllowsCallouts` on the class
- `Database.Stateful` only when state genuinely crosses batch chunks; it is not
  free
- Batch scope sized deliberately, not left at the default when the work is heavy
- Chained Queueables need a Transaction Finalizer to handle their own failure

### Flow
- No Get, Create, Update or Delete Records element inside a loop. This is the
  declarative form of SOQL in a loop and fails the same way
- Before-save record-triggered flows for same-record field updates; after-save
  costs a full extra save cycle
- Every element that can fail has a fault path. Without one, a Flow fails
  silently and the user sees nothing
- No hardcoded record type, profile, queue or user IDs; use Custom Metadata or
  a Get Records lookup
- Reuse subflows rather than copying a set of elements into a second flow

### LWC
- Use `@wire` for reactive data, imperative calls for actions
- Handle the error branch of every wire adapter and imperative call

## Reviewer Criteria

### Apex
- SOQL in loops: flag any query inside a for/while loop
- DML limits: verify bulk operations use `Database.insert` with partial success
  where appropriate
- `with sharing` / `without sharing` correctness: verify it matches the use case
- Trigger handler pattern: no logic in trigger files
- API version: classes should target a current API version
- Check for hardcoded IDs (record types, profiles) — use Custom Metadata or
  Custom Settings instead
- Permission sets over profile permissions; Salesforce is retiring permissions
  on profiles

### Order of execution
- When an object has both an Apex trigger and a record-triggered Flow, work out
  what actually runs and in what order. This is where correctness dies
- Multiple record-triggered flows on one object: verify the flow trigger order
  is set explicitly, not left to chance
- Recursion across the boundary: a Flow updating a record that fires a trigger
  that updates a record that re-fires the Flow
- Before-save flow field changes are visible to after-save triggers; confirm
  that is intended

### Query performance
- Selectivity on large objects: a filter on a non-indexed field against a
  million-row object will not scale, whatever the governor limits say
- Standard indexed fields: Id, Name, OwnerId, CreatedDate, and external ID or
  unique fields. Formula fields and text areas are not indexed
- `LIMIT` and selective `WHERE` on anything that could grow unbounded

### Async
- `@future` in new code: ask why it is not Queueable
- Queueable chaining depth and whether the chain can be entered twice
- Batch `start` returning a QueryLocator, not a List, when the volume is real

### Flow
- Fault path coverage: which elements can fail and what the user sees when they do
- Entry criteria tight enough that the flow does not run on every save
- Flow formula and decision logic that duplicates Apex already in the org

### LWC
- Verify `@track` and `@api` usage follows current best practices
- Duplicate logic between an LWC and the Apex controller behind it

## Tester Criteria

### Apex
- `@isTest` data isolation: use `@TestSetup` or `Test.loadData`, not
  org-dependent data. Never `SeeAllData=true`
- Bulk test scenarios: test with 200+ records to verify governor limit compliance
- Mock HTTP callouts with `HttpCalloutMock` for external integrations
- Test both positive and negative paths (valid data, invalid data, missing
  permissions)
- Assert specific values, not just "didn't throw". Prefer the `Assert` class
  over `System.assertEquals` on current API versions, and give every assertion
  a message
- Test trigger recursion prevention
- `System.runAs` to cover the permission paths, not just the admin path
- Aim for 85%+ code coverage (Salesforce deployment minimum is 75%)

### Async
- `Test.startTest` / `Test.stopTest` around the call that enqueues async work,
  or the async never runs and the test asserts nothing
- Batch tests that exercise more than one chunk, not a single 200-record run
- Chained Queueables cannot chain in a test context; verify the test accounts
  for that rather than silently covering only the first link

### Flow
- Record-triggered flows have Flow tests (`.flowtest-meta.xml`). A flow with no
  test is untested automation carrying the same risk as untested Apex
- Flow fault paths are exercised, not just the happy path

### LWC
- Jest tests via `sfdx-lwc-jest` for every component with logic
- Mock the wire adapter and assert the rendered result, not just that the
  component mounts
- Assert on rendered output through `querySelector`, not on internal state

## UI/UX Designer Criteria

- LWC component design: proper use of Lightning Design System (SLDS) classes
- Lightning Design System compliance: use standard components before custom
- Mobile-first: test in the Salesforce mobile app, not just desktop
- Loading states: show spinners during wire/imperative calls
- Error handling UI: display user-friendly error messages from Apex exceptions
- Accessibility: SLDS components are accessible by default, verify custom markup
- Screen flows: label every input, put validation messages next to the field
  they concern, and confirm the Previous/Next path makes sense
- Screen flow error experience: a fault path that ends the flow with a raw
  system message is a broken screen, not an error state

## Security Auditor Criteria

- CRUD/FLS enforcement: check object and field-level permissions before DML.
  Prefer `WITH USER_MODE` on SOQL and `Security.stripInaccessible` over manual
  `isAccessible` chains
- Sharing model: verify `with sharing` is used unless explicitly needed otherwise
- Async Apex runs as System regardless of the caller; CRUD/FLS must still be
  enforced explicitly inside batch, queueable and scheduled classes
- Flow run context: a flow set to run in system context without sharing bypasses
  the running user's access entirely. Verify that is deliberate and necessary
- XSS in Visualforce: use `escape="true"`, avoid unescaped merge fields in
  JavaScript
- XSS in LWC: avoid `innerHTML`, use template expressions
- SOQL injection: use bind variables, not string concatenation in queries
- External callout security: verify endpoint URLs are in Named Credentials, or
  Remote Site Settings where a Named Credential is not possible
- Sensitive data: no PII in debug logs, no credentials in Custom Settings
- Permission set assignments granted by this change: verify each one is the
  least privilege that works, and that none grants Modify All or View All

## Project Manager Criteria

- Sandbox strategy: verify changes work in sandbox before production
- Deployment dependencies: `package.xml` includes all metadata
- Metadata coverage: no missing components that would cause deployment failure
- Destructive changes: verify any deleted metadata is in `destructiveChanges.xml`
- Test coverage report: all classes meet the minimum coverage threshold
- Flow versioning: deploying a flow creates a new version and does not activate
  it by default. Confirm the activation step is planned, or the change ships inert
- Scheduled jobs: a deploy cannot replace a class with scheduled jobs against it.
  Confirm the abort-and-reschedule step is in the plan
- Async capacity: the org has a daily async execution limit. A new batch or
  scheduled job that fans out is a capacity decision, not just a code change
