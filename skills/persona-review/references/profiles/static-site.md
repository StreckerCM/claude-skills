---
name: static-site
display_name: "Static Site (Astro / Eleventy)"
build_command: "npm run build"
test_command: ""
rotation_size: 4
personas: [implementer, reviewer, ui-ux-designer, security-auditor]
---

# Static Site Review Profile

## Implementer Criteria
- Component structure follows framework conventions (Astro components, Eleventy layouts)
- Build performance: avoid unnecessary client-side JavaScript
- Image optimization: use framework image components (Astro Image, responsive srcset)
- Content collections typed correctly (Astro) or data files structured properly (Eleventy)
- Proper use of static vs dynamic rendering (islands architecture in Astro)
- CSS scoping: component-scoped styles, no global style leaks
- No hardcoded URLs: use relative paths or config-based base URLs

## Reviewer Criteria
- SEO metadata: title, description, og:tags on every page
- Semantic HTML: proper heading hierarchy, landmark elements
- Bundle size: no unnecessary JavaScript shipped to client
- Dead code: unused components, styles, or data files
- Sitemap and robots.txt are generated and correct
- RSS feed if applicable
- 404 page exists and is styled

## UI/UX Designer Criteria
- Responsive layout: test at mobile (375px), tablet (768px), desktop (1280px+)
- Accessibility: alt text on images, skip navigation link, ARIA labels where needed
- Lighthouse scores: aim for 90+ on Performance, Accessibility, Best Practices, SEO
- Mobile UX: touch target sizes (min 44x44px), no horizontal scroll
- Typography: readable font sizes (min 16px body), proper line height
- Color contrast: WCAG AA minimum (4.5:1 for normal text)
- Dark mode support if the site uses it

## Security Auditor Criteria
- Security headers are configured for the host: Content-Security-Policy,
  X-Content-Type-Options, Referrer-Policy and HSTS. On a static host these
  live in `_headers`, `netlify.toml`, `vercel.json` or
  `staticwebapp.config.json`, not in application code, which is why they
  are routinely missing entirely
- Forms are the one real attack surface on a static site. Verify where the
  submission goes, that the endpoint is not an unauthenticated relay into
  an inbox, and that it has spam protection
- No secrets in client code. Anything in the built output is public,
  including an API key inlined at build time from an environment variable
- Third-party scripts: every analytics, chat, font or embed tag is code
  someone else controls, running on your domain. Confirm each is intended
  and pinned, with subresource integrity where the host supports it
- `target="_blank"` links carry `rel="noopener"`
- Verify the built output contains no source maps, `.env` files, draft
  content, or admin pages that were not meant to ship

## Project Manager Criteria
- Content accuracy: verify text, links, and contact information
- Deployment pipeline: build succeeds in CI
- Sitemap/robots.txt configuration correct for production domain
- Analytics/tracking code present if required
- Legal pages (privacy policy, terms) are linked and current
