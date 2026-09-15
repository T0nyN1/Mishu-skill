# Workflow: report progress anytime (log)

Use this whenever the user says something like "done", "did part of it", "applied to 3", "76 kg today", or uploads a photo.

## 1. Find the item
- Use `status` or `status GID` to find the goal and action ID.
- If it's ambiguous, offer the user 2–3 candidates. **Don't guess.**
- If the work isn't in any goal:
  - **It belongs to an existing goal:** `task add` it first, then log it. This is progress-level, but tell the user.
  - **It's something new:** put it in the inbox.

## 2. Pick the command

| Report | Command |
|---|---|
| An action done or partly done | `log G01.T05 --result done\|partial --time 60m --evidence … [--reason O] [--note]` |
| A habit session | `log G02.T01 --result done --time 40m --evidence verbal` |
| A quota with a quantity (applied to 5) | `log G03.T03 --result done --qty 5 --time 45m --evidence link` **and** `funnel G03 Applied +5 --evidence link` |
| A metric value (weight, …) | `metric G02 76.1 --evidence photo\|verbal [--note]` |
| Funnel progress (got an interview) | `funnel G03 Interview +1 --evidence link --note "Company X first round"` |
| Learning units | `units G04 --done 7 --mastered 6 --evidence link`, plus `log` on the action if relevant |
| A phase is complete | `phase done G01.M2 --evidence code --note …` (mishu.py asks for confirmation if actions are still open) |
| Blocked, waiting on someone | `task set G01.T06 blocked --wait Sam` |
| Started working on it | `task set G01.T05 doing` |

## 3. Apply the goal's evidence method
First run `status GID` to see its `verify` settings, then:

### repo: code check
Dispatch a read-only sub-agent before writing, when `when` is `every` or this is a phase completion. The template is in `references/evidence.md`.
- **"Done":** log 🔍 with the commit hash in the note.
- **"Partial" or "no evidence":** show the user the difference and let them decide.
  - If the user insists it's done, log ✓ 💬 with the note "user reports done; check found no X".
  - If the user agrees with the check, log what the check found, with 🔍.

### photo
1. **Photo uploaded:** read the key value (e.g. the scale) and **read it back**: "I see 76.1 kg, right?" Once confirmed, log 📷 with the note "photo viewed, not stored".
2. **No photo, and this entry is within `when`:** politely ask for one, **once**.
3. **Declined, not convenient, or no reply:** log 💬. **Don't ask again, and don't comment.**
4. **Unreadable or ambiguous** (e.g. lb vs kg): ask for the number and log 💬. **Never guess a reading.**
5. **Storing the photo:** only run `evidence add GID <path>` when the user explicitly asks you to store it and gives a local path. Put the filename in the note.

### link
Ask for a link, screenshot or path; without one, log verbal.

### verbal
Log it.

## 4. Respond
- **Confirm the write** in one sentence, quoting mishu.py's numbers (e.g. "G02 progress 24%").
- **Act on hints** (🎉 all done, phase complete, no next action) the same way as step 7 of the check-in workflow.
- **Pace light changed?** If the entry changed a goal's light, mention it briefly.
