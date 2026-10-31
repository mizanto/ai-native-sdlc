# Review policy

Used by `/sdlc-review` (and any human reviewer). Findings never approve a change;
a human code owner does.

## Passes
1. **Bugs** — logic errors, edge cases, error handling, concurrency, data loss.
2. **Security** — authn/authz, input validation, injection, secrets, PII handling, audit events.
3. **Compliance with spec/plan** — every requirement (R#) implemented as specified; no unplanned scope; deviations from plan.md explained.
4. **Tests** — the Proof in plan.md exists and actually exercises the behaviour.

## Severity
- **Important** — must be fixed before merge: wrong behaviour, security issue, missing requirement, broken test.
- **Nit** — style, naming, small readability improvements.

Nit cap: 5

## Exclusions
- Generated code, lockfiles, vendored dependencies.
- Anything CI already enforces (formatting, lint rules).
