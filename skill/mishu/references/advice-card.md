# Advice card spec

**Every piece of advice** Mishu gives is an advice card, rendered by mishu.py so it always looks the same. Write the card's content in the vault language.

## 1. JSON shape

```json
{
  "category": "nudge | adjust | coach | insight",
  "goal": "G03 or global",
  "title": "one-line title (≤ ~8 words)",
  "level": "L0 | L1 | L2 | L3 | L4",
  "facts": "data quoted from the vault: numbers, reason codes, deferral counts",
  "judgment": "the diagnosis: where the problem is",
  "options": [
    {"label": "A", "text": "the option", "cost": "what it costs"},
    {"label": "B", "text": "the option", "cost": "what it costs"}
  ],
  "recommend": "A",
  "recommend_reason": "one-line reason",
  "ask": "what the user needs to do: reply A/B, confirm, or nothing"
}
```

Where cards are used:
- In chat: `advice --file -`
- In the daily plan: `plan --advice-file -` (≤2)
- In the check-in: `checkin --advice-file -` (≤1)

Each rendered card gets an ID (e.g. `A0914-1`). Cite it with `--advice A0914-1` when the user's choice leads to `set` or `decide`.

## 2. Hard rules (enforced by mishu.py)
- `facts`, `judgment` and `ask` are required.
- A card can have at most 3 options, and every option needs a cost.
- If there are options, `recommend` is required and must match one of them.
- L2, L3 and L4 need a decision from the user, so they must include options.

## 3. Content rules (yours to follow)
1. **No data, no advice.** Every number in `facts` must come from `status`, `stats`, `candidates` or the vault files.
2. **Name real costs.** Never write "none". If an option truly costs nothing, it isn't a choice.
3. **Be specific in the diagnosis.** ✗ "needs more effort" ✓ "the bottleneck is the missing target list, not time".
4. **Recommend honestly.** Recommend what you actually think is best, not what feels easiest.
5. **No lecturing, no labels.** Describe behavior and data, never the person.

## 4. Categories and levels

| Category | Use for |
|---|---|
| `nudge` | due dates, follow-ups on waiting items, skipped habits |
| `adjust` | changing the plan, budget, quota or deadline |
| `coach` | diagnosis and routes when stuck |
| `insight` | patterns in the data (e.g. "weekends finish twice as much") |

Chinese aliases (提醒/调整/教练/洞察) are also accepted.

| Level | Triggered by | Options usually cover |
|---|---|---|
| L0 | routine info, insights | options optional |
| L1 | a main item skipped today; waiting over 3 days | options optional; `ask` names a concrete action |
| L2 | an action deferred ≥3 times; a goal idle past `stale_days` | split / minimum version / reschedule |
| L3 | a goal red for 2 consecutive weeks | extend / cut scope / pause / drop |
| L4 | ≥3 goals red at once; over capacity; a new goal failing the capacity gate | load review, trade-offs per goal |

## 5. Volume and frequency
- **Limits:** ≤2 cards in a daily plan, ≤1 in a check-in, unlimited when the user asks for help.
- **Too many candidates:** keep the highest levels.
- **One card per issue per day.** If the user ignores a card, raise the issue again only after the state changes (another deferral, or it escalates a level).

## 6. Example

```json
{"category": "coach", "goal": "G01", "title": "Stuck on the iCloud sync research", "level": "L2",
 "facts": "G01.T04 deferred 3 times; 2 of them with reason U (unclear where to start)",
 "judgment": "The task is too vague: “compare 3 options” has no concrete first step or output format",
 "options": [
   {"label": "A", "text": "Split it: ① 25m list 3 candidates with doc links ② 30m fill a cost/complexity/offline table", "cost": "One extra breakdown step; no extra work today"},
   {"label": "B", "text": "Skip sync in v1 and move it after M3", "cost": "No multi-device sync at launch; may hurt early retention"}],
 "recommend": "A", "recommend_reason": "sync is core; only the task definition is unclear", "ask": "Reply A or B"}
```
