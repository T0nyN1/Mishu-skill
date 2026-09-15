# Workflow: coach mode (stuck)

Use this when the user says things like "I don't want to", "no idea what to do", "can't make progress", "should I give up", or "too much on my plate".
Principle: **diagnose first, then offer routes.** Give ≤3 data-backed routes, each with its cost, plus a recommendation, and let the user choose. No empty pep talks.

## 0. The person before the task
If the user is clearly distressed (overwhelmed, sleepless, harsh on themselves), respond to the feeling first. **Pause task pressure.** If the signs are serious, gently suggest professional help. **No advice cards here.**

## 1. Gather facts
```bash
python3 ~/.claude/skills/mishu/scripts/mishu.py status G01
python3 ~/.claude/skills/mishu/scripts/mishu.py stats --gid G01 --days 14
```
For a general "too much going on", use `status` and `stats --days 14` instead.

## 2. Diagnose
Use the data first. Ask at most 2 questions if needed.

| Category | Signals in the data | What you might ask |
|---|---|---|
| **Unclear** (doesn't know the next step) | Many U codes; vague action titles; no next action | "If you only had 25 minutes right now, where would you start?" |
| **Avoidance** | Many A codes; repeated deferrals despite having time | "When you think about it, which part feels worst?" |
| **Can't move** (missing skill or resources) | Many B or O codes; ◐ keeps repeating | "Is it knowledge, a tool, or someone else you're missing?" |
| **Doubting the direction** | Long stall; user questions the goal | "If you were starting from scratch today, would you still set this goal?" |
| **Overload** | Many T/E codes; several 🔴; budgets over capacity | "Which of these could you set down for three months without real harm?" |

## 3. Routes by category
- **Unclear → break it down.**
  - Split into a first step of ≤25 minutes that can start right now, and name the output format.
  - Use `task add` for the new steps. Then either cancel the old action (`task set cancel --confirmed`) or keep it with `task edit --reset-defer`.
- **Avoidance → shrink it.**
  - Two minutes, or the minimum version (`task edit --min`), anchored to a fixed time.
  - Mention the `why` once, without preaching.
- **Can't move → add resources.**
  - Offer a learning path, someone to ask, or an alternative.
  - Mark waiting-on-others as `blocked` and schedule a follow-up.
- **Doubting the direction → revisit `done_when`.**
  - Routes: shrink the scope, pause until a date, or drop it.
  - **Dropping is a legitimate choice.** Record it as a decision.
- **Overload → trade off.**
  - List all active goals with their budgets and pace.
  - Ask the user to pause or cut 1–2 of them, or to lower budgets.

## 4. Issue the advice card
```bash
python3 ~/.claude/skills/mishu/scripts/mishu.py advice --file - <<'JSON'
{"category": "coach", "goal": "G01", "title": "…", "level": "L2",
 "facts": "numbers quoted from status and stats", "judgment": "the diagnosis",
 "options": [{"label": "A", "text": "…", "cost": "…"}, {"label": "B", "text": "…", "cost": "…"}],
 "recommend": "A", "recommend_reason": "…", "ask": "Reply A or B"}
JSON
```

Pick the level:

| Level | When | Options usually cover |
|---|---|---|
| L2 | A single stuck action | split / minimum version / reschedule |
| L3 | A goal red for 2 weeks | extend / cut scope / pause / drop |
| L4 | Overall overload | a trade-off across goals |

## 5. Carry out the user's choice
- **Progress-level changes** (breakdown, re-estimate, minimum version): apply them directly, and cite the advice card ID in `--reason`.
- **Structural changes** (extend, pause, drop, budget): the user's pick counts as confirmation. Run `set … --confirmed --reason … --advice <AID>`.
- **No structural change?** Still record the choice with `decide GID "Chose A: …" --advice <AID>`.
- **Finish** by telling the user the **concrete next step**, in one sentence.
