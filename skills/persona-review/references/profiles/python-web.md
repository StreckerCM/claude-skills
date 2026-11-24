---
name: python-web
display_name: "Python Web App (Overlay)"
type: overlay
applies_to: [python-tools]
adds_personas: [ui-ux-designer]
---

# Python Web App Review Overlay

This is an **additive overlay**, not a standalone profile. These criteria are
appended to the base stack profile's criteria for each persona.

It is detected when a Python project depends on a web framework (Flask, Django,
FastAPI, Starlette, Quart). The base `python-tools` criteria are written for
command-line tools and say nothing about requests, templates, browsers or the
network, so without this overlay a web app is reviewed as though it had no
attack surface and no user interface. It also adds the UI/UX Designer to the
rotation, which in turn loads the accessibility overlay.

## Three things to get right before anything else

**Local does not mean private.** A tool that serves a personal archive "only on
localhost" is still reachable from every web page the owner visits, through DNS
rebinding and cross-site requests, unless it checks the Host header and the
request origin. Once it binds `0.0.0.0` for a phone or another machine, it is
reachable by everything on the network. Review the bind address and the auth
story first, because every other finding is worse when either is missing.

**Everything a file route serves is a document on your origin.** A file served
inline with a type of `text/html`, `image/svg+xml` or any XML type runs script
with the app's full authority. Where the type comes from data the app did not
create — an upload, a received attachment, a guessed extension — that is stored
XSS, however carefully the templates escape.

**Autoescaping protects templates, not everything that reaches the browser.**
`|safe`, `Markup()`, `mark_safe`, f-string HTML returned from a view, and
`innerHTML` in the page's own JavaScript all bypass it. Each one is a sink to
trace back to its source.

## Implementer Criteria (additional)

- Use an app factory, and keep configuration out of module import side effects
- Database connections are opened per request and closed in `finally`, a
  context manager, or a teardown hook — never only on the happy path
- Code on the request path never calls `sys.exit()` or relies on CLI helpers
  that do; a missing resource becomes a 4xx/5xx response, not a dead worker
- Request parameters are parsed through one helper per type that rejects
  NaN/inf, falls back on parse errors and clamps to a range. `?limit=-1` must
  not reach SQL as `LIMIT -1`
- Responses for the same failure look the same across routes: an htmx fragment
  route returns a fragment with a 4xx status, not a full error page
- Long-running work (transcodes, model calls, regex over a whole archive) has a
  request-wide time budget, not just a per-item one
- Use `logging`, not `print`, so a server's output can be routed and filtered

## Reviewer Criteria (additional)

- Every numeric query parameter is clamped; every date or regex parameter has a
  400 path that every route shares
- Pagination counts and `has_more` are computed after any filtering, not before
- Duplicate route logic: two routes serving the same kind of thing (a main and
  an "orphan" variant, a page and its fragment) through copied code
- Caches written to disk are versioned and fail open: a corrupt or old-shaped
  entry is a miss, never a 500
- Development-server use (`app.run`, `manage.py runserver`, `debug=True`) is
  confined to development and never the documented way to serve it
- Templates and views agree on what is already escaped; a value is escaped
  exactly once

## Tester Criteria (additional)

- Use the framework test client against fixtures, never a real user dataset
- Hostile-input tests per route: negative, zero, huge and non-numeric paging
  values; malformed dates; a pathological regex; unknown ids
- A lint test that lists every `|safe`, `Markup(` and `mark_safe` site and fails
  on a new one not on an allow-list
- File routes: a `Range` request returns 206 with `Content-Range`; a failed
  transcode falls back cleanly; an HTML- or SVG-typed row is served as a
  download
- Security behaviour has tests: a foreign `Host` header is rejected, a
  cross-origin POST is rejected, and auth (if any) cannot be bypassed
- Client-side JavaScript that builds HTML has tests too, even a small node
  harness, because a test suite that renders only server HTML misses it

## Security Auditor Criteria (additional)

- **Bind address and authentication.** What does the server bind to by default
  and in its documented mode? Anything beyond loopback needs authentication,
  and a production-grade server rather than the framework's development server
- **Host header.** Reject requests whose `Host` is not an expected name, or DNS
  rebinding turns a loopback-only app into one any web page can read
- **CSRF.** Every state-changing request checks `Origin` / `Sec-Fetch-Site` or a
  token. A GET must not change state, including writing history or logs that
  later render
- **File serving.** Serve inline only an allowlist of media types. Everything
  else, and always `image/svg+xml`, `text/html` and XML, goes out as
  `as_attachment` with `application/octet-stream`. Set
  `X-Content-Type-Options: nosniff` and `Content-Security-Policy: sandbox` on
  file responses. Resolve paths strictly and confirm they stay under an allowed
  root
- **Response headers.** `nosniff`, `frame-ancestors 'none'` or
  `X-Frame-Options: DENY`, `Referrer-Policy`, and a CSP. Inline `on*=` handlers
  and inline scripts block a `script-src 'self'` policy, so count them
- **Deserialization.** No `pickle` of anything stored where another user, a
  sync client or a share could write it — including the app's own caches
- **Error output.** Exceptions and file paths are logged, not reflected
- **Secrets.** Framework `SECRET_KEY` is not hard-coded or defaulted

## UI/UX Designer Criteria (additional)

- Responsive layout at 375px, 768px and 1280px+, with no horizontal scroll
- Touch targets at least 44 by 44 px on phone layouts; at least 24 by 24
  everywhere (2.5.8)
- Body text at least 16px on phones, with sizes in rem so text-only zoom works
- Contrast: 4.5:1 for text, 3:1 for control boundaries, checked separately for
  every surface colour and for dark mode
- Every failed request is visible: a 5xx or network error replaces the stale
  result with an error message, never leaves the old one looking current
- Partial-page swaps (htmx, fetch) announce what changed through a live region
  and move focus deliberately, and update the document title on navigation
- Empty states and error states say what happened and what to do next

## Stack notes

### Flask
- `send_file(..., mimetype=...)` serves inline by default; `as_attachment=True`
  is opt-in
- `TRUSTED_HOSTS` exists only from Flask 3.1; on older pins, check `Host` in a
  `before_request` hook
- `app.run(host="0.0.0.0")` is the Werkzeug development server

### Django
- Check `ALLOWED_HOSTS`, `DEBUG`, `CSRF_TRUSTED_ORIGINS` and whether
  `@csrf_exempt` appears anywhere
- `mark_safe` and `|safe` are the escape hatches to trace
- `FileResponse` needs `as_attachment=True` for untrusted content

### FastAPI / Starlette
- No CSRF protection by default for cookie-authenticated routes
- `TrustedHostMiddleware` is the Host-header check
- `FileResponse` takes `media_type` from the caller; it does not sniff safely
