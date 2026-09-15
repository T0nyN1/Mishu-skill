---
id: G01
title: Ship budgeting app v1
type: project
area: Career
priority: P1
status: active
created: 2026-09-01
start: 2026-09-01
deadline: 2026-11-30!
why: Portfolio piece + prove I can ship solo
done_when: Live on the App Store with 10 real users
budget: 8h/w
review: weekly
verify:
  method: repo
  repo: ~/code/budget-app
  when: every
  fallback: verbal
measure:
  progress: phases
  pace: timeline
phases:
  - {id: M1, title: Requirements & prototype, weight: 1, due: 2026-09-10, status: done}
  - {id: M2, title: Core expense tracking, weight: 2, due: 2026-10-20, status: active}
  - {id: M3, title: Polish & launch, weight: 1, due: 2026-11-30, status: todo}
---

## Actions
- [x] T01 Wireframe the 5 core screens · 90m · M1
- [x] T02 Pick the stack and scaffold the project · 60m · M1
- [/] T03 Implement local expense CRUD · 120m · M2
- [ ] T04 Compare 3 iCloud sync options in a table · 45m · M2 · defer:3
- [ ] T05 Design the category & tag model · 60m · M2
- [!] T06 Ask a designer friend for the app icon · 15m · M2 · wait:Sam · since:2026-09-11

## Log
- 2026-09-01 | created | = |  | ⚙️ | goal created (active)
- 2026-09-02 | T01 | ✓ | 1h30m | 🔍 | commit 3f2a1c wireframes in docs/
- 2026-09-04 | T02 | ✓ | 1h15m | 🔍 | commit 8b7d02 SwiftUI+SwiftData scaffold
- 2026-09-04 | M1 | ✓ |  | 🔍 | wireframes and scaffold verified
- 2026-09-09 | T03 | ◐ | 1h | 🔍 | [O] commit c41e9a model layer done, UI not wired
- 2026-09-10 | T04 | ➜ |  |  | [T]
- 2026-09-12 | T04 | ✗ |  |  | [U] not sure where to start comparing
- 2026-09-14 | T04 | ✗ |  |  | [U] still unsure how to compare
- 2026-09-14 | T03 | ◐ | 1h | 🔍 | [O] sub-agent verified commit e19f55: list view wired, edit view missing

## Decisions
- 2026-09-13 | D01 | Drop multi-currency support | Reason: keep v1 focused | Revisit: 2026-12-01
