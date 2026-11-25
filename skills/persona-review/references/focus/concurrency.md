---
name: concurrency
display_name: "Concurrency"
skip_personas: [ui-ux-designer]
hotspots:
  - 'Thread|ThreadPool|ProcessPool|concurrent\.futures|multiprocessing|asyncio'
  - 'Lock\(|RLock|Semaphore|Event\(|Queue\('
  - 'lru_cache|cache|_CACHE|global '
  - 'sqlite3\.connect|check_same_thread|isolation_level|BEGIN|WAL'
  - 'CREATE (TABLE|INDEX|VIRTUAL TABLE)(?! IF NOT EXISTS)'
  - 'os\.replace|rename|tempfile|\.tmp'
  - 'threaded=|app\.run|waitress|gunicorn'
---

# Focus: concurrency

Concurrency problems appear when two things run at once: two web requests,
a CLI command while the server is up, a sync client writing the same folder,
worker threads inside one job.

## What counts

- **Check-then-act races.** "If the table does not exist, create it", "if the
  file is missing, write it", run by two requests at once.
- **Shared mutable state** in module globals or caches, mutated from request
  handlers or worker threads without a lock.
- **SQLite misuse across threads or processes.** Connections shared between
  threads, long write transactions blocking readers, WAL on network
  filesystems, read paths that write.
- **Temp-file collisions.** Fixed temp names two processes can both use.
- **Interrupted work.** Ctrl-C or a killed worker leaving locks held, partial
  files, or executors that wait for their whole queue.

## Hunt first, then read

Search for the hotspot patterns first. For each, name the two actors that can
run at once and what each sees. Say which patterns you searched and which hits
you read in full.

## Severity

- **critical:** corruption or loss under normal concurrent use.
- **high:** a 500, a deadlock or a wrong answer under plausible concurrency
  (two browser tabs, the CLI and the server together).
- **medium:** problems only under unusual load or timing.
