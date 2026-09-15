#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""guard.py — Mishu write guard (PreToolUse hook).

Once the skill has been invoked, this guard stays active for the rest of the session:
  1. blocks Edit / Write / MultiEdit / NotebookEdit on vault files;
  2. blocks edits to the skill itself (mishu.py, dashboard, workflows, references);
  3. blocks Bash commands that bypass mishu.py to write those places (redirects, sed -i, rm, mv, cp, ...).

The vault can only be written through mishu.py. To work on the skill itself, the user (not the AI)
creates ~/.config/mishu/dev_mode, which unlocks the skill directory; the vault stays protected.

This is a guard rail against the model casually bypassing the rules — not a security sandbox.
"""
import json
import os
import re
import shlex
import sys
from pathlib import Path

WRITE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
BASH_WRITE = re.compile(
    r"(\bsed\s+(-[a-zA-Z]*i|--in-place)|\bperl\s+-[a-zA-Z]*i|\brm\b|\bmv\b|\bcp\b|\btouch\b|\bmkdir\b|\bln\b"
    r"|\bchmod\b|\btruncate\b|\btee\b|\bdd\b|\bgit\s+(checkout|reset|restore|clean|stash)\b|\bpython3?\s+-c\b"
    r"|\bnode\s+-e\b|\bruby\s+-e\b|\bawk\b.*-i\s+inplace)"
)


def config_dir():
    cfg = os.environ.get("MISHU_CONFIG")
    return Path(cfg).expanduser().parent if cfg else Path("~/.config/mishu").expanduser()


def protected_roots():
    roots = []
    try:
        vault = json.loads((config_dir() / "config.json").read_text("utf-8")).get("vault")
        if vault:
            roots.append(("the Mishu vault", Path(vault).expanduser().resolve()))
    except (OSError, ValueError):
        pass
    if os.environ.get("MISHU_VAULT"):
        roots.append(("the Mishu vault", Path(os.environ["MISHU_VAULT"]).expanduser().resolve()))
    if not (config_dir() / "dev_mode").exists():
        roots.append(("the Mishu skill", Path(__file__).resolve().parent.parent))
    return roots


def hit(path_str, roots, cwd):
    if not path_str:
        return None
    p = Path(os.path.expanduser(path_str))
    if not p.is_absolute():
        p = Path(cwd) / p
    try:
        rp = p.resolve()
    except OSError:
        return None
    for label, root in roots:
        if rp == root or root in rp.parents:
            return label, rp
    return None


def deny(label, target):
    msg = (f"🛡 Mishu guard: direct writes to {label} are blocked ({target}).\n"
           "- Vault data can only be written through mishu.py (progress: log/metric/funnel/units/checkin; "
           "structure: set --confirmed).\n"
           "- The skill code, dashboard renderer, workflows and references must not be changed while in use.\n"
           "- If mishu.py lacks a feature or has a bug, stop and tell the user honestly — do not try to work around it.\n"
           "🛡 秘书守卫：禁止绕过 mishu.py 直接修改档案库或 skill 文件。")
    print(msg, file=sys.stderr)
    sys.exit(2)


def main():
    try:
        data = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)
    tool = data.get("tool_name", "")
    ti = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()
    roots = protected_roots()
    if not roots:
        sys.exit(0)

    if tool in WRITE_TOOLS:
        h = hit(ti.get("file_path") or ti.get("notebook_path"), roots, cwd)
        if h:
            deny(*h)
        sys.exit(0)

    if tool == "Bash":
        cmd = ti.get("command") or ""
        home = str(Path.home())
        for seg in re.split(r"(?:&&|\|\||;|\||\n)", cmd):
            if not seg.strip():
                continue
            is_tool = re.search(r"\bmishu\.py\b", seg) is not None
            for m in re.finditer(r"(?<![0-9&])>>?\s*([^\s;&|]+)", seg):
                h = hit(m.group(1).strip("'\""), roots, cwd)
                if h:
                    deny(*h)
            if is_tool:
                continue
            if BASH_WRITE.search(seg):
                try:
                    tokens = shlex.split(seg)
                except ValueError:
                    tokens = seg.split()
                for tok in tokens:
                    if "/" in tok or tok.startswith("~") or tok.startswith("."):
                        h = hit(tok, roots, cwd)
                        if h:
                            deny(*h)
                for label, root in roots:
                    if str(root) in seg or str(root).replace(home, "~") in seg:
                        deny(label, root)
    sys.exit(0)


if __name__ == "__main__":
    main()
