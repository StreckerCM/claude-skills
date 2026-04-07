---
name: nodejs-api
display_name: "Node.js / Express API"
build_command: "npm run build"
test_command: "npm test"
rotation_size: 4
personas: [implementer, reviewer, tester, security-auditor]
---

# Node.js / Express API Review Profile

## Implementer Criteria
- Proper async/await error handling (try/catch in route handlers, or express-async-errors)
- Middleware ordering: body parsers before routes, error handler last
- Express 5 patterns if applicable (returned promises auto-caught)
- Docker health check endpoint exists and works
- Environment variable validation at startup (fail fast on missing config)
- Proper HTTP status codes and consistent error response format
- Use of TypeScript types or JSDoc for API contracts

## Reviewer Criteria
- Dependency audit: check for known vulnerabilities (`npm audit`)
- Error propagation: async errors reach the error handler, not silently swallowed
- Azure SDK credential handling: use DefaultAzureCredential, not hardcoded keys
- Rate limit configuration: verify limits are appropriate for the endpoint
- Logging: structured logs with request IDs for traceability
- Memory leaks: check for event listener accumulation, unclosed streams
- Package.json: no unnecessary dependencies, lock file is committed

## Tester Criteria
- Supertest integration tests for all endpoints
- Mock external services (email, Azure APIs) in tests
- Test error response formats match API contract
- Test rate limiting behavior
- Test authentication/authorization scenarios
- Test input validation edge cases (empty body, wrong content-type, oversized payload)

## Security Auditor Criteria
- Input validation with a schema library (Joi, Zod, or express-validator)
- CORS configuration: verify allowed origins whitelist, no wildcard in production
- Helmet.js headers: verify security headers are set
- Credential storage: no secrets in code, use environment variables
- Rate limiting: verify all public endpoints are rate-limited
- Request size limits: body parser has reasonable maxSize
- Dependency security: no packages with known critical vulnerabilities
- Docker: non-root user in Dockerfile, no secrets in image layers
