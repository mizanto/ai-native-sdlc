---
id: CLM-7-claim-status
artifact: intent
lane: full
status: accepted
upstream: none
created: 2026-10-27
accepted_by: Sergey Bendak
accepted_at: 2026-10-28T10:00:00
---

# Intent: Customers can check their claim status themselves

## Problem
"About 40% of the calls we get are people asking where their claim is" (Maria, support lead). Policy holders have no way to see progress on a claim, so they phone support, which costs us and frustrates them.

## Proposed outcome
A policy holder can see the current status of their own claim, and when it last changed, from the mobile app without calling support.

## Affected users and systems
- Policy holders (mobile app users)
- Support team (fewer status calls)
- claims-service API (`claims/api.py`), consumed by the mobile app team

## Constraints
- Must never reveal another customer's claim (see SECURITY.md).
- Mobile app team needs it for the November release.

## Success criteria
- Status-related support calls drop by at least 30% within two months of launch.
- Mobile app shows status for 100% of a user's claims.

## Open questions
- Should we also show a human-readable explanation of each status? (Product to decide; out of scope for now.)
