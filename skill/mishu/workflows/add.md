# Workflow: goal intake (7 steps)

Principle: **you draft, the user corrects.** Intake usually takes 2–3 exchanges.
For the JSON draft format, see `references/vocabulary.md` §3. Write titles and notes in the vault language.

---

## ① Capture
- If the goal comes from the inbox, note its item number N; you'll need `--inbox N` in step ⑦.
- If the user mentions something in passing while doing something else, `inbox add` it **without derailing**, and ask later whether to set it up now.

## ② Classify
Pick the type with this decision tree. Tell the user the result and the reason in one sentence; they can correct it.

```
Done in a few steps, ≤3h total?                          → errand   📦
Is the goal to master knowledge or a skill?              → learning 📚
Outcome depends on others' choices, needs many tries?    → pipeline 🎯
Repeated behavior changing a metric or state?            → habit    🔁
None of the above                                        → project  🏗
```

**Mixed goals:** pick the main type by asking "what decides success in the end?". The other parts become ordinary actions. If a part is big on its own, split it into a separate goal.

## ③ Clarify (one round, with drafted answers)
Draft the answers first, then say: "Here's my first pass. Correct anything that's off."

**Four universal fields**

| Field | What to settle |
|---|---|
| `done_when` | What counts as done? It must be **observable** (✗ "get good at Rust"; ✓ "all 20 chapters' exercises + a small CLI tool"). |
| `why` | One sentence. |
| `deadline` | Append `!` for a hard deadline. Habits may skip it. |
| `budget` + `priority` | Hours per week. Set priority **by comparing** with the current active goals: run `status` first, then ask "Is this more important than G01?" |

**Type-specific (≤3 each)**

| Type | Settle |
|---|---|
| project | Phases and their due dates; current state; external dependencies. **For code projects: the local repo path.** |
| habit | Outcome metric (current → target); sessions per week; the minimum version for bad days. |
| errand | Steps; information or budget needed. |
| pipeline | Funnel stages; weekly action quota; how many final results are needed. |
| learning | Materials and units (total, already done); how mastery is proven (it must be an output). |

## ④ Break down
**Code projects:** if the user gave a repo path, first dispatch a read-only sub-agent so you don't list finished work as to-dos:

> Agent(subagent_type="Explore"): "Read-only look at the repo {repo}: the last 20 commits, the directory layout, and README/TODO. Summarize what's already built and what's clearly unfinished. Don't modify files, install dependencies or run builds. ≤15 lines."

**Phases:** 3–5, each with a title and due date. Only the first one is `active`.

**Actions:** **only for the current phase and the next two weeks.** Each action must be:
- verb-first, with an observable outcome;
- estimated at 15m–2h (anything over 2h must be split);
- for recurring habits: `every` for fixed weekdays, or `frequency.task` for "N times per week";
- given a `min` (minimum version) where useful.

There must be at least one next action the user can start right away.

## ⑤ Measure and evidence
Use the type's default measure. Confirm it in one sentence, e.g. "Progress tracks weight from 78 to 70 kg; pace checks whether you hit 4 sessions a week."

**Agree the evidence method explicitly:**

| Type | Default verify | Say something like |
|---|---|---|
| project (code) | `{"method": "repo", "repo": "path", "when": "every"}` | "When you say something's done, I'll have a sub-agent glance at the commits." |
| project (non-code) | verbal; link/file at milestones | — |
| habit | `{"method": "photo", "when": "metric", "fallback": "verbal"}` | "When you update your weight, could you snap the scale? If not, just tell me the number. I won't store the photo." |
| pipeline | link, for value updates | application screenshots or tracker links |
| learning | link, at milestones | exercise code or notes |
| errand | verbal | — |

If the user objects, switch to what they're comfortable with (even all-verbal) without arguing.

## ⑥ Capacity gate + ⑦ Confirm and activate
1. **Preview the draft:**
```bash
python3 ~/.claude/skills/mishu/scripts/mishu.py add-goal --dry-run --file - <<'JSON'
{ …draft… }
JSON
```
2. **Handle the exit code:**
   - **2 (not ready):** ask about or fix the listed gaps.
   - **3 (capacity gate):** show an L4 `adjust` advice card with `advice`, with three options and their costs:
     - A. Lower another goal's budget
     - B. Pause another goal
     - C. Save the new goal as `someday`

     After the user picks:
     - **A or B:** run `set … --confirmed --reason "make room for the new goal" --advice <AID>` on the existing goal.
     - **C:** set `"status": "someday"` in the draft.

     Then preview again.
   - **Success:** paste the goal card and ask "Create it?"
3. **After an explicit yes,** run it without `--dry-run`. Add `--inbox N` if it came from the inbox.
   - Inbox numbers shift after every processed item. **Run `inbox list` right before each `--inbox N`** (mishu.py also prints the renumbered list after processing).
4. **Tell the user** the goal ID and the **first next action**.
