---
name: scientific-computing
display_name: "Scientific Computing (Overlay)"
type: overlay
applies_to: [dotnet-desktop, dotnet-library, python-tools, nodejs-api]
---

# Scientific Computing Review Overlay

This is an **additive overlay**, not a standalone profile. These criteria are appended to the base stack profile's criteria for each persona.

## Implementer Criteria (additional)
- Numerical precision: use double (not float) for intermediate calculations
- Coordinate system transformations: document which convention is used (NED vs ENU, left-hand vs right-hand)
- Unit consistency: verify all calculations use consistent units (radians vs degrees, meters vs feet)
- Algorithm correctness: reference the paper/standard the implementation is based on
- Magic numbers: named constants with units in the name (e.g., `EARTH_RADIUS_METERS`)
- Avoid loss of significance in subtraction of nearly-equal values
- Use Kahan summation or compensated algorithms for long running sums

## Reviewer Criteria (additional)
- Verify mathematical formulas against cited papers or standards (ISCWSA, SPE, IGRF, WMM)
- Check for floating-point comparison pitfalls: use `Math.Abs(a - b) < epsilon`, never `==`
- Verify coordinate system conventions are consistent throughout the codebase
- Check unit conversions: degrees to radians, feet to meters, etc.
- Look for potential division by zero in geometric calculations (sin(0), tan(90), radius at poles)
- Verify matrix operations: correct dimensions, proper transpose/inverse usage
- Check for numerical stability in edge cases (near poles, near dateline, near equator)

## Tester Criteria (additional)
- Known-answer tests from published papers (ISCWSA test cases, SPE reference datasets)
- Boundary value testing at geographic extremes: poles (lat +/-90), dateline (lon +/-180), equator (lat 0)
- Regression tests with reference datasets (golden files)
- Precision tests: verify results match reference to expected decimal places
- Round-trip tests: convert forward then inverse, verify original values recovered
- Test with real-world data samples, not just synthetic inputs
- Test coefficient file loading and model date validity ranges

## Security Auditor Criteria (additional)
- Input range validation: latitude -90 to +90, longitude -180 to +180
- Altitude/depth bounds checking: reject clearly invalid values
- Division by zero protection in geometric calculations
- Coefficient file integrity: validate file format before parsing
- Buffer overflow prevention in native interop (P/Invoke, ctypes)
- Verify model validity date ranges are enforced (e.g., WMM epoch checks)
