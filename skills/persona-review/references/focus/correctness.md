---
name: correctness
display_name: "Correctness"
skip_personas: [ui-ux-designer]
hotspots:
  - 'OFFSET|has_more|next_offset|LIMIT \{|LIMIT \?|\[:\s*limit\]|\[offset'
  - 'GROUP BY|SELECT DISTINCT|COUNT\(\*\)'
  - 'ORDER BY'
  - "LIKE '%|LIKE \?|MATCH \?|REGEXP|ESCAPE"
  - "fromtimestamp|'unixepoch'|localtime|tzinfo|astimezone|978307200"
  - 'except (Exception|BaseException)?\s*(as \w+)?:\s*(pass|continue|return.*)?$'
  - '[^<]/ ?\(?(rng|denom|norm)\b|np\.linalg\.norm|\.norm\(|[^<]/ ?\(?len\('
---

# Focus: correctness

Correctness means the code returns the right answer: the right rows, the
right count, the right order, the right value, every time, including the
edges. A wrong answer the user cannot see is worse than a crash, because
nothing prompts anyone to look.

## What counts

- **Wrong rows.** Joins that multiply rows (one row per chat, per message,
  per attachment), filters that silently match everything when their input
  normalises to empty, prefix or suffix matches where an exact match was
  meant, unescaped wildcards.
- **Wrong counts.** Totals computed before filtering, after slicing, or over
  a prefilter broader than the real match. `has_more` that disagrees with
  what the next page returns.
- **Wrong order and pages.** Sorting before truncating (newest N instead of
  best N), ties with no unique tiebreaker, a ranking pool that changes with
  the page offset, offsets ignored on one branch.
- **Wrong values.** Scores on incomparable scales sorted together,
  normalisation that divides by zero or stretches noise, units and time zones
  mixed (UTC buckets against local filters, seconds against nanoseconds),
  float precision lost where integers would do.
- **Silent degradation.** A swallowed exception that turns "this feature
  failed" into "this feature found nothing", so results quietly get worse
  with no signal: an import that never resolves, a query the database
  rejects, a fallback that becomes permanent.
- **Inconsistent paths.** Two code paths for the same question (CLI and web,
  regex and substring, fan-out and single index) that give different answers.
- **Stale derived data.** Caches and mirrors refreshed on a heuristic (a row
  count) that misses real changes.

## Hunt first, then read

Correctness defects are less concentrated than data-loss ones, so the hotspot
map is a starting point here, not a boundary: query builders, ranking and
pagination code deserve a full read even where few patterns hit.

Search the scope for the hotspot patterns listed in this preset before
reading anything in order. For every hit, trace the value from its source to
where the user sees it, and ask what input makes it wrong. Prefer probes: a
small fixture that shows the wrong count or order is worth more than a
paragraph of reasoning.

Say in your summary which patterns you searched for, how many hits there
were, and which you traced in full.

## Each persona's angle

- **Implementer:** the arithmetic and the SQL. Every join, aggregate, slice
  and comparison, checked against what the caller assumes.
- **Reviewer:** paths that should agree and do not; swallowed errors that
  hide a wrong answer; duplicated logic that has drifted.
- **Tester:** known-answer tests. Hand-built inputs whose right output can be
  computed by hand, at the edges: empty, one, ties, the boundary value, the
  page boundary.
- **Security Auditor:** wrong answers an attacker can cause: inputs that make
  a filter match everything, values that poison a ranking, timestamps that
  land in the wrong bucket.

## Severity

- **critical:** wrong results on the main path, by default, with no signal.
- **high:** wrong results under common inputs (punctuation, ties,
  multi-chat messages, second pages), or a feature silently disabled.
- **medium:** wrong results only at rare edges, or counts that are off
  without affecting which rows are shown.
