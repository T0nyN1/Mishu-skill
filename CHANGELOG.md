# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed
- **Quieter web dashboard.** Today's list shows the task alone with a toggle for the details; habits, errands and the evening check-in are no longer shown there (they stay in the Markdown daily file). Advice cards moved to the sidebar, the inbox panel is now "Needs your input", goal cards keep five short lines with everything else behind a "Details" toggle, actions are numbered 1. 2. 3. instead of T01, and the evidence method is no longer printed on the card.

### Added
- **Checkboxes on the dashboard.** Actions and today's items can be ticked off while you work. The state lives in the browser only; a tray offers "reply to Mishu", which copies a ready-made message to paste into the conversation. `mishu.py` is still the only writer.
- **Completed history.** Setting a goal to `done` now stamps a completion date. The board and web dashboard get a "Completed" block with a short brief per goal (dates, days taken, time spent, actions done, definition of done), and the new `done` command lists every completed goal with its closing note. Reopening a goal clears the date.
- Both demo vaults include a goal completed in August.

### Fixed
- The daily candidate picker could suggest a later action before an earlier one in the same goal and phase (e.g. "place the order" before "compare keyboards"). Actions are now suggested in order, and a skipped action is labelled "after G01.T01".
- Chinese advice cards had a stray space after 「代价：」; the "Your call" and "Reason" labels used half-width colons.
- Chinese lists in candidates and error messages used English commas.
- Processing an inbox item shifts the numbers of the remaining items; mishu.py now prints the renumbered list, and the workflows tell Mishu to re-list before each `--inbox N`.

## [0.2.0] - 2026-09-14

### Changed
- **Renamed the project to Mishu (秘书).**
  - Skill: `skill/mishu`, invoked as `/mishu`.
  - CLI: `sec.py` → `mishu.py`.
  - Vault metadata: `.secretary/` → `.mishu/`.
  - Config: `~/.config/mishu/`.
  - Environment variables: `MISHU_VAULT`, `MISHU_CONFIG`, `MISHU_TODAY`.
- Skill instructions (SKILL.md, workflows, references) are now written in English. Mishu still talks to users in their own language.
- Docs moved to `docs/en/` and `docs/zh-CN/`.

### Added
- **English/Chinese output.** Each vault's `profile.lang` (`en`/`zh`) selects the language of the board, daily plans, check-ins, advice cards, CLI messages and the web dashboard. Goal files and daily plans parse in either language, so you can switch at any time without migrating.
- **Empty first run with guided onboarding.**
  - `context` detects an empty or unconfigured vault.
  - The setup workflow walks the user through a brain dump, picking the top 3–5 goals, and intake for each.
  - The dashboard and board show a welcome panel while the vault is empty.
- **Demo vaults in both languages:** `bash examples/build_demo.sh [en|zh|all]`.
- **English README and CONTRIBUTING**, alongside the Chinese versions.
- **A translation-coverage test** and Chinese-output tests (22 tests in total).
- **Advice categories** now use `nudge`/`adjust`/`coach`/`insight`; the Chinese names are still accepted as aliases.

## [0.1.0] - 2026-09-14

First usable version (MVP, named "Secretary").

### Added
- **Universal paradigm:** 5 goal types; 4 progress methods × 3 pace methods; one vocabulary of IDs and status, result, evidence and reason codes.
- **The CLI as the vault's only writer:**
  - Definition of Ready, capacity gate, external-edit hash detection.
  - Progress, pace lights, staleness, candidate scoring.
  - Rendering of the board, daily plans, check-ins and advice cards.
  - Progress-level vs. structural write permissions.
- **A read-only web dashboard** (single file, light/dark, responsive).
- **A PreToolUse write guard**, with a dev mode.
- **Workflows:** setup, add (7-step intake), today, checkin, log, stuck (coach mode), status.
- **Evidence protocol:** read-only sub-agent code checks, photo checks with a verbal fallback, links.
