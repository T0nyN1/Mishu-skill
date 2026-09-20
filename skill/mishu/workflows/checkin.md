# Workflow: evening check-in (checkin)

Principle: **go item by item, collect evidence and reasons, then write everything back in one go.** Aim for 2 exchanges.

## Steps

### 1. Read today's plan
```bash
cat <vault>/daily/$(date +%F).md
```
- **No plan today:** say so, and record what they did item by item with `workflows/log.md`.
- **Check-in already done:** say so. Anything extra gets appended with `log`.

### 2. Ask everything at once (with a reply format)
List the items with numbers and suggest a compact reply, e.g.:

> Here's today's list. Reply with number + result (✓ done / ◐ partly / ✗ didn't / ➜ another day). For anything not done, add a word on why:
> 1. G03.T02 Build a target company list
> 2. G01.T04 Compare iCloud sync options
> 3. G02.T01 Strength session
>
> Also: anything done that wasn't on the list? Any numbers to update today (weight, applications…)?

**If the user pastes ticks from the dashboard** — a message like "Mishu, here's today (2026-09-15):" followed by lines such as `✓ G02.T03 Implement local expense CRUD` / `✗ G04.T03 Apply to 5 target companies` — read them as results (`✓` done, `✗` not done) and only ask for what's missing: time spent, reasons for the misses, and evidence where `verify.when` requires it. The dashboard's checkboxes never write to the vault; this check-in does.

### 3. Fill in evidence (see `references/evidence.md`)
- **`repo` goals with ✓/◐:** before writing, dispatch read-only sub-agents. If several repos are involved, send them in one message, in parallel.
  - The check agrees → log 🔍 and put the commit hash in the note.
  - The check disagrees → show the difference and let the user decide.
- **`photo` goals:** ask for a photo only when `when` requires it (e.g. a value update).
- **Everything else:** follow `verify.method`. With no evidence, log 💬.

### 4. Fill in reason codes
Every ◐ / ✗ / ➜ needs a reason code. Map the user's words to a code, or offer the options:

| Code | Meaning |
|---|---|
| T | no time |
| E | low energy |
| U | unclear how |
| A | avoiding it |
| B | blocked |
| O | underestimated |
| P | plan changed / no longer needed |

If the user doesn't want to say, pick the closest code, note "user didn't say", and don't press.

### 5. Tomorrow and the advice card
- **`--tomorrow`:** pick 1–3 items from unfinished main items and the goals' next actions.
- **At most one advice card**, by priority:
  1. An action deferred 3 times → L2 `coach`.
  2. A main item skipped two days running → L1 `nudge`.
  3. A clear pattern in the data → `insight`.

### 6. Write back
```bash
python3 ~/.claude/skills/mishu/scripts/mishu.py checkin \
  --item "G03.T02|done|50m||link|22 companies saved in Notion" \
  --item "G01.T04|skip||U||not sure how to compare" \
  --item "G02.T01|done|35m||verbal|" \
  --item "G03.T03|done|45m||link|application screenshots|5" \
  --tomorrow "G01.T03,G03.T03" --summary "the user's one-line self-assessment (optional)" \
  --advice-file - <<'JSON'
{ …advice card… }
JSON
```
- **`--item` fields:** `ID|result|time|reason|evidence|note|qty`.
  - `qty` is only for quota tasks with a unit (e.g. 5 applications); omit it otherwise.
  - Unplanned work can go in as an `--item` too; it's tagged "unplanned".
- **Every planned item must be reviewed.** Only use `--allow-missing` if the user really won't say.
- **Value updates** (`metric` / `funnel` / `units`) run after the check-in.

### 7. Act on the hints
- **"🎉 All actions done":** ask whether the definition of done is met. After a yes, run `set GID status done --confirmed --reason …`.
- **"All actions in phase … are done":** verify as `verify.when` requires, then run `phase done`.
- **"No open next action":** break down new actions with the user (`task add`).

### 8. Close
- Paste the check-in output.
- Say one sentence in the profile's tone: acknowledge what got done, and name the single most important leftover. **No lecturing.**
