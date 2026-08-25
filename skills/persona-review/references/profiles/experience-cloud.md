---
name: experience-cloud
display_name: "Salesforce Experience Cloud (Overlay)"
type: overlay
applies_to: [salesforce]
---

# Experience Cloud Review Overlay

This is an **additive overlay**, not a standalone profile. These criteria are
appended to the Salesforce profile's criteria for each persona.

It applies when the project contains `experiences/` or `networks/` metadata. An
Experience Cloud site puts Salesforce data on the public internet, so the guest
user is an unauthenticated stranger with a profile. Most of the weight below is
on the Security Auditor for that reason.

## Implementer Criteria (additional)

- Guest users cannot own records (Winter '21 onward). Any flow or Apex that
  assigns ownership to the running user breaks for guest traffic
- Apex called from a guest context must be `without sharing` only when
  deliberate, and the reason belongs in a comment
- Use `@AuraEnabled(cacheable=true)` for read-only guest queries so the page
  does not hit the server on every render
- Site-facing components should degrade when a field is inaccessible rather than
  throwing, since guest FLS is narrower than any internal profile
- LWR templates do not support Aura components; verify the component type
  matches the template

## Reviewer Criteria (additional)

- Distinguish public pages from authenticated pages, and confirm each page's
  audience matches what its components expose
- Guest user queries need explicit `LIMIT`, since an anonymous caller controls
  the request rate
- Verify the site's error pages do not leak stack traces or org details
- Check that the same component is not implemented twice, once for internal
  users and once for the site, where one parameterised component would do
- Self-registration and login flows: verify the handler assigns the intended
  profile and permission sets, not a broader default

## Tester Criteria (additional)

- Test as the guest user with `System.runAs`, not only as an admin. Guest access
  is the path that ships broken
- Test with the site's sharing set and sharing rules in place, not with data the
  running test user happens to own
- Cover the unauthenticated path for every public endpoint the change adds
- Verify a guest cannot reach a record outside the sharing set, and assert the
  failure rather than assuming it

## UI/UX Designer Criteria (additional)

- Public pages are the org's front door: verify branding set, theme and
  responsive behaviour on a real mobile viewport
- Login, self-registration, forgot-password and error pages are part of the
  design surface and are usually the least reviewed
- Accessibility matters more here than internally, because the audience is
  unknown and unsupported
- SEO for public pages: page titles, meta description, and a URL that reads
- Guest-visible empty states: an anonymous visitor who sees an empty list needs
  to know whether that means "nothing here" or "please log in"

## Security Auditor Criteria (additional)

- **Guest user sharing.** Verify "Secure guest user record access" is on, and
  that every guest sharing rule grants Read only and is scoped as narrowly as
  the site allows
- **Guest profile permissions.** Review object and field permissions on the
  guest profile against what the site actually renders. Guest FLS is the single
  most common Experience Cloud data leak
- **Guest-callable Apex.** Every `@AuraEnabled` method reachable by a guest is
  an unauthenticated public endpoint. Enumerate them and treat them as such
- **No ID-in-URL trust.** A guest-reachable method that accepts a record id and
  queries it `without sharing` is an enumeration vulnerability
- **CSP and Trusted Sites.** Verify script and connect sources are declared
  rather than the policy being relaxed to make something work
- **Clickjack protection** enabled for the site
- **Rate limiting and CAPTCHA** on self-registration and any guest-writable form
- **File and attachment access:** verify guests cannot reach ContentDocument or
  Attachment records through a related list or a direct id
- No PII in a guest-reachable field set, and no internal-only fields on a
  public page layout

## Project Manager Criteria (additional)

- Site activation state and the deployment order between the site, its pages and
  its guest profile
- Custom domain, certificate and DNS steps that are outside the metadata deploy
- Communities licence consumption when the change adds authenticated site users
- A rollback plan that accounts for the site being publicly reachable during the
  window
