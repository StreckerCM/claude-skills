---
name: salesforce
display_name: "Salesforce (Apex / LWC)"
build_command: "sf project deploy validate"
test_command: "sf apex run test --test-level RunLocalTests"
rotation_size: 6
personas: [implementer, reviewer, tester, ui-ux-designer, security-auditor, project-manager]
---

# Salesforce Review Profile

## Implementer Criteria
- Bulk-safe patterns: no SOQL/DML inside loops
- Governor limit awareness: check query limits, DML limits, CPU time
- Wire adapters (LWC): use @wire for reactive data, imperative calls for actions
- Sharing rules: explicit `with sharing` or `without sharing` on every Apex class
- Trigger patterns: one trigger per object, handler class pattern
- Use Custom Labels for user-facing strings (i18n ready)
- Proper null checks on SObject field access

## Reviewer Criteria
- SOQL in loops: flag any query inside a for/while loop
- DML limits: verify bulk operations use Database.insert with partial success where appropriate
- `with sharing` / `without sharing` correctness: verify matches the use case
- Trigger handler pattern: no logic in trigger files
- API version: classes should target a current API version
- LWC reactivity: verify @track and @api usage follows current best practices
- Check for hardcoded IDs (record types, profiles) - use Custom Metadata or Custom Settings instead

## Tester Criteria
- `@isTest` data isolation: use `@TestSetup` or Test.loadData, not org-dependent data
- Bulk test scenarios: test with 200+ records to verify governor limit compliance
- Mock HTTP callouts with HttpCalloutMock for external integrations
- Test both positive and negative paths (valid data, invalid data, missing permissions)
- Assert specific values, not just "didn't throw"
- Test trigger recursion prevention
- Aim for 85%+ code coverage (Salesforce deployment minimum is 75%)

## UI/UX Designer Criteria
- LWC component design: proper use of Lightning Design System (SLDS) classes
- Lightning Design System compliance: use standard components before custom
- Mobile-first: test in Salesforce mobile app, not just desktop
- Loading states: show spinners during wire/imperative calls
- Error handling UI: display user-friendly error messages from Apex exceptions
- Accessibility: SLDS components are accessible by default, verify custom markup

## Security Auditor Criteria
- CRUD/FLS enforcement: check object/field-level permissions before DML
- Sharing model: verify `with sharing` is used unless explicitly needed otherwise
- XSS in Visualforce: use escape="true", avoid unescaped merge fields in JavaScript
- XSS in LWC: avoid innerHTML, use template expressions
- SOQL injection: use bind variables, not string concatenation in queries
- External callout security: verify endpoint URLs are in Remote Site Settings or Named Credentials
- Sensitive data: no PII in debug logs, no credentials in Custom Settings (use Named Credentials)

## Project Manager Criteria
- Sandbox strategy: verify changes work in sandbox before production
- Deployment dependencies: package.xml includes all metadata
- Metadata coverage: no missing components that would cause deployment failure
- Destructive changes: verify any deleted metadata is in destructiveChanges.xml
- Test coverage report: all classes meet minimum coverage threshold
