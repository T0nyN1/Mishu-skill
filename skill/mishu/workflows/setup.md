# Workflow: first run & setup

Goal: create an **empty** vault and profile, then onboard the user's **first batch of goals**. Aim for about 3 exchanges before the first goal goes in.

**Starting state:** the vault is always empty on first use.
- Never copy or import anything from the repository's `examples/` folder.
- Never invent sample goals.
- If the user only wants to look around first, point them to the demo instead: `bash examples/build_demo.sh`, run from the cloned repo. The demo is built in the repo's own folder and never touches their vault.

## Steps

### 1. Welcome and choose a location
1. Explain in 1–2 sentences how Mishu works: a plan every morning and a check-in every evening, with all data in a local folder they can read anytime.
2. Detect the user's language from the conversation. That becomes the vault's `lang`: `zh` for Chinese speakers, otherwise `en`.
3. Confirm where the vault should live:
   - Default: `~/MishuVault`.
   - **Never inside the skill directory.** Data and skill stay separate.
   - Avoid shared synced folders.

### 2. Profile interview (one round, with defaults)
Ask everything at once. Offer a default for each item so the user only changes what they disagree with:

| Item | Default |
|---|---|
| What to call them | — |
| Total weekly hours across all goals | 20h |
| Typical weekday availability | 3h |
| Typical weekend availability | 5h |
| Tone: gentle / coach / strict | coach |
| Max goals in progress at once (habits count 0.5) | 5 |
| Evening check-in time | 21:30 |

Optionally, ask about their routine and common distractions (class hours, doom-scrolling times, …).

### 3. Create the empty vault
```bash
python3 ~/.claude/skills/mishu/scripts/mishu.py init --vault ~/MishuVault --lang en --set-default \
  --name "Alex" --capacity 20h --daily 3h --weekend 5h --tone coach --wip 5
```
- **Check-in time:** if it isn't the default, change it with `profile set checkin_time "22:00" --confirmed --reason "setup interview"`.
- **Background:** if the user shared routine details, summarize them as 3–6 bullets, confirm them with the user, then write them:
```bash
python3 ~/.claude/skills/mishu/scripts/mishu.py profile background --confirmed --file - <<'TXT'
- Classes 9:00–18:00 on weekdays; free after 20:00
- Tends to scroll the phone before bed
TXT
```

### 4. Onboard the first batch of goals
1. **Brain dump.** Ask the user to list **everything** on their plate, unorganized: projects, habits, errands, job hunting, studying, small purchases.
2. **Capture each item** with `inbox add "…"`, so nothing is lost.
3. **Pick the first batch.** Show the captured list and agree on the **3–5 most important**, in priority order. Say plainly that the rest stays in the inbox for later.
4. **Run intake.** Take each chosen item through `workflows/add.md` with `--inbox N`.
   - Do the first one fully.
   - Batch questions for the rest to keep things moving.
   - The capacity gate will stop you if the batch doesn't fit their hours. Treat that as a real trade-off for the user, not an error.
5. **Check in** after each goal: "Goal N is in. Next one, or stop here for today?"

### 5. Wrap up
1. Run `board --open` so the dashboard opens in the browser, then summarize in one or two sentences what's active.
2. Explain daily use in at most three lines:
   - In the morning: "what should I do today?" (or `/mishu today`)
   - In the evening: "let's review" (or `/mishu checkin`)
   - Anytime: report progress, or say when you're stuck
3. Offer to plan today right away if there's time left in the day.
