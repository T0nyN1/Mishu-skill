# Workflow: daily plan (today)

Principle: rules produce the candidates, you make the judgment calls, and **nothing is written until the user confirms**.

## Steps

### 1. Check state
- **Empty vault:** go to `workflows/setup.md` step 4 instead. There's nothing to plan yet.
- **Today's plan already exists:** `cat` the daily file, show it, and ask whether to re-plan. If yes, add `--force` in step 6.
- **Check-in already done today:** don't re-plan; say why.
- **Yesterday has a plan but no check-in** (`daily/<yesterday>.md` has no "🌙" section): briefly ask how those items went, and backfill with `log <ID> … --date <yesterday>`. The evidence rules still apply.

### 2. Ask about today (one question)
> "How much time do you have today, and how's your energy from 1 to 5?"

Offer defaults: `daily_default` on weekdays, `weekend_default` on weekends, and energy 3. "Same as usual" means the defaults.

### 3. Get candidates
```bash
python3 ~/.claude/skills/mishu/scripts/mishu.py candidates --hours 4 --energy 3
```

### 4. Make the calls
Start from the ✔ suggestions, then adjust:
- **Prefer yesterday's "Tomorrow" items** from yesterday's check-in.
- **Red goals:** include at least one item from each 🔴 goal, unless the user says not today.
- **Big blocks:** at most one block over 60m per goal per day, except when sprinting to a deadline.
- **Low energy (≤2):** swap to low-effort items or minimum versions. mishu.py times minimum versions automatically.
- **Balance areas:** don't push the same area several days running.

mishu.py enforces the hard limits: ≤3 main items, and total ≤ available × 0.7.

### 5. Prepare advice cards (≤2, highest level first)
Triggers:
- "Needs breakdown" in the candidates → an L2 `coach` card with a breakdown.
- A 🔴 goal → an L2 `adjust` card.
- Waiting on someone for more than 3 days → an L1 `nudge`.
- A pattern that's clearly in the data even though the user didn't mention it.

Rules are in `references/advice-card.md`. **If nothing is worth saying, issue no card.**

### 6. Draft → confirm → write
1. **Show a short draft:** one line per item with ID, title, time, and a one-line reason. Ask "Does this work?"
2. **After the user confirms or adjusts, write it:**
```bash
python3 ~/.claude/skills/mishu/scripts/mishu.py plan --hours 4 --energy 3 \
  --main G03.T02,G01.T04 --habit G02.T01 --errand G05.T02 --advice-file - <<'JSON'
[ …advice cards… ]
JSON
```
Leave out `--advice-file` when there are no cards.

### 7. Show it
- Paste the plan that mishu.py rendered.
- End with one sentence: the single most important item today, and when the check-in is.
