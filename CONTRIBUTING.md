# Contributing

**English** · [简体中文](CONTRIBUTING.zh-CN.md)

Thanks for helping improve Mishu!

## Setup

- Python 3.9+. **No third-party dependencies:** `mishu.py`, `i18n.py`, `dashboard.py` and `guard.py` use only the standard library.
- Run the tests before you start, to confirm a green baseline:
  ```bash
  python3 -m unittest discover -s tests -v
  ```
- If you work on the skill inside a Claude Code session where `/mishu` was invoked, enable dev mode first: `touch ~/.config/mishu/dev_mode`.

## Design principles (check before submitting)

1. **Markdown is the single source of truth.** New features must not introduce a second copy of state. The dashboard stays read-only.
2. **Scripts compute, the AI judges.** If a constraint can be expressed as a deterministic rule, put it in `mishu.py`, not only in a prompt.
3. **Consistent formats.** New outputs must use the vocabulary and fixed blocks in the paradigm spec ([EN](docs/en/paradigm-spec.md) / [中文](docs/zh-CN/paradigm-spec.md)). If you change the spec, update both language versions and `skill/mishu/references/vocabulary.md`.
4. **Both languages, always.** Every user-facing string goes through `tr()` (or `_t()` in the dashboard) with an English source string and a Chinese entry in `i18n.py`. `tests/test_mishu.py` fails if a translation is missing.
5. **Never loosen write permissions.** Structural changes require `--confirmed --reason` and log a decision; logs are append-only.
6. **Respect the user.** Evidence requests always leave a way out. No nagging, no lecturing. Photos aren't stored by default.
7. **First run is empty.** Nothing from `examples/` may leak into a user's vault.

## Submitting changes

- Add tests in `tests/test_mishu.py` when you change `mishu.py` behaviour.
- After changing rendering, run `bash examples/build_demo.sh` and commit the regenerated demo vaults.
- Update the screenshots in `docs/images/` for significant UI changes.
- Describe your change under "Unreleased" in `CHANGELOG.md`.
