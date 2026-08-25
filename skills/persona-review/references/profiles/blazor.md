---
name: blazor
display_name: "Blazor (Overlay)"
type: overlay
applies_to: [aspnet-web, dotnet-desktop]
---

# Blazor Review Overlay

This is an **additive overlay**, not a standalone profile. These criteria are
appended to the base stack profile's criteria for each persona.

It applies when the project contains `.razor` components. Blazor is not Razor
Pages with more syntax: components are stateful and long-lived, the render mode
decides where code actually runs, and a Server circuit holds memory per
connected user. Most Blazor defects come from reviewing it as though it were
request-response.

## Implementer Criteria (additional)

- Render mode is chosen deliberately per component: static, Server,
  WebAssembly, or Auto. It determines where the code runs and what it may touch
- Prerendering runs `OnInitializedAsync` **twice**, once on the server and once
  after the interactive connection. Any side effect there happens twice unless
  guarded
- Implement `IDisposable` or `IAsyncDisposable` on any component that
  subscribes to an event, starts a timer, or registers a JS callback. A
  component that does not unsubscribe leaks for the life of the circuit
- `@key` on every element rendered from a collection that can reorder, or the
  diff reuses the wrong element and state attaches to the wrong row
- `EventCallback` rather than `Action` for child-to-parent events, so
  `StateHasChanged` runs automatically
- `StateHasChanged` only where the framework will not already re-render, such as
  a callback from a timer or an external event

## Reviewer Criteria (additional)

- Component lifecycle correctness: work that belongs in `OnInitializedAsync`
  versus `OnParametersSetAsync`, which runs on every parameter change
- `[Parameter]` properties are set by the framework and must not be mutated
  inside the component
- Blazor Server: state held in a component or a scoped service lives for the
  whole circuit, which is the user's session, not a request
- `async void` in a component is the same defect as anywhere else, and here it
  takes down the circuit rather than surfacing an error
- JS interop calls are disposed, and none run during prerendering, where there
  is no browser to call
- Long-running work started from a lifecycle method is cancelled on disposal
- Duplicate logic between a component and the service behind it

## Tester Criteria (additional)

- Component tests with bUnit for anything with rendering logic. Testing only the
  service behind a component leaves the component untested
- Assert on rendered markup, not on component fields
- Cover the prerender-then-interactive path for components that fetch on
  initialise, since that is where double-execution shows up
- Test the disposal path: after disposing, subscriptions are released and no
  callback fires

## UI/UX Designer Criteria (additional)

- Loading state for every await in a lifecycle method. Without one the component
  renders empty and then jumps
- Blazor Server reconnection: the default "attempting to reconnect" overlay is
  unstyled and jarring. Verify it has been considered
- Error boundaries around components that can throw, so one failure does not
  blank the page
- Form validation uses `EditForm` with a validator and shows messages next to
  the field, not only in a summary
- Disable the submit button while a request is in flight, or the user
  double-submits
- Keyboard focus after navigation and after a dialog closes

## Security Auditor Criteria (additional)

- **WebAssembly runs on the client.** Anything in a WASM component is readable
  by the user: no secrets, no API keys, and no authorisation decision that
  matters
- Authorisation is enforced in the API or service, not only by hiding UI with
  `AuthorizeView`. Hidden markup is not access control
- `MarkupString` renders raw HTML and is an XSS vector wherever its input is
  not fully trusted
- Blazor Server sends every UI event over the circuit: validate the payload
  server-side, since a caller can send values no rendered control offered
- `[Parameter]` values arriving from a route are user input and need the same
  validation as a query string
