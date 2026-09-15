# Workflow: view & manage (status)

## Viewing
| The user wants | Do |
|---|---|
| The dashboard | `board --open` opens `dashboard.html` in the browser. **Prefer this when they want "the big picture".** |
| The board in chat | `board --print` pastes the Markdown board. If it's long, show "Needs attention" and "Goals overview" first. |
| One goal | `status G01` |
| Everything | `status` |
| Recent performance | `stats --days 7` or `stats --days 14` |
| The inbox | `inbox list` |
| Completed goals ("what have I finished?") | `done` (add `--limit 5` for the latest). The dashboard's "Completed" panel shows the same briefs |

Show mishu.py output as-is. You may add 1–3 sentences of interpretation, but **never rewrite the numbers**.

## Managing (all structural: explain and get explicit confirmation first)

| Action | Command |
|---|---|
| Pause | `set G06 status paused --confirmed --reason "…" --revisit 2026-10-15` |
| Resume | `set G06 status active --confirmed --reason "…"` (capacity is re-checked) |
| Finish | `set G05 status done --confirmed --reason "definition of done met: …"` (archived automatically; the completion date is stamped and the reason becomes the closing note shown in `done` and on the dashboard) |
| Drop | `set G07 status dropped --confirmed --reason "…"` (archived, decision kept) |
| Change deadline or budget | `set G01 deadline 2026-12-15! --confirmed --reason "…"` |
| Change priority | `set G04 priority P1 --confirmed --reason "…"` |
| Switch output language | `profile set lang zh --confirmed --reason "user prefers Chinese"` (existing files still parse) |
| Turn an inbox item into a goal | Run `workflows/add.md` with `--inbox N` |
| Discard an inbox item | `inbox done --n N` (with the user's OK) |

When finishing a goal:
1. Confirm against `done_when` with the user that it's really met.
2. Congratulate briefly.
3. Mention how many weekly hours it frees up.

## When something's off
- **`validate` errors:** relay them as-is. If the user hand-edited a file, ask them to fix it; you can't edit vault files.
- **"Edited outside mishu.py":** confirm with the user that they made the edit.
- **The user wants the board or its format hand-edited:** explain that it's generated and manual edits get overwritten. Capture format requests in the inbox as feedback for the skill.
