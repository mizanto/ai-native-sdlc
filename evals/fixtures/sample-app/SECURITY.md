# Security policy

- Every endpoint that returns claim or policy data must verify the caller (`X-User`) owns it.
- Responses to the mobile app must not include monetary amounts unless the screen needs them (data minimisation).
- Never put customer identifiers or PII in URLs beyond opaque IDs.
