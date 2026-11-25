---
name: power-query
display_name: "Power Query (M) / Power BI Models"
build_command: ""
test_command: ""
rotation_size: 4
personas: [implementer, reviewer, tester, security-auditor]
---

# Power Query Review Profile

## Review notes

The reviewed artefacts are Power Query M queries. They are usually one query
per `.pq` file, sometimes alongside an exported dump of the whole model, or
embedded in a Power BI project (`.pbip` with `.tmdl` files). Queries refer to
each other by name. `#"Query Name"` and bare `QueryName` are the same
reference, so a query's dependencies are the other query names it mentions.

No reviewer can evaluate M offline. There is no runtime here, no data source,
and no credentials. So claims about query results are `traced` at best. Two
things can still be `observed`:

- A Python probe that parses the files: it resolves every query reference to
  an existing query, lists the functions each query calls, or diffs the `.pq`
  files against the dump.
- Re-implementing a small piece of logic in Python with hand-made rows, to
  show what a join or grouping does on a crafted input.

Say which you did.

The repository's conventions file or README usually records:
- the group numbering
- which queries load
- how `.pq` files are synced to the live model
- the open questions owned by the business

Treat a recorded owner decision as binding, and an open question as open.

## Implementer Criteria
- **Types.**
  - Every staging and report query sets column types explicitly
    (`Table.TransformColumnTypes`), with a culture argument wherever text is
    parsed into numbers or dates.
  - Columns left as `any` load as text, and break sorting and DAX.
- **Errors.**
  - `try ... otherwise`, `Table.RemoveRowsWithErrors` and
    `Table.ReplaceErrorValues` hide data defects. Each use needs a reason. A
    QA query that surfaces the error is better.
  - `MissingField.Ignore` and `MissingField.UseNull` on a column the logic
    depends on turn a schema change into wrong numbers.
- **Joins.**
  - Check the `Table.NestedJoin` or `Table.Join` kind against intent.
  - A non-unique key on the lookup side multiplies rows after the expand.
  - A left-anti or inner join drops rows silently.
  - Key columns must be the same type and the same case and trim. Use
    `Text.Upper` and `Text.Trim`, or a shared cleaning function.
- **Determinism.**
  - `Table.Distinct` and `Table.Group` after a `Table.Sort` do not keep the
    first sorted row unless the table is buffered (`Table.Buffer`) first.
  - "Keep latest record" logic must not depend on unbuffered sort order.
- **Nulls.**
  - Arithmetic with null yields null.
  - `List.Sum` of an all-null list returns null.
  - Comparisons with null are false.
  - Check that aggregates and conditions handle a missing value as intended.
- **Dates and times.**
  - `DateTime.LocalNow` and `DateTimeZone.LocalNow` evaluate in the refresh
    service's time zone, which is UTC in the Power BI service.
  - Time-zone and daylight-saving helpers must be correct on both changeover
    days.
  - Date-only comparisons must not be tripped by a time component.
- **Query folding and performance.**
  - Filters and column selection come before steps that break folding.
  - `SharePoint.Files` over a whole site, then filtered to one folder, is
    slow; prefer `SharePoint.Contents` navigation or one shared navigation
    query.
  - Buffer only deliberately.
- **Combine Files.** Helper queries (`Transform Sample File` and `Parameter`)
  that nothing references are dead. A combine that takes its schema from a
  single sample file breaks when a file's layout differs.
- **Parameters.** Values that vary by environment or are business thresholds
  are parameters or configuration queries, not literals inside a step.

## Reviewer Criteria
- **Duplicated logic.** Parsers, cleaners and time-zone helpers copied across
  queries or models drift apart. Name the copy that should survive as the
  shared function, and check that a fix applied to one copy reached the
  others.
- **Hard-coded rules.** Plants, material groups, storage locations, excluded
  documents and magic dates belong in configuration queries, in one place.
- **Positional fragility.**
  - Columns referenced by position, or by an auto-generated name such as
    `Column1` or `Data.Column7`.
  - `Table.PromoteHeaders` on a source whose header row can move.
  - Row skips (`Table.Skip`) counted for one export layout.
- **Business logic.**
  - Classification and comparison rules must match the model README and any
    owner decision: stockout versus safety stock, current versus previous
    report, and what counts as a change.
  - Comparisons must use the right report pair, the right snapshot and the
    right boundary (`<` versus `<=`).
- **Load settings.** Only consumed tables load. Staging, function and
  parameter queries do not. A loaded table that nothing consumes costs
  refresh time.
- **Sync.** Where the repository keeps the `.pq` source ahead of the live
  model and records the sync, the record must be current for the queries in
  scope.

## Tester Criteria
- **QA queries.**
  - Check what QA or validation queries exist: duplicate-key checks, row-count
    reconciliation between stages, source freshness, and expected columns
    present.
  - For each transformation rule in scope, name the QA query that would catch
    its failure, or report that none does.
- **Edge sources.** For each source, trace what happens on:
  - an empty file
  - a missing expected column
  - an extra column
  - a duplicate key
  - a blank or text value in a numeric column
  - the first run, with no previous snapshot
  - a report that did not arrive today
  - a daylight-saving changeover day
- **Hand-checkable cases.** For each comparison or classification, give at
  least one crafted input with its expected output. A reviewer can show the
  rule wrong by reproducing it in Python on that input.
- **Known-answer data.** Note whether there is a sample-data fixture or a
  recorded known-good output to compare against after a change. Report its
  absence as a coverage gap.

## Security Auditor Criteria
- **Credentials.**
  - No credentials, API keys or connection strings with passwords appear in
    query text.
  - `Web.Contents` takes keys through the `ApiKeyName` or `Headers` options
    backed by stored credentials, not in the URL.
- **Native queries.** `Value.NativeQuery` and `Sql.Database` with a `Query`
  option must not build SQL by concatenating parameter or data values.
- **Privacy levels.**
  - Combining sources with different privacy levels can send data from one
    source to another during folding.
  - A model that relies on "ignore privacy levels" must say so and why.
- **Sensitive data in the repository.**
  - Dumps, sample files and documentation must not hold real customer, employee
    or pricing data that should not be in version control.
  - Real tenant URLs and site names, if the conventions call for placeholders.
- **Outputs.** Report tables consumed by email or export flows must contain
  only the fields their audience should see.

## Project Manager Criteria
- Every query is described in its model README, along with its group and load
  setting.
- Changed queries are reflected in the repository's sync record, so someone
  knows to paste them into the live model.
- Fixes that depend on an open business question name that question and do not
  silently decide it.
- A change to a report table's columns names the downstream consumers: report
  visuals, DAX measures, and the flows or exports that read it.
