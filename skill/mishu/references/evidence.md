# Evidence & verification protocol

## 1. Why evidence
Evidence keeps the **progress data trustworthy**. Pace lights, forecasts and advice are only as good as that data.
It is not distrust: the user can always choose a verbal report, and Mishu must accept it.

## 2. Evidence codes

| Code | Name | Strength | Used for |
|---|---|---|---|
| 🔍 | code check | highest | a sub-agent found the matching commits or code in the repo |
| 📷 | photo | high | scale readings, fitness app screenshots, physical items |
| 🔗 | link / file | high | documents, application records, notes, exercise code paths |
| 💬 | verbal | baseline | the user's own report |
| ⚙️ | system | — | written by mishu.py itself (goal created, field changed); never pass it manually |

## 3. A goal's verify settings

```yaml
verify:
  method: repo | photo | link | verbal   # preferred evidence
  repo: ~/code/budget-app                # required when method=repo
  when: every | metric | milestone       # when the preferred evidence is required
  fallback: verbal                       # what to accept otherwise
```

- `every`: every ✓ or ◐ needs the preferred evidence.
- `metric`: only value updates (metric / funnel / units).
- `milestone`: only phase completion (`phase done`).

Anything outside `when` accepts 💬 without extra checks.

## 4. Code projects: sub-agent verification

### When to dispatch
The goal has `verify.method=repo`, and any of these is true:
- `when=every` and the user reported ✓ or ◐;
- it's a phase completion;
- the user asks you to check progress.

### How to dispatch
- Use the Agent tool with `subagent_type: "Explore"` (read-only).
- If several repos are involved in the same turn, **dispatch them in parallel in a single message**.
- Prompt template:

```
You are a progress verifier. Inspect a code repository READ-ONLY and judge whether the reported items are really done.

Repository: {absolute repo path}
Goal: {GID} {goal title}
Items to verify:
- {GID}.{TID} {action title} — user reports: {✓ done / ◐ partial}, in their words: {quote}
Last verified: {date of the goal's latest 🔍 log, else the goal's start date}

Rules:
1. Read-only. You may use git log / git show / git diff --stat, read files, and search code.
   Do NOT modify files, run git checkout/reset/commit/push, install dependencies, or run builds/tests.
2. Look at commits since the last verified date (git log --since) and locate commits/code related to each item.
3. For each item decide: done / partial / no evidence. Be conservative: if you can't find it, it's "no evidence". Don't speculate.
4. Output exactly this table and nothing else:

| Item | Verdict | Evidence | Notes |
|---|---|---|---|
| G01.T03 | partial | commit e19f55 (src/Ledger/ListView.swift:12-80) | list view wired; no edit view found |
```

### Using the verdict

| Check result | User said | Log as |
|---|---|---|
| done | ✓ | ✓ 🔍, commit hash in the note |
| partial | ◐ | ◐ 🔍, note what's done and what isn't |
| partial or no evidence | ✓ | **show the difference and let the user decide** (see below) |
| repo path missing or unreadable | — | tell the user, log 💬 this time, and suggest fixing `verify.repo` (a structural change) |

When the check and the user disagree:
- If the user insists it's done, log ✓ 💬 with the note "user reports done; check: {verdict}".
- If the user accepts the check, log what the check found, with 🔍.

If the user says "don't bother" or "skip the check", log 💬 with the note "user chose to skip the check".

## 5. Body metrics and physical items: photos

### Asking
- Only ask when `when` requires it, **once per item**, and always give an out.
- Example: "If it's handy, could you snap the scale? Otherwise just tell me the number. I only read it, I don't keep the photo."

### Reading
- Read out the key value and **confirm it**: "I see 76.1 kg, right?"
- If it's unreadable or ambiguous (lb vs kg), ask for the number and log 💬.
- If the photo contradicts the user's words, point it out politely and let them confirm.

### Privacy
- **Photos are not stored by default.** The note says "photo viewed, not stored".
- Only run `evidence add GID <path>` when the user explicitly wants it stored and gives a local file path.
- Never comment on the user's body, appearance or shape.

### If the user declines
- Log 💬. Don't ask again, don't comment, don't bring it up later.
- Weekly stats report the evidence mix as plain data, never as a moral judgment.

## 6. Other goal types

| Type | Practice |
|---|---|
| pipeline (job hunt, …) | Application or interview screenshots and email subjects count as 🔗; otherwise 💬 |
| learning | Exercise code paths, note links and quiz scores count as 🔗. At phase completion, consider asking the user to **explain what they learned** (log 💬 with the key points) |
| errand | verbal is fine |
