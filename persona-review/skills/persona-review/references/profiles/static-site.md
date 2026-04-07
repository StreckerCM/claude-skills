---
name: static-site
display_name: "Static Site (Astro / Eleventy)"
build_command: "npm run build"
test_command: ""
rotation_size: 4
personas: [implementer, reviewer, ui-ux-designer, project-manager]
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

## Project Manager Criteria
- Content accuracy: verify text, links, and contact information
- Deployment pipeline: build succeeds in CI
- Sitemap/robots.txt configuration correct for production domain
- Analytics/tracking code present if required
- Legal pages (privacy policy, terms) are linked and current
