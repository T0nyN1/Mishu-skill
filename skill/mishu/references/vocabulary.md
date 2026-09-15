# Vocabulary & data formats

## 1. Shared vocabulary

### Goal types
| Icon | type | Default progress | Default pace |
|---|---|---|---|
| 🏗 | project | phases | timeline |
| 🔁 | habit | metric | frequency |
| 📦 | errand | checklist | deadline |
| 🎯 | pipeline | phases | frequency |
| 📚 | learning | units | timeline |

### Statuses
- **Goal:** `inbox` → `draft` → `active` ⇄ `paused` → `done` / `dropped`, plus `someday` (uses no capacity).
- **Action:** `[ ]` todo · `[/]` doing · `[x]` done · `[!]` blocked · `[-]` cancelled.
- **Phase:** `todo` · `active` · `done`.

### Pace lights
| Light | Meaning |
|---|---|
| 🟢 | pace ratio ≥ 0.9 |
| 🟡 | ratio 0.7–0.9, or idle longer than `stale_days` |
| 🔴 | ratio < 0.7, overdue, or idle longer than 2 × `stale_days` |
| ⚪ | not started |
| ⏸ | paused |
| ✅ | done |
| 💭 | someday |
| 📝 | draft |

### Result codes
| Code | Alias | Meaning |
|---|---|---|
| ✓ | done | done |
| ◐ | partial | partly done |
| ✗ | skip | not done |
| ➜ | moved | rescheduled |
| ✂ | cancel | cancelled |
| = | — | value update (system) |

### Evidence codes
| Code | Alias | Meaning |
|---|---|---|
| 🔍 | code | code check |
| 📷 | photo | photo |
| 🔗 | link | link or file |
| 💬 | verbal | verbal |
| ⚙️ | — | system |

### Reason codes
| Code | Meaning |
|---|---|
| T | no time |
| E | low energy |
| U | unclear |
| A | avoiding it |
| B | blocked |
| O | underestimated |
| P | plan changed |

### Priority and IDs
- **Priority:** `P0` must · `P1` important · `P2` want · `P3` nice to have.
- **IDs:** goal `G01` · phase `G01.M2` · action `G01.T05` · decision `G01.D03` · advice card `A0914-1`.

## 2. File formats (maintained by mishu.py; for reading only)

Section headers follow the vault language (`## Actions` / `## 行动`, …). mishu.py reads either language.

**Action line**
```
- [status] T05 Verb-first title · 90m · M2 · due:2026-09-20 · every:mon,wed · min:10m · defer:2 · wait:Sam · since:2026-09-10
```

**Log line** (6 columns)
```
- date | ref | result | time or value | evidence | note
```
- A note starting with `[U]` carries the reason code.
- `ref` is an action ID, a metric name, `funnel:<stage>`, a phase ID or a decision ID.

**Decision line**
```
- date | D01 | text | Reason: … | Revisit: date | Source: advice ID
```

## 3. Goal JSON draft (input to add-goal)

```json
{
  "title": "Ship budgeting app v1",
  "type": "project",
  "area": "Career",
  "priority": "P1",
  "status": "active",
  "start": "2026-09-15",
  "deadline": "2026-11-30!",
  "budget": "8h/w",
  "why": "Portfolio piece + prove I can ship solo",
  "done_when": "Live on the App Store with 10 real users",
  "verify": {"method": "repo", "repo": "~/code/budget-app", "when": "every", "fallback": "verbal"},
  "phases": [
    {"title": "Requirements & prototype", "due": "2026-09-25"},
    {"title": "Core expense tracking", "weight": 2, "due": "2026-10-20"}
  ],
  "tasks": [
    {"title": "Wireframe the 5 core screens", "est": "90m", "phase": "M1"},
    {"title": "Strength session", "est": "40m", "min": "10m"},
    {"title": "Weigh in and snap the scale", "est": "5m", "every": "sun"}
  ],
  "measure": { }
}
```

Field notes:
- **`status`:** optional; defaults to `active` (`someday` and `draft` also work).
- **`start`:** defaults to today. **`review`:** defaults to `weekly`.
- **`completed`:** never set in a draft. mishu.py stamps it when the goal is set to `done` and removes it if the goal is reopened.
- **`phases`:** numbered M1, M2… in order; the first is `active`.
- **`tasks`:** numbered T01, T02… in order; `phase` refers to `"M1"`-style IDs.
- **`verify`:** optional; the type's default is used. If only `repo` is given, it becomes `method=repo, when=every`.
- **`measure`:** only the type-specific parts; `progress` and `pace` are filled in from the type.

**measure by type**
```json
// habit
{"metric": {"name": "Weight", "unit": "kg", "baseline": 78, "target": 70, "current": 78, "direction": "down"},
 "frequency": {"task": "T01", "per_week": 4}}

// pipeline
{"funnel": [{"stage": "Applied", "count": 0}, {"stage": "Interview", "count": 0}, {"stage": "Offer", "count": 0, "target": 1}],
 "frequency": {"stage": "Applied", "per_week": 10, "unit": "apps"}}

// learning
{"units": {"name": "chapters", "total": 20, "done": 4, "mastered": 4}}

// project / errand
{}
```

Override the defaults when they don't fit, e.g. `"measure": {"progress": "checklist", "pace": "deadline"}`.
