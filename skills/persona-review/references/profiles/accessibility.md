---
name: accessibility
display_name: "Accessibility — WCAG 2.2 AA (Overlay)"
type: overlay
applies_to: [static-site, aspnet-web, dotnet-desktop, salesforce]
loaded_when: ui-ux-designer is in the rotation
---

# Accessibility Review Overlay

This is an **additive overlay**, not a standalone profile. These criteria are
appended to the base stack profile's criteria for each persona.

It is not detected from the code. Load it whenever `ui-ux-designer` is in the
rotation: any project with a user interface has an accessibility surface.

The target is **WCAG 2.2 Level AA**. Cite the success criterion in a finding —
"2.4.7 Focus Visible", not "focus is hard to see" — so the reader can look it up
and so the finding survives a disagreement.

## Two things to get right before anything else

**Automated tools find roughly a third of WCAG failures.** axe, Lighthouse and
pa11y detect what is machine-checkable: a missing `alt`, a contrast ratio, a
form control with no accessible name. They cannot judge whether alt text is
*meaningful*, whether focus order matches the visual order, whether an error is
announced, or whether a custom widget behaves like the thing it imitates. A
perfect automated score is a floor, never a pass. Never report one as evidence
the interface is accessible.

**The first rule of ARIA is not to use ARIA.** A native `<button>`, `<a href>`,
`<label>` or `<input type="checkbox">` carries role, state and keyboard
behaviour for free. A `<div role="button">` carries the role and nothing else,
and now you owe Enter, Space, focus and disabled handling. Incorrect ARIA is
worse than none, because it overrides what the browser already knew. Treat every
ARIA attribute in a diff as something to justify, not something to approve.

## Implementer Criteria (additional)

- Use the native element. Reach for ARIA only when no native element has the
  semantics you need, and say why in a comment
- Every interactive control is reachable and operable by keyboard alone.
  Anything with a click handler needs a keyboard path (2.1.1)
- Every form control has a programmatically associated label — `<label for>`, a
  wrapping `<label>`, or `aria-labelledby`. Placeholder text is not a label
- Images carry `alt`. Decorative images carry `alt=""` so they are skipped, and
  informative images describe the information, not the picture
- Do not remove the focus outline without replacing it with something at least
  as visible (2.4.7, 2.4.11)
- Headings describe structure, not size. Never skip a level to get smaller text
- Colour is never the only way information is conveyed (1.4.1)
- Respect `prefers-reduced-motion` for any animation, parallax or auto-playing
  transition (2.3.3)

## Reviewer Criteria (additional)

- One `<h1>` per page and no skipped heading levels
- Landmarks present and used once each where singular: `<header>`, `<nav>`,
  `<main>`, `<footer>`. A skip link targets `<main>`
- Lists marked up as lists, tables as tables with `<th>` and scope. A table used
  for layout is a finding
- `lang` set on `<html>`, and on any element in a different language (3.1.1)
- Link text makes sense out of context. "Read more" repeated eight times gives a
  screen-reader user eight identical links (2.4.4)
- Dynamic content that appears without a page load is announced: a live region
  for status messages, or focus moved deliberately to the new content (4.1.3)
- Custom widgets implement the full keyboard pattern for the role they claim.
  A combobox that does not handle Arrow keys is not a combobox
- No positive `tabindex`. It overrides document order and never stays correct

## Tester Criteria (additional)

- Run an automated scan (axe-core, `@axe-core/playwright`, pa11y) in CI and fail
  the build on new violations. This is the floor, not the test
- **Keyboard pass:** Tab through the whole page. Every control is reachable,
  focus is always visible, the order matches the visual order, and nothing traps
  focus (2.1.2). This catches more real defects than any tool
- **Screen reader pass** on anything new or custom: NVDA or JAWS on Windows,
  VoiceOver on macOS. Confirm each control announces its name, role and state
- **Zoom to 400%** and confirm content reflows into one column with no
  horizontal scrolling and nothing clipped (1.4.10)
- Confirm the error path: a failed form moves or announces focus, and each
  message identifies the field it belongs to (3.3.1)
- Test with the OS in high-contrast or forced-colors mode
- Automated checks assert on the accessibility tree, not on CSS classes

## UI/UX Designer Criteria (additional)

- Contrast: 4.5:1 for body text, 3:1 for large text and for the boundary of any
  interactive control or meaningful graphic (1.4.3, 1.4.11)
- Focus indicators are visible against every background they appear on, not just
  the light theme (2.4.11)
- Target size at least 24 by 24 CSS pixels, or spaced so the effective area is
  (2.5.8). 44 by 44 is the comfortable figure for touch
- Error messages sit next to the field, say what is wrong and how to fix it, and
  never rely on red alone (3.3.3)
- Anything that reappears across steps — a previously entered value, a
  confirmation — is not re-entered from memory (3.3.7)
- Text is resizable to 200% without loss of content or function (1.4.4)
- Time limits are adjustable or absent (2.2.1)
- A drag interaction has a single-pointer alternative (2.5.7)
- Content revealed on hover or focus is dismissible, hoverable and persistent
  (1.4.13). A tooltip that vanishes when you move toward it is unusable
- Dark mode is checked for contrast separately. Palettes that pass in light mode
  routinely fail inverted

## Stack notes

### Web (static sites, ASP.NET, Blazor, Razor)
- Client-side routing must move focus and update the page title on navigation,
  or a screen-reader user is never told the page changed
- A modal traps focus while open, closes on Escape, and returns focus to the
  element that opened it
- `aria-live="polite"` for status, `assertive` only for genuine interruptions

### XAML (WPF and WinForms)
- `AutomationProperties.Name` on every control conveying meaning, and
  `LabeledBy` where a separate label element exists
- Verify the tree in Accessibility Insights for Windows, which is the desktop
  equivalent of an axe scan
- Keyboard access keys do not collide, and tab order follows the visual layout
  rather than the XAML declaration order
- Custom-drawn controls expose an automation peer, or they are invisible to
  assistive technology

### Salesforce (LWC, Aura, screen flows)
- Standard SLDS components ship accessible markup. That is a starting point, not
  a result: composition, labelling and focus order are still yours to get right,
  and a custom component built with SLDS *classes* has none of the behaviour
- Screen flow inputs are labelled, and a validation failure explains itself
  rather than showing a raw system message
- Test in the Salesforce mobile app, where the touch target and reflow criteria
  bite hardest
