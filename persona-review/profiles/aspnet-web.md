---
name: aspnet-web
display_name: "ASP.NET Web Application"
build_command: "dotnet build *.sln"
test_command: "dotnet test *.sln"
rotation_size: 6
personas: [implementer, reviewer, tester, ui-ux-designer, security-auditor, project-manager]
---

# ASP.NET Web Review Profile

## Implementer Criteria
- Follow existing project pattern (WebForms postback lifecycle, MVC controller patterns, or Razor Pages)
- Proper Session state management (avoid storing large objects)
- ViewState management in WebForms (minimize ViewState size, disable where not needed)
- Use async controller actions for I/O-bound operations
- Proper model binding and validation attributes
- Connection string management through configuration, not hardcoded

## Reviewer Criteria
- OWASP Top 10 compliance at every code change
- Authentication/authorization patterns: verify [Authorize] attributes, role checks
- Connection string and config management (no secrets in appsettings.json committed to git)
- Proper error handling: custom error pages, no stack traces in production
- Check for proper HTTP status code usage
- Verify anti-forgery token usage on state-changing operations
- Review middleware ordering (authentication before authorization)

## Tester Criteria
- Integration tests with test server (WebApplicationFactory or similar)
- Form submission validation testing (valid, invalid, boundary inputs)
- Authentication/authorization scenario tests (anonymous, authenticated, wrong role)
- API endpoint contract tests (request/response shapes)
- Test error responses and edge cases (404, 500, validation errors)

## UI/UX Designer Criteria
- HTML forms usability: proper labels, fieldsets, input types
- Server control rendering: verify generated HTML is semantic
- CSS consistency across pages and layouts
- Responsive layout: test at common breakpoints
- Form validation feedback: clear error messages near the relevant field
- Loading indicators for async operations

## Security Auditor Criteria
- CSRF protection: anti-forgery tokens on all POST/PUT/DELETE forms
- XSS prevention: output encoding, Content Security Policy headers
- Input validation: server-side validation (never trust client-only validation)
- ViewState tampering protection (WebForms): EnableViewStateMac
- Windows Authentication configuration: verify authorized users/groups
- SQL injection: parameterized queries, no string concatenation in queries
- Sensitive data exposure: check response headers, error messages, logs
- CORS configuration: verify allowed origins are intentional

## Project Manager Criteria
- IIS deployment configuration is updated if needed
- SSRS report versioning matches application version
- Web.config transforms are correct for each environment
- Verify database migration scripts are included
