---
id: G03
title: Land a new-grad offer
type: pipeline
area: Career
priority: P0
status: active
created: 2026-09-01
start: 2026-09-01
deadline: 2026-11-15!
why: Start as a mobile engineer after graduation
done_when: Signed at least one mobile engineering offer
budget: 5h/w
review: weekly
verify:
  method: link
  when: metric
  fallback: verbal
measure:
  progress: phases
  pace: frequency
  funnel:
    - {stage: Applied, count: 3}
    - {stage: Screened, count: 1}
    - {stage: Interview, count: 0}
    - {stage: Offer, count: 0, target: 1}
  frequency: {stage: Applied, per_week: 10, unit: apps}
phases:
  - {id: M1, title: Polish the résumé, weight: 1, due: 2026-09-07, status: done}
  - {id: M2, title: Apply in volume, weight: 2, due: 2026-10-15, status: active}
  - {id: M3, title: Interviews, weight: 2, due: 2026-11-10, status: todo}
  - {id: M4, title: Choose an offer, weight: 1, due: 2026-11-15, status: todo}
---

## Actions
- [x] T01 Rewrite project bullets against target JDs · 90m · M1
- [x] T02 Build a target company list (20) · 45m · M2 · defer:2
- [ ] T03 Apply to 5 target companies · 45m · M2
- [ ] T04 Prepare 5 STAR behavioral stories · 60m · M3

## Log
- 2026-09-01 | created | = |  | ⚙️ | goal created (active)
- 2026-09-05 | T01 | ✓ | 1h30m | 🔗 | résumé v3 uploaded
- 2026-09-05 | M1 | ✓ |  | 🔗 | phase completed
- 2026-09-08 | T02 | ✗ |  |  | [U] no idea which companies to target
- 2026-09-10 | T02 | ✗ |  |  | [U]
- 2026-09-10 | funnel:Applied | = | +3 | 🔗 | application screenshots
- 2026-09-13 | funnel:Screened | = | +1 | 🔗 | recruiter email
- 2026-09-14 | T02 | ✓ | 50m | 🔗 | 22 companies saved in Notion

## Decisions
