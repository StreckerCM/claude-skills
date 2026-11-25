---
name: data-loss
display_name: "Data loss"
skip_personas: [ui-ux-designer]
hotspots:
  - 'DELETE FROM'
  - 'DROP (TABLE|INDEX|TRIGGER)'
  - 'INSERT OR REPLACE|REPLACE INTO'
  - 'UPDATE [A-Za-z_]+ SET'
  - 'executescript\('
  - '\.unlink\(|os\.remove\(|shutil\.rmtree\(|rmtree\('
  - 'os\.replace\(|os\.rename\(|shutil\.move\(|tmp\w*\.replace\(|\.rename\('
  - 'open\([^)]*["'']w|write_text\(|write_bytes\(|np\.save\('
  - 'journal_mode|PRAGMA'
  - 'commit\(\)|rollback\(\)|BEGIN'
  - 'except (Exception|BaseException)?\s*(as \w+)?:\s*(pass|continue|return.*)?$'
---

# Focus: data loss

Data loss is any path by which data the user cares about ends up deleted,
overwritten, truncated, silently dropped, or unrecoverably corrupted. Count
derived data too when rebuilding it is expensive or lossy (indexes that take
hours, model outputs that cost GPU time), and count user-entered data above
everything (manual overrides, favourites, labels), because nothing can
rebuild it.

## What counts

- **Destroy before validate.** A delete, truncate or overwrite that runs
  before the inputs are confirmed to exist and parse.
- **Destroy before replace.** Old data removed, or metadata committed, before
  the new data is fully written. The safe order is write new, then swap, then
  delete old.
- **Whole-row replace.** `INSERT OR REPLACE` / `REPLACE` deletes the row and
  reinserts only the listed columns; every unlisted column is lost. An upsert
  that names its columns does not have this problem.
- **Non-atomic writes.** Writing in place, with no temp-file-and-rename, so a
  crash or a full disk leaves a truncated file. Check the temp file is cleaned
  up on failure.
- **Partial commits.** A failure midway that commits half the work. Look for
  `finally` blocks and helpers that commit implicitly (`executescript`, DDL).
- **Swallowed failures.** `except Exception: pass`, or a fallback that turns
  "could not read" into "nothing there", which a later step then acts on as
  if it were true (deletes, marks done, never retries).
- **Destructive migrations and cleanups** that run automatically, on every
  start, without a flag or a dry run.
- **Dry runs that write.** A dry run that changes anything at all, including
  pragmas and journal mode.
- **Identity collisions.** Two records mapped to one key, file name, row
  number or vector row, so one silently overwrites the other.
- **Lossy transforms stored over the original.** Cleanup, normalisation or
  segmentation written back in place, with no copy of the source.

## Hunt first, then read

Search the scope for the hotspot patterns listed in this preset before
reading anything in order. For every hit, read the whole function and its
callers until you can say what is destroyed, when, and what has been
confirmed by then. Read the rest of the scope only as time allows.

Say in your summary which patterns you searched for, how many hits there
were, and which you read in full. A focused review that silently skipped half
its hotspots is worse than one that says so.

## Each persona's angle

- **Implementer:** the ordering inside each write path. Validate, write new,
  swap, then delete old. Every connection, transaction and temp file is
  closed or cleaned up on failure.
- **Reviewer:** what the code assumes about the data it overwrites. Which
  columns or files exist that the writer does not know about? Which callers
  pass partial data?
- **Tester:** prove survival. For each destructive path, the test that fails
  when data is lost: interrupt it midway, feed it a missing input, run it
  twice, run it on a row with a manual override. Report destructive paths
  with no such test.
- **Security Auditor:** the same paths, driven by an attacker or by a synced
  or shared folder someone else can write: forged inputs that trigger a
  delete, files planted where a cleanup will remove the wrong thing,
  traversal that redirects a write.

## Severity

- **critical:** user-entered or irreplaceable data lost with no warning, on a
  path users run routinely.
- **high:** loss that needs an unusual but plausible condition (a crash, a
  typo, a missing mount), or loss of derived data that costs hours to
  rebuild.
- **medium:** recoverable loss, or loss only through misuse that the tool
  could easily have refused.
