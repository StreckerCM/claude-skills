---
name: power-automate
display_name: "Power Automate Cloud Flows"
build_command: ""
test_command: ""
rotation_size: 4
personas: [implementer, reviewer, tester, security-auditor]
---

# Power Automate Review Profile

## Review notes

The reviewed artefacts are exported cloud flows. The logic is in
`definition.json` and uses the Logic Apps workflow definition language:
`properties.definition` holds `triggers`, `actions`, `parameters` and `outputs`.
Each action has `type`, `inputs`, and a `runAfter` map that sets execution order
and failure handling. `Scope`, `If`, `Foreach`, `Until` and `Switch` nest further
`actions`. Beside the definition, `apisMap.json`, `connectionsMap.json` and the
package `manifest.json` map connectors and connections. Solution exports put the
same definitions under `Workflows/`.

No reviewer can run a flow. That needs the tenant, its connections and its data.
So runtime claims are `traced` at best. The JSON can be checked mechanically:
write a short Python probe that walks every action, resolves each `runAfter`
reference, and lists every expression. Results from such a probe are
`observed`.

Connector behaviour lives in Microsoft's services: default page sizes,
throttling, trigger semantics, and what an action returns when nothing
matches. A claim about it is `asserted` unless you cite the connector's
documentation. Say so plainly.

## Implementer Criteria
- **Error handling.**
  - Main work sits in a `Scope`, and a handler runs after it with `runAfter`
    covering `Failed` and `TimedOut` (and `Skipped` where relevant).
  - A handler that reports failure ends in `Terminate` with status `Failed`, so
    the run history doesn't show success.
  - An action that only runs on success of a step that can be skipped will
    never run. Trace every `runAfter` chain.
- **Expressions.**
  - Null-safe access: use `?[...]` or `coalesce()` on optional fields.
  - Trigger outputs and `body()` paths match the connector's actual output
    shape.
  - `first()` and indexing on arrays that can be empty.
  - `int()` and `float()` on text that can be blank.
  - `formatDateTime`, `utcNow` and `convertTimeZone` with an explicit time zone
    wherever a business day or schedule depends on it.
- **Loops and concurrency.**
  - `Foreach` runs in parallel by default when concurrency control is on.
    `SetVariable` or `AppendToArrayVariable` inside a parallel loop is a race.
    Set the degree of parallelism to 1, or use `Compose` or `Select` instead.
  - `Until` has a count and timeout limit, and the flow handles hitting that
    limit.
- **Pagination and limits.** List actions (SharePoint Get items or Get files,
  Dataverse List rows, Outlook) return a default page. A flow that needs every
  row turns pagination on with a threshold, or uses `$top` or a filter query. A
  silently truncated list is a defect.
- **Triggers.**
  - Polling and recurrence intervals fit the source.
  - Trigger conditions filter early, instead of a `Condition` after an
    expensive step.
  - For file and email triggers, decide how duplicates and re-deliveries are
    handled (idempotency).
- **Retry.** Actions calling flaky or throttled services carry a deliberate
  `retryPolicy`. Non-idempotent actions (send email, create item) are not
  retried blindly.
- **Prefer bulk actions.** Use `Filter array`, `Select` and `Join` instead of
  `Foreach` plus `Condition`, both for speed and for action-count limits.
- **Naming.** Every action has a descriptive name. Renaming an action changes
  every expression that references it, so check that none were left pointing
  at the old name.

## Reviewer Criteria
- **Hard-coded values.** Site URLs, list GUIDs, folder paths, mailbox
  addresses, recipients and thresholds that recur across flows belong in
  environment variables or one documented place. Check that the repository's
  anonymisation placeholders are used consistently.
- **Duplicated logic.** Near-identical notification or processing flows
  should share a child flow or a common pattern, and a fix applied to one
  should have reached its siblings.
- **Business rules.** Check filter queries, conditions and subject or file-name
  matching against the documented intent. Look for case sensitivity,
  `contains` matching more than intended, and date-boundary errors such as
  yesterday versus the last 24 hours, and the UTC day versus the local day.
- **Cross-flow contracts.** When one flow writes a file or folder another flow
  triggers on, check that names, paths and timing agree. Check that a refresh
  does not run before its source has landed, and that no flow triggers itself.
- **Email content.** HTML tables are built from escaped data. Subjects and
  bodies are correct when the source data is empty.
- **Package consistency.** The connectors in `manifest.json` and
  `connectionsMap.json` match the connectors the definition uses.

## Tester Criteria
- **Failure path.** Every flow has a reachable failure path, and that path
  notifies someone. The flow-failure alert is not enough on its own: the
  run can end `Succeeded` after a handled error.
- **Edge inputs.** For each flow, trace what happens on:
  - an empty list or no matching rows
  - an email with no attachments
  - an attachment with an unexpected name or extension
  - a file that already exists
  - a source report that arrived twice, late, or not at all
  - a DST change day
  - a value with commas, quotes or HTML in it
- **Test record.** Check whether a test procedure or run record exists: sample
  inputs, and the expected outputs or emails. Report its absence as a
  coverage gap, not as a code defect.
- **Probe.** A probe that resolves every `runAfter` target and every
  `body('X')`, `outputs('X')` and `items('X')` reference to an existing action
  name is cheap, and it catches renamed-action breakage. Write it.

## Security Auditor Criteria
- **Secrets.**
  - No passwords, API keys, SAS tokens or bearer tokens appear in the
    definition or in action inputs.
  - HTTP actions take credentials from a connection, Key Vault or a secure
    environment variable, and those actions set `secureInputs` and
    `secureOutputs` so run history does not keep them.
- **Tenant data in the repository.** Check for real tenant hosts, mailbox
  addresses, user names, connection names or GUIDs that the repository's
  anonymisation convention says must be placeholders. Check that build
  artefacts carrying real values are git-ignored.
- **Shared mailbox and email triggers.**
  - Filter on the sender, or on an allow-list, before acting on attachment
    content.
  - Never forward or save attachments from arbitrary senders into locations
    that feed reports.
- **Outbound data.**
  - Recipients come from configuration, not from email content.
  - Reports with sensitive fields go only to intended audiences.
  - A `Send an HTTP request` action or HTTP connector to an external origin is
    justified and documented.
- **Connections.** Embedded connections run as their owner. Note which
  identity each connection runs as, and flag a personal account used for a
  production flow.
- **Data loss prevention.** Combining business and non-business connectors in
  one flow may be blocked, or worse, allowed when it should not be. Flag
  unusual combinations.

## Project Manager Criteria
- The README's inventory and flow diagram list every flow, and each flow's
  trigger and its downstream consumers.
- A new placeholder or connection is documented for the package build tool and
  the import steps.
- A change to a file name, folder or schedule that another flow or a Power BI
  dataset depends on names that dependency and is coordinated with it.
- A flow's owner and its failure-notification recipients are documented.
