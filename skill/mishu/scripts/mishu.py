#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mishu.py — command-line tool for the Mishu vault.

This script is the vault's ONLY writer: goals, actions, logs, decisions, daily
plans and boards are all read, written and rendered here. The AI never edits
vault files directly.

Output language follows the vault profile (`lang: en | zh`).
Python 3.9+ standard library only. Usage: python3 mishu.py <command> --help
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from i18n import ZH  # noqa: E402

VERSION = "0.2.0"

# ═══════════════════════════════════════════════════════════════ language
LANGS = ("en", "zh")
_LANG = "en"


def set_lang(code):
    global _LANG
    _LANG = code if code in LANGS else "en"


def cur_lang():
    return _LANG


def tr(_msg, /, **kw):
    """Translate an English template into the vault language, then format it."""
    tpl = ZH.get(_msg, _msg) if _LANG == "zh" else _msg
    return tpl.format(**kw) if kw else tpl


def sep():
    """List separator used inside a sentence."""
    return "；" if _LANG == "zh" else "; "


def paren(s):
    return f"（{s}）" if _LANG == "zh" else f" ({s})"


# ═══════════════════════════════════════════════════════════════ vocabulary
TYPE_ICON = {"project": "🏗", "habit": "🔁", "errand": "📦", "pipeline": "🎯", "learning": "📚"}
TYPE_NAME = {"project": "Project", "habit": "Habit", "errand": "Errand", "pipeline": "Pipeline", "learning": "Learning"}
TYPE_DEFAULTS = {
    "project": ("phases", "timeline"),
    "habit": ("metric", "frequency"),
    "errand": ("checklist", "deadline"),
    "pipeline": ("phases", "frequency"),
    "learning": ("units", "timeline"),
}
DEFAULT_VERIFY = {
    "project": {"method": "verbal", "when": "milestone", "fallback": "verbal"},
    "habit": {"method": "photo", "when": "metric", "fallback": "verbal"},
    "errand": {"method": "verbal", "when": "every", "fallback": "verbal"},
    "pipeline": {"method": "link", "when": "metric", "fallback": "verbal"},
    "learning": {"method": "link", "when": "milestone", "fallback": "verbal"},
}
STATUSES = ["inbox", "draft", "active", "paused", "done", "dropped", "someday"]
STATUS_ICON = {"paused": "⏸", "done": "✅", "dropped": "🗑", "draft": "📝", "someday": "💭", "inbox": "📥"}
PRIORITY_W = {"P0": 3.0, "P1": 2.0, "P2": 1.0, "P3": 0.5}
PROGRESS_KINDS = ["phases", "metric", "units", "checklist"]
PACE_KINDS = ["timeline", "frequency", "deadline"]
PHASE_STATUSES = ["todo", "active", "done"]
VERIFY_METHODS = ["repo", "photo", "link", "verbal"]
VERIFY_WHEN = ["every", "metric", "milestone"]

TASK_MARK = {" ": "todo", "/": "doing", "x": "done", "!": "blocked", "-": "cancel"}
MARK_OF = {v: k for k, v in TASK_MARK.items()}

RESULTS = {"✓": "Done", "◐": "Partial", "✗": "Not done", "➜": "Moved", "✂": "Cancelled", "=": "Value update"}
RESULT_ALIAS = {"done": "✓", "partial": "◐", "skip": "✗", "moved": "➜", "cancel": "✂", "update": "="}
EVIDENCE = {"🔍": "Code check", "📷": "Photo", "🔗": "Link/file", "💬": "Verbal", "⚙️": "System"}
EVIDENCE_ALIAS = {"code": "🔍", "photo": "📷", "link": "🔗", "verbal": "💬", "auto": "⚙️"}
REASONS = {"T": "No time", "E": "Low energy", "U": "Unclear", "A": "Avoiding it", "B": "Blocked",
           "O": "Underestimated", "P": "Plan changed"}
ADVICE_CATS = {"nudge": "Nudge", "adjust": "Adjust", "coach": "Coach", "insight": "Insight"}
ADVICE_ALIAS = {"提醒": "nudge", "调整": "adjust", "教练": "coach", "洞察": "insight"}
LEVELS = ["L0", "L1", "L2", "L3", "L4"]
WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
WD_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WD_ZH = "一二三四五六日"
LIGHT_ORDER = {"🔴": 0, "🟡": 1, "🟢": 2, "⚪": 3}
LIGHT_CLASS = {"🟢": ("ok", "On track"), "🟡": ("warn", "Watch"), "🔴": ("crit", "At risk"),
               "⚪": ("idle", "Not started"), "⏸": ("idle", "Paused"), "✅": ("ok", "Done"),
               "💭": ("idle", "Someday"), "📝": ("idle", "Draft"), "🗑": ("idle", "Dropped"), "📥": ("idle", "Inbox")}

# Section headers are written in the vault language but read in either language.
GOAL_SECTIONS = {"tasks": {"en": "Actions", "zh": "行动"}, "logs": {"en": "Log", "zh": "日志"},
                 "decisions": {"en": "Decisions", "zh": "决策"}}
SECTION_KEY = {name: key for key, names in GOAL_SECTIONS.items() for name in names.values()}
DECISION_PARTS = {"reason": ("Reason: ", "原因："), "revisit": ("Revisit: ", "回看："), "source": ("Source: ", "来源：")}
FUNNEL_PREFIXES = ("funnel:", "漏斗:")
REVIEW_RE = re.compile(r"^## 🌙", re.M)
DAILY_SECTIONS = {"🎯": "main", "🔁": "habit", "⚡": "errand", "👀": "waiting", "💡": "advice"}

SET_FIELDS = [
    "title", "area", "priority", "status", "start", "deadline", "budget", "done_when", "why", "review",
    "verify.method", "verify.repo", "verify.when", "verify.fallback",
    "measure.metric.target", "measure.metric.baseline", "measure.frequency.per_week",
    "measure.units.total", "measure.funnel.target",
]
PROFILE_FIELDS = ["name", "lang", "weekly_capacity", "daily_default", "weekend_default", "wip_limit",
                  "stale_days", "tone", "day_start", "checkin_time", "areas"]
DEFAULT_AREAS = {"en": ["Career", "Learning", "Health", "Life", "Finance", "Relationships"],
                 "zh": ["事业", "学习", "健康", "生活", "财务", "关系"]}


class MishuError(Exception):
    def __init__(self, msg, code=1):
        super().__init__(msg)
        self.code = code


# ═══════════════════════════════════════════════════════════════ helpers
_TODAY = None


def today() -> dt.date:
    if _TODAY:
        return _TODAY
    env = os.environ.get("MISHU_TODAY")
    return dt.date.fromisoformat(env) if env else dt.date.today()


def parse_date(s):
    """Return (date or None, is_hard_deadline)."""
    if s is None or str(s).strip() == "":
        return None, False
    s = str(s).strip()
    hard = s.endswith("!")
    s = s.rstrip("!")
    try:
        return dt.date.fromisoformat(s), hard
    except ValueError:
        pass
    m = re.fullmatch(r"(\d{1,2})-(\d{1,2})", s)
    if m:
        t = today()
        d = dt.date(t.year, int(m.group(1)), int(m.group(2)))
        if (t - d).days > 180:
            d = d.replace(year=t.year + 1)
        return d, hard
    raise MishuError(tr("Cannot parse date: {s} (use YYYY-MM-DD; append ! for a hard deadline)", s=s))


def norm_date(s, allow_hard=True):
    d, hard = parse_date(s)
    if not d:
        return None
    return d.isoformat() + ("!" if hard and allow_hard else "")


DUR_RE = re.compile(r"^(?:(\d+(?:\.\d+)?)h)?(?:(\d+)m)?$")


def parse_minutes(s):
    if s is None or s == "":
        return None
    if isinstance(s, (int, float)):
        return int(s)
    s = str(s).strip()
    m = DUR_RE.fullmatch(s)
    if not s or not m or (m.group(1) is None and m.group(2) is None):
        raise MishuError(tr("Cannot parse duration: {s} (e.g. 45m, 2h, 1h30m)", s=s))
    return int(round(float(m.group(1) or 0) * 60 + int(m.group(2) or 0)))


def minutes_in(text):
    total = 0
    for m in re.finditer(r"(\d+(?:\.\d+)?)h(?:(\d+)m)?(?![a-zA-Z])|(?<![\d.])(\d+)m(?![a-zA-Z])", str(text or "")):
        if m.group(1):
            total += float(m.group(1)) * 60 + int(m.group(2) or 0)
        else:
            total += int(m.group(3))
    return int(round(total))


def fmt_hm(minutes):
    minutes = int(round(minutes or 0))
    h, m = divmod(minutes, 60)
    if h and m:
        return f"{h}h{m}m"
    return f"{h}h" if h else f"{m}m"


def parse_hours(s):
    if s is None or s == "":
        return None
    if isinstance(s, (int, float)):
        return float(s)
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*h(?:/w)?", str(s).strip())
    if not m:
        raise MishuError(tr("Cannot parse hours: {s} (e.g. 25h, 8h/w)", s=s))
    return float(m.group(1))


def num(v, name="value"):
    try:
        f = float(v)
    except (TypeError, ValueError):
        raise MishuError(tr("{name} must be a number: {v}", name=name, v=v))
    return int(f) if f.is_integer() else f


def gnum(x):
    return f"{x:g}" if isinstance(x, float) else str(x)


def clean(text):
    """Strip separators that would break the line formats."""
    return re.sub(r"\s+", " ", str(text or "").replace("|", "/").replace(" · ", "·")).strip()


def bar(p):
    p = max(0.0, min(1.0, p or 0))
    n = int(round(p * 10))
    return "▓" * n + "░" * (10 - n) + f" {p:.0%}"


def short(s, n=16):
    s = str(s or "")
    return s if len(s) <= n else s[: n - 1] + "…"


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def weekday_name(d):
    return "周" + WD_ZH[d.weekday()] if _LANG == "zh" else WD_EN[d.weekday()]


def read_stdin_or_file(path):
    if path == "-":
        return sys.stdin.read()
    return Path(path).expanduser().read_text("utf-8")


def type_label(t):
    return tr(TYPE_NAME.get(t, t or ""))


def unit_label(f):
    return (f or {}).get("unit") or tr("times")


# ═══════════════════════════════════════════════════════════════ mini YAML
# Only the subset Mishu needs: mappings, indented nesting, lists, flow {…}/[…], scalars.

def _strip_comment(s):
    out, q = [], None
    for i, ch in enumerate(s):
        if q:
            if ch == q:
                q = None
        elif ch in "\"'" and (i == 0 or s[i - 1] in " ,[{:"):
            q = ch
        elif ch == "#" and (i == 0 or s[i - 1] in " \t"):
            break
        out.append(ch)
    return "".join(out).rstrip()


def _scalar(s):
    s = s.strip()
    if s in ("", "~", "null"):
        return None
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        inner = s[1:-1]
        if s[0] == '"':
            inner = inner.replace('\\"', '"').replace("\\\\", "\\")
        return inner
    if s == "true":
        return True
    if s == "false":
        return False
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    return s


def _split_top(s):
    parts, cur, depth, q = [], [], 0, None
    for ch in s:
        if q:
            cur.append(ch)
            if ch == q:
                q = None
            continue
        prev = "".join(cur).rstrip()
        if ch in "\"'" and (prev == "" or prev.endswith(":")):
            q = ch
            cur.append(ch)
            continue
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur))
    return parts


def _value(s):
    s = s.strip()
    if s.startswith("{") and s.endswith("}"):
        d = {}
        for part in _split_top(s[1:-1]):
            k, _, v = part.partition(":")
            d[k.strip()] = _value(v)
        return d
    if s.startswith("[") and s.endswith("]"):
        return [_value(p) for p in _split_top(s[1:-1])]
    return _scalar(s)


def _parse_block(lines, i, indent):
    if i >= len(lines):
        return None, i
    if lines[i][1].startswith("- ") or lines[i][1] == "-":
        res = []
        while i < len(lines) and lines[i][0] == indent and (lines[i][1].startswith("- ") or lines[i][1] == "-"):
            item = lines[i][1][2:].strip()
            i += 1
            if re.match(r"^[^\s{\[\"'][^:]*:(\s|$)", item):
                sub = [(indent + 2, item)]
                while i < len(lines) and lines[i][0] > indent:
                    sub.append(lines[i])
                    i += 1
                v, _ = _parse_block(sub, 0, indent + 2)
                res.append(v)
            else:
                res.append(_value(item))
        return res, i
    res = {}
    while i < len(lines) and lines[i][0] == indent:
        content = lines[i][1]
        m = re.match(r"^([^:]+?):(?:\s+(.*))?$", content)
        if not m or content.startswith("- "):
            raise MishuError(tr("Cannot parse YAML line: {line}", line=content))
        key, rest = m.group(1).strip(), m.group(2)
        i += 1
        if rest is None or rest == "":
            if i < len(lines) and lines[i][0] > indent:
                v, i = _parse_block(lines, i, lines[i][0])
            elif i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("- "):
                v, i = _parse_block(lines, i, indent)
            else:
                v = None
            res[key] = v
        else:
            res[key] = _value(rest)
    if i < len(lines) and lines[i][0] > indent:
        raise MishuError(tr("YAML indentation error: {line}", line=lines[i][1]))
    return res, i


def yaml_load(text):
    lines = []
    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        line = _strip_comment(raw)
        if not line.strip():
            continue
        lines.append((len(line) - len(line.lstrip(" ")), line.strip()))
    if not lines:
        return {}
    val, i = _parse_block(lines, 0, lines[0][0])
    if i < len(lines):
        raise MishuError(tr("YAML structure error near: {line}", line=lines[i][1]))
    return val or {}


def _needs_quote(s):
    if s == "" or s != s.strip():
        return True
    if re.search(r"[,:{}\[\]#\"']", s):
        return True
    if s in ("true", "false", "null", "~") or re.fullmatch(r"-?\d+(\.\d+)?", s):
        return True
    return s[0] in "-!&*?|>%@`"


def _dump_scalar(v):
    if v is None:
        return ""
    if v is True:
        return "true"
    if v is False:
        return "false"
    if isinstance(v, (int, float)):
        return gnum(v)
    s = str(v)
    if _needs_quote(s):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def _flow(v):
    if isinstance(v, dict):
        return "{" + ", ".join(f"{k}: {_flow(x)}" for k, x in v.items()) + "}"
    if isinstance(v, list):
        return "[" + ", ".join(_flow(x) for x in v) + "]"
    return _dump_scalar(v)


def yaml_dump(d, indent=0):
    out, pad = [], " " * indent
    for k, v in d.items():
        if isinstance(v, dict):
            flat = all(not isinstance(x, (dict, list)) for x in v.values())
            if not v or (indent > 0 and flat):
                out.append(f"{pad}{k}: {_flow(v)}")
            else:
                out.append(f"{pad}{k}:")
                out.extend(yaml_dump(v, indent + 2))
        elif isinstance(v, list):
            if all(not isinstance(x, (dict, list)) for x in v):
                out.append(f"{pad}{k}: {_flow(v)}")
            else:
                out.append(f"{pad}{k}:")
                out.extend(f"{pad}  - {_flow(x)}" for x in v)
        else:
            out.append(f"{pad}{k}: {_dump_scalar(v)}".rstrip())
    return out


def split_frontmatter(text, name="file"):
    if not re.match(r"^---\s*\n", text):
        raise MishuError(tr("{name} has no YAML frontmatter (must start with ---)", name=name))
    start = text.index("\n") + 1
    m = re.search(r"^---\s*$", text[start:], re.M)
    if not m:
        raise MishuError(tr("{name}: frontmatter is missing its closing ---", name=name))
    return text[start:start + m.start()], text[start + m.end():].lstrip("\n")


# ═══════════════════════════════════════════════════════════════ data model
TASK_RE = re.compile(r"^- \[(.)\] (T\d+) (.+)$")


class Task:
    ORDER = ["due", "every", "qty", "min", "defer", "wait", "since"]

    def __init__(self, tid, mark=" ", title="", est=None, phase=None, fields=None, extra=None):
        self.tid, self.mark, self.title = tid, mark, title
        self.est, self.phase = est, phase
        self.fields = fields or {}
        self.extra = extra or []

    @classmethod
    def parse(cls, line, where=""):
        m = TASK_RE.match(line.rstrip())
        if not m:
            raise MishuError(tr("{where}cannot parse action line: {line}", where=where, line=line))
        mark, tid, rest = m.groups()
        if mark not in TASK_MARK:
            raise MishuError(tr("{where}unknown action status [{mark}]: {line}", where=where, mark=mark, line=line))
        segs = [s.strip() for s in rest.split(" · ")]
        t = cls(tid, mark, segs[0])
        for s in segs[1:]:
            if not s:
                continue
            if re.fullmatch(r"M\d+", s):
                t.phase = s
            elif DUR_RE.fullmatch(s):
                t.est = parse_minutes(s)
            elif re.fullmatch(r"[a-z_]+:.+", s):
                k, v = s.split(":", 1)
                t.fields[k] = v.strip()
            else:
                t.extra.append(s)
        return t

    @property
    def status(self):
        return TASK_MARK[self.mark]

    @property
    def defer(self):
        try:
            return int(self.fields.get("defer") or 0)
        except ValueError:
            return 0

    @property
    def open(self):
        return self.mark in " /"

    def dump(self):
        parts = [f"- [{self.mark}] {self.tid} {clean(self.title)}"]
        if self.est is not None:
            parts.append(f"{self.est}m")
        if self.phase:
            parts.append(self.phase)
        keys = [k for k in self.ORDER if k in self.fields] + [k for k in self.fields if k not in self.ORDER]
        for k in keys:
            v = self.fields[k]
            if v in (None, "") or (k == "defer" and str(v) == "0"):
                continue
            parts.append(f"{k}:{clean(v)}")
        parts += self.extra
        return " · ".join(parts)


class Log:
    def __init__(self, date, ref, result, value="", evidence="", note=""):
        self.date, self.ref, self.result = date, ref, result
        self.value, self.evidence, self.note = value, evidence, note

    @classmethod
    def parse(cls, line):
        parts = [p.strip() for p in line[2:].split("|")]
        if len(parts) == 5:
            parts.insert(4, "")
        parts += [""] * (6 - len(parts))
        if len(parts) > 6:
            parts = parts[:5] + ["/".join(parts[5:])]
        return cls(*parts)

    @property
    def reason(self):
        m = re.match(r"^\[([A-Z])\]", self.note or "")
        return m.group(1) if m else None

    def dump(self):
        return ("- " + " | ".join(clean(x) for x in
                                  [self.date, self.ref, self.result, self.value, self.evidence, self.note])).rstrip()


class Decision:
    def __init__(self, date, did, text, reason="", revisit="", source=""):
        self.date, self.did, self.text = date, did, text
        self.reason, self.revisit, self.source = reason, revisit, source

    @classmethod
    def parse(cls, line):
        parts = [p.strip() for p in line[2:].split("|")]
        d = cls(parts[0] if parts else "", parts[1] if len(parts) > 1 else "", parts[2] if len(parts) > 2 else "")
        for p in parts[3:]:
            for attr, prefixes in DECISION_PARTS.items():
                for pre in prefixes:
                    if p.startswith(pre):
                        setattr(d, attr, p[len(pre):].strip())
        return d

    def dump(self):
        parts = [self.date, self.did, clean(self.text)]
        idx = 1 if _LANG == "zh" else 0
        for attr in ("reason", "revisit", "source"):
            if getattr(self, attr):
                parts.append(DECISION_PARTS[attr][idx] + clean(getattr(self, attr)))
        return "- " + " | ".join(parts)


GOAL_KEY_ORDER = ["id", "title", "type", "area", "priority", "status", "created", "start", "deadline",
                  "why", "done_when", "budget", "review", "verify", "measure", "phases"]


class Goal:
    def __init__(self, path, meta, tasks=None, logs=None, decisions=None, extras=None, preamble=None):
        self.path, self.meta = path, meta
        self.tasks = tasks or []
        self.logs = logs or []
        self.decisions = decisions or []
        self.extras = extras or []
        self.preamble = preamble or []

    @classmethod
    def load(cls, path: Path):
        text = path.read_text("utf-8")
        fm, body = split_frontmatter(text, path.name)
        g = cls(path, yaml_load(fm))
        section = None
        where = f"{path.name}: "
        for line in body.splitlines():
            if line.startswith("## "):
                section = SECTION_KEY.get(line[3:].strip())
                if section is None:
                    g.extras.append([line, []])
                    section = "extra"
                continue
            if section == "tasks":
                if line.strip():
                    g.tasks.append(Task.parse(line, where))
            elif section == "logs":
                if line.startswith("- "):
                    g.logs.append(Log.parse(line))
                elif line.strip():
                    raise MishuError(tr("{where}cannot parse log line: {line}", where=where, line=line))
            elif section == "decisions":
                if line.startswith("- "):
                    g.decisions.append(Decision.parse(line))
                elif line.strip():
                    raise MishuError(tr("{where}cannot parse decision line: {line}", where=where, line=line))
            elif section is None:
                if line.strip():
                    g.preamble.append(line)
            else:
                g.extras[-1][1].append(line)
        return g

    gid = property(lambda s: str(s.meta.get("id") or ""))
    title = property(lambda s: str(s.meta.get("title") or ""))
    type = property(lambda s: s.meta.get("type"))
    status = property(lambda s: s.meta.get("status"))
    priority = property(lambda s: s.meta.get("priority") or "P2")
    measure = property(lambda s: s.meta.get("measure") or {})
    phases = property(lambda s: s.meta.get("phases") or [])
    verify = property(lambda s: s.meta.get("verify") or {})

    @property
    def recurring_ids(self):
        ids = {t.tid for t in self.tasks if t.fields.get("every")}
        ftask = (self.measure.get("frequency") or {}).get("task")
        if ftask:
            ids.add(ftask)
        return ids

    def task(self, tid):
        for t in self.tasks:
            if t.tid == tid:
                return t
        raise MishuError(tr("Action {tid} not found in {gid}", tid=tid, gid=self.gid))

    def phase(self, pid):
        for p in self.phases:
            if p.get("id") == pid:
                return p
        raise MishuError(tr("Phase {pid} not found in {gid}", pid=pid, gid=self.gid))

    def next_task_id(self):
        n = max([int(t.tid[1:]) for t in self.tasks] + [0])
        return f"T{n + 1:02d}"

    def next_decision_id(self):
        n = max([int(d.did[1:]) for d in self.decisions if re.fullmatch(r"D\d+", d.did)] + [0])
        return f"D{n + 1:02d}"

    def filename(self):
        if self.path and self.path.name.startswith(self.gid + "-"):
            return self.path.name
        slug = re.sub(r"[\\/:*?\"<>|\s]+", "-", self.title).strip("-")[:32] or "goal"
        return f"{self.gid}-{slug}.md"

    def dump(self):
        meta = {k: self.meta[k] for k in GOAL_KEY_ORDER if k in self.meta}
        meta.update({k: v for k, v in self.meta.items() if k not in meta})
        head = {k: GOAL_SECTIONS[k][_LANG] for k in GOAL_SECTIONS}
        lines = ["---", *yaml_dump(meta), "---", ""]
        if self.preamble:
            lines += self.preamble + [""]
        lines += [f"## {head['tasks']}", *[t.dump() for t in self.tasks], "",
                  f"## {head['logs']}", *[lg.dump() for lg in self.logs], "",
                  f"## {head['decisions']}", *[d.dump() for d in self.decisions]]
        for header, content in self.extras:
            while content and not content[-1].strip():
                content.pop()
            lines += ["", header, *content]
        return "\n".join(lines).rstrip() + "\n"


class Profile:
    DEFAULTS = {"name": "", "lang": "en", "weekly_capacity": "20h", "daily_default": "3h", "weekend_default": "5h",
                "wip_limit": 5, "stale_days": 7, "tone": "coach", "day_start": "08:30",
                "checkin_time": "21:30", "areas": DEFAULT_AREAS["en"]}

    def __init__(self, path):
        self.path = path
        fm, self.body = split_frontmatter(path.read_text("utf-8"), "profile.md")
        self.meta = yaml_load(fm)

    def get(self, k):
        v = self.meta.get(k)
        return self.DEFAULTS.get(k) if v is None else v

    @property
    def capacity(self):
        return parse_hours(self.get("weekly_capacity"))

    @property
    def stale_days(self):
        return int(self.get("stale_days"))

    def dump(self):
        return "\n".join(["---", *yaml_dump(self.meta), "---", ""]) + self.body.rstrip() + "\n"


# ═══════════════════════════════════════════════════════════════ validation
NO_NEXT = "No open next action"


def validate_goal(g: Goal, strict_ready=False):
    E, W = [], []
    m = g.meta
    if not re.fullmatch(r"G\d{2,}", g.gid):
        E.append(tr("id must look like G01"))
    for k in ("title", "type", "area", "priority", "status", "created"):
        if m.get(k) in (None, ""):
            E.append(tr("missing field {k}", k=k))
    if g.type not in TYPE_ICON:
        E.append(tr("type must be one of {v}", v="/".join(TYPE_ICON)))
    if g.status not in STATUSES:
        E.append(tr("status must be one of {v}", v="/".join(STATUSES)))
    if m.get("priority") not in PRIORITY_W:
        E.append(tr("priority must be P0-P3"))
    for k in ("created", "start", "deadline"):
        try:
            parse_date(m.get(k))
        except MishuError as e:
            E.append(f"{k}: {e}")
    if m.get("budget") not in (None, ""):
        try:
            parse_hours(m.get("budget"))
        except MishuError as e:
            E.append(f"budget: {e}")

    meas = g.measure
    prog, pace = meas.get("progress"), meas.get("pace")
    if prog not in PROGRESS_KINDS:
        E.append(tr("measure.progress must be one of {v}", v="/".join(PROGRESS_KINDS)))
    if pace not in PACE_KINDS:
        E.append(tr("measure.pace must be one of {v}", v="/".join(PACE_KINDS)))
    if prog == "metric":
        mt = meas.get("metric") or {}
        for k in ("name", "unit", "baseline", "target", "current", "direction"):
            if mt.get(k) in (None, ""):
                E.append(tr("measure.metric is missing {k}", k=k))
        if mt.get("direction") not in (None, "up", "down"):
            E.append(tr("measure.metric.direction must be up/down"))
        for k in ("baseline", "target", "current"):
            if mt.get(k) is not None and not isinstance(mt.get(k), (int, float)):
                E.append(tr("measure.metric.{k} must be a number", k=k))
    if prog == "units":
        u = meas.get("units") or {}
        if not isinstance(u.get("total"), int) or u.get("total", 0) <= 0:
            E.append(tr("measure.units.total must be a positive integer"))
        for k in ("done", "mastered"):
            if not isinstance(u.get(k, 0), int):
                E.append(tr("measure.units.{k} must be an integer", k=k))
    funnel = meas.get("funnel")
    if funnel is not None:
        if not isinstance(funnel, list) or not funnel:
            E.append(tr("measure.funnel must be a non-empty list"))
        else:
            for st in funnel:
                if not isinstance(st, dict) or not st.get("stage") or not isinstance(st.get("count", 0), int):
                    E.append(tr("bad funnel stage: {st}", st=st))
    if pace == "frequency":
        f = meas.get("frequency") or {}
        if not isinstance(f.get("per_week"), (int, float)) or f.get("per_week", 0) <= 0:
            E.append(tr("measure.frequency.per_week must be a positive number"))
        if f.get("task"):
            if f["task"] not in {t.tid for t in g.tasks}:
                E.append(tr("measure.frequency.task points to a missing action {t}", t=f["task"]))
        elif f.get("stage"):
            if f["stage"] not in [s.get("stage") for s in (funnel or []) if isinstance(s, dict)]:
                E.append(tr("measure.frequency.stage points to a missing funnel stage {s}", s=f["stage"]))
        else:
            E.append(tr("measure.frequency needs task or stage"))

    pids = []
    for p in g.phases:
        if not isinstance(p, dict) or not re.fullmatch(r"M\d+", str(p.get("id") or "")):
            E.append(tr("bad phase: {p}", p=p))
            continue
        if p["id"] in pids:
            E.append(tr("duplicate phase id: {p}", p=p["id"]))
        pids.append(p["id"])
        if p.get("status") not in PHASE_STATUSES:
            E.append(tr("phase {p} status must be todo/active/done", p=p["id"]))
        if not p.get("title"):
            E.append(tr("phase {p} has no title", p=p["id"]))
        try:
            parse_date(p.get("due"))
        except MishuError as e:
            E.append(f"{p['id']}: {e}")
    if prog == "phases" and not pids:
        E.append(tr("progress=phases needs at least one phase"))
    if sum(1 for p in g.phases if isinstance(p, dict) and p.get("status") == "active") > 1:
        W.append(tr("more than one active phase"))

    tids = set()
    for t in g.tasks:
        if t.tid in tids:
            E.append(tr("duplicate action id: {t}", t=t.tid))
        tids.add(t.tid)
        if t.phase and t.phase not in pids:
            E.append(tr("action {t} points to a missing phase {p}", t=t.tid, p=t.phase))
        for k in ("due", "since"):
            try:
                parse_date(t.fields.get(k))
            except MishuError as e:
                E.append(f"{t.tid} {k}: {e}")
        ev = t.fields.get("every")
        if ev and any(x not in WEEKDAYS for x in ev.split(",")):
            E.append(tr("action {t}: every must use {v}", t=t.tid, v=",".join(WEEKDAYS)))
        if t.est and t.est > 120:
            W.append(tr("action {t} is estimated over 2h; consider splitting it", t=t.tid))

    v = g.verify
    if v:
        if v.get("method") not in VERIFY_METHODS:
            E.append(tr("verify.method must be one of {v}", v="/".join(VERIFY_METHODS)))
        if v.get("method") == "repo" and not v.get("repo"):
            E.append(tr("verify.repo is required when verify.method=repo"))
        if v.get("when") not in (None, *VERIFY_WHEN):
            E.append(tr("verify.when must be one of {v}", v="/".join(VERIFY_WHEN)))
        if v.get("fallback") not in (None, *VERIFY_METHODS):
            E.append(tr("verify.fallback is invalid"))

    for lg in g.logs:
        try:
            parse_date(lg.date)
        except MishuError:
            E.append(tr("invalid log date: {d}", d=lg.date))
        if lg.result not in RESULTS:
            E.append(tr("invalid result code: {r} ({line})", r=lg.result, line=lg.dump()))
        if lg.evidence and lg.evidence not in EVIDENCE:
            E.append(tr("invalid evidence code: {e}", e=lg.evidence))

    if g.status == "active" or strict_ready:
        for prob in ready_problems(g, strict=strict_ready):
            # While executing, "no next action" only warns — it must never block recording progress.
            (W if prob == tr(NO_NEXT) and not strict_ready else E).append(prob)
    return E, W


def ready_problems(g: Goal, strict=False):
    """Definition of Ready checklist."""
    P = []
    if not g.meta.get("done_when"):
        P.append(tr("Missing done_when (definition of done)"))
    if not g.meta.get("budget"):
        P.append(tr("Missing budget (hours per week)"))
    if g.measure.get("pace") != "frequency" and not g.meta.get("deadline"):
        P.append(tr("Missing deadline (or use frequency pace)"))
    if not any(t.open for t in g.tasks):
        P.append(tr(NO_NEXT))
    if strict:
        if not any(t.open and (t.est or 0) <= 120 for t in g.tasks):
            P.append(tr("Needs at least one next action of 2h or less"))
        for t in g.tasks:
            if t.est is None:
                P.append(tr("Action {t} has no estimate", t=t.tid))
            elif t.est > 120:
                P.append(tr("Action {t} is estimated at {m}m — over 2h, must be split", t=t.tid, m=t.est))
        if not g.verify:
            P.append(tr("Missing verify (evidence method)"))
    return P


# ═══════════════════════════════════════════════════════════════ vault
def config_path():
    return Path(os.environ.get("MISHU_CONFIG") or "~/.config/mishu/config.json").expanduser()


def resolve_vault_path(arg=None):
    if arg:
        return Path(arg).expanduser().resolve()
    if os.environ.get("MISHU_VAULT"):
        return Path(os.environ["MISHU_VAULT"]).expanduser().resolve()
    cp = config_path()
    if cp.exists():
        v = json.loads(cp.read_text("utf-8")).get("vault")
        if v:
            return Path(v).expanduser().resolve()
    return None


class Vault:
    def __init__(self, root: Path):
        self.root = root
        if not (root / "profile.md").exists():
            raise MishuError(tr("{root} is not a Mishu vault (profile.md missing). Run init first.", root=root), 4)
        self.goals_dir = root / "goals"
        self.archive_dir = root / "goals" / "_archive"
        self.daily_dir = root / "daily"
        self.weekly_dir = root / "weekly"
        self.evidence_dir = root / "evidence"
        self.meta_dir = root / ".mishu"
        self._profile = None
        set_lang(self.profile.get("lang"))

    @property
    def profile(self):
        if not self._profile:
            self._profile = Profile(self.root / "profile.md")
        return self._profile

    # ---- state & audit
    def state(self):
        p = self.meta_dir / "state.json"
        st = json.loads(p.read_text("utf-8")) if p.exists() else {}
        st.setdefault("hashes", {})
        st.setdefault("advice", {})
        return st

    def save_state(self, st):
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        (self.meta_dir / "state.json").write_text(json.dumps(st, ensure_ascii=False, indent=2), "utf-8")

    def log_change(self, cmd, target, detail):
        self.meta_dir.mkdir(parents=True, exist_ok=True)
        rec = {"ts": dt.datetime.now().isoformat(timespec="seconds"), "today": today().isoformat(),
               "cmd": cmd, "target": target, "detail": detail}
        with open(self.meta_dir / "changelog.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # ---- goals
    def goal_paths(self, archive=False):
        paths = sorted(self.goals_dir.glob("G*.md"))
        if archive:
            paths += sorted(self.archive_dir.glob("G*.md"))
        return paths

    def goals(self, archive=False):
        return [Goal.load(p) for p in self.goal_paths(archive)]

    def load_goal(self, gid, for_write=False):
        gid = gid.upper()
        for p in self.goal_paths(archive=True):
            if p.name.split("-")[0] == gid:
                g = Goal.load(p)
                if for_write:
                    self._check_external(g)
                return g
        raise MishuError(tr("Goal {gid} not found", gid=gid))

    def next_goal_id(self):
        n = max([int(p.name.split("-")[0][1:]) for p in self.goal_paths(archive=True)] + [0])
        return f"G{n + 1:02d}"

    def _check_external(self, g):
        st = self.state()
        h, cur = st["hashes"].get(g.gid), sha(g.path)
        if h and h != cur:
            E, _ = validate_goal(g)
            if E:
                raise MishuError(tr("{gid} was edited outside mishu.py and fails validation:", gid=g.gid)
                                 + "\n  - " + "\n  - ".join(E) + "\n"
                                 + tr("Tell the user and let them fix the file before continuing."), 5)
            print(tr("⚠️ {gid} was edited outside mishu.py (valid, accepted). Confirm with the user that they made this edit.",
                     gid=g.gid))
            self.log_change("external-edit", g.gid, "external edit accepted after validation")
            st["hashes"][g.gid] = cur
            self.save_state(st)

    def save_goal(self, g: Goal, cmd, detail, render=True):
        E, _ = validate_goal(g)
        if E:
            raise MishuError(tr("Write refused — the changed data fails validation:") + "\n  - " + "\n  - ".join(E))
        target_dir = self.archive_dir if g.status in ("done", "dropped") else self.goals_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        new_path = target_dir / g.filename()
        new_path.write_text(g.dump(), "utf-8")
        if g.path and g.path.resolve() != new_path.resolve() and g.path.exists():
            g.path.unlink()
        g.path = new_path
        st = self.state()
        st["hashes"][g.gid] = sha(new_path)
        self.save_state(st)
        self.log_change(cmd, g.gid, detail)
        if render:
            render_board(self)

    def daily_path(self, d):
        return self.daily_dir / f"{d.isoformat()}.md"


def open_vault(args):
    p = resolve_vault_path(getattr(args, "vault", None))
    if not p:
        raise MishuError(tr("No vault configured. Run: mishu.py init --vault ~/MishuVault --set-default"), 4)
    return Vault(p)


# ═══════════════════════════════════════════════════════════════ metrics
def last_active(g: Goal):
    ds = [parse_date(lg.date)[0] for lg in g.logs if lg.result in ("✓", "◐", "=")]
    ds = [d for d in ds if d]
    return max(ds) if ds else None


def is_funnel_ref(ref, stage):
    return any(ref == p + stage for p in FUNNEL_PREFIXES)


def freq_count(g: Goal, t: dt.date):
    f = g.measure.get("frequency") or {}
    start = t - dt.timedelta(days=6)
    unit = f.get("unit")
    total = 0.0
    for lg in g.logs:
        d = parse_date(lg.date)[0]
        if not d or d < start or d > t:
            continue
        if f.get("task") and lg.ref == f["task"] and lg.result in ("✓", "◐"):
            q = re.search(rf"(\d+(?:\.\d+)?)\s*{re.escape(unit)}", lg.value) if unit else None
            total += float(q.group(1)) if q else (1.0 if lg.result == "✓" else 0.5)
        elif f.get("stage") and is_funnel_ref(lg.ref, f["stage"]):
            q = re.match(r"^\+(\d+)", lg.value or "")
            if q:
                total += int(q.group(1))
    return total


def compute_progress(g: Goal):
    kind = g.measure.get("progress")
    meas = g.measure
    rec = g.recurring_ids
    if kind == "phases" and g.phases:
        tw = acc = 0.0
        cur = None
        for p in g.phases:
            w = float(p.get("weight") or 1)
            tw += w
            if p.get("status") == "done":
                acc += w
            elif p.get("status") == "active":
                cur = cur or p
                ts = [x for x in g.tasks if x.phase == p["id"] and x.mark != "-" and x.tid not in rec]
                tot = sum(x.est or 30 for x in ts)
                dn = sum(x.est or 30 for x in ts if x.mark == "x")
                acc += w * (dn / tot if tot else 0)
        val = acc / tw if tw else 0.0
        if cur:
            detail = tr("{pid} {title} in progress", pid=cur["id"], title=cur.get("title"))
        elif all(p.get("status") == "done" for p in g.phases):
            detail = tr("All phases done")
        else:
            detail = tr("No phase in progress")
    elif kind == "metric":
        mt = meas.get("metric") or {}
        b, tg, c = mt.get("baseline"), mt.get("target"), mt.get("current")
        val = (c - b) / (tg - b) if isinstance(b, (int, float)) and tg != b else 0.0
        detail = tr("{c}{unit}, baseline {b} → target {t}", c=gnum(c), unit=mt.get("unit", ""), b=gnum(b), t=gnum(tg))
    elif kind == "units":
        u = meas.get("units") or {}
        tot = u.get("total") or 1
        val = (u.get("mastered") or 0) / tot
        detail = tr("Mastered {m}/{n} {name} · studied {d}", m=u.get("mastered", 0), n=tot,
                    name=u.get("name", tr("units")), d=u.get("done", 0))
    else:
        ts = [x for x in g.tasks if x.mark != "-" and x.tid not in rec]
        dn = sum(1 for x in ts if x.mark == "x")
        val = dn / len(ts) if ts else 0.0
        detail = tr("{d}/{n} items", d=dn, n=len(ts))
    if meas.get("funnel"):
        fs = [f"{s['stage']} {s.get('count', 0)}" + (f"/{s['target']}" if s.get("target") else "")
              for s in meas["funnel"]]
        detail += tr("; funnel: {f}", f=" → ".join(fs))
    return max(0.0, min(1.0, val)), detail


def _ratio_light(r):
    return "🟢" if r >= 0.9 else ("🟡" if r >= 0.7 else "🔴")


def compute_pace(g: Goal, prog, t):
    kind = g.measure.get("pace")
    start = parse_date(g.meta.get("start") or g.meta.get("created"))[0] or t
    dl, _ = parse_date(g.meta.get("deadline"))
    if kind == "frequency":
        f = g.measure.get("frequency") or {}
        per = float(f.get("per_week") or 1)
        c = freq_count(g, t)
        text = tr("Last 7 days {c}/{per} {unit}", c=f"{c:g}", per=f"{per:g}", unit=unit_label(f))
        days_in = (t - start).days + 1
        # Ramp-up: allow one day of slack so a brand-new habit doesn't go red before you had a chance.
        expect = per if days_in >= 7 else per * (days_in - 1) / 7
        if expect < 1 and c < per:
            return "🟢", None, text + tr(" (ramp-up)")
        ratio = c / expect
        return _ratio_light(ratio), ratio, text
    if kind == "deadline":
        if prog >= 1:
            return "🟢", None, tr("Done")
        if not dl:
            return "🟢", None, tr("No deadline")
        left = (dl - t).days
        if left < 0:
            return "🔴", None, tr("Overdue by {n} days", n=-left)
        if left <= 2:
            return "🔴", None, tr("{n} days to deadline", n=left)
        if left <= 7 and prog == 0:
            return "🟡", None, tr("{n} days to deadline, not started", n=left)
        return "🟢", None, tr("{n} days to deadline", n=left)
    if prog >= 1:
        return "🟢", None, tr("Achieved")
    if not dl:
        return "🟢", None, tr("No deadline")
    if t > dl:
        return "🔴", 0.0, tr("Past deadline {d}", d=dl.strftime("%m-%d"))
    total = max(1, (dl - start).days)
    exp = min(1.0, max(0.0, (t - start).days / total))
    if exp < 0.1:
        return "🟢", None, tr("Actual {p} / expected {e} (ramp-up)", p=f"{prog:.0%}", e=f"{exp:.0%}")
    ratio = prog / exp
    return _ratio_light(ratio), ratio, tr("Actual {p} / expected {e} (pace ratio {r})",
                                          p=f"{prog:.0%}", e=f"{exp:.0%}", r=f"{ratio:.2f}")


def next_task(g: Goal):
    rec = g.recurring_ids
    for mark in "/ ":
        for x in g.tasks:
            if x.mark == mark and x.tid not in rec:
                return x
    for x in g.tasks:
        if x.tid in rec and x.open:
            return x
    return None


def goal_metrics(g: Goal, t: dt.date, profile: Profile):
    limit = profile.stale_days
    prog, detail = compute_progress(g)
    start = parse_date(g.meta.get("start") or g.meta.get("created"))[0]
    res = {"gid": g.gid, "title": g.title, "type": g.type, "status": g.status, "priority": g.priority,
           "area": g.meta.get("area"), "progress": prog, "progress_detail": detail, "ratio": None,
           "pace_text": "", "risks": [], "task_risks": [], "stale_days": 0}
    if g.status != "active":
        res["light"] = STATUS_ICON.get(g.status, "⚪")
    elif start and start > t:
        res["light"], res["pace_text"] = "⚪", tr("starts {d}", d=start.strftime("%m-%d"))
    else:
        light, ratio, text = compute_pace(g, prog, t)
        res["light"], res["ratio"], res["pace_text"] = light, ratio, text
        ref = last_active(g) or start or t
        stale = (t - ref).days
        res["stale_days"] = stale
        if g.measure.get("pace") != "deadline" and prog < 1:
            if stale > 2 * limit:
                res["light"] = "🔴"
            elif stale > limit and res["light"] == "🟢":
                res["light"] = "🟡"
            if stale > limit:
                res["risks"].append(tr("{n} days without progress", n=stale))
    monday = t - dt.timedelta(days=t.weekday())
    wk = [lg for lg in g.logs if monday <= (parse_date(lg.date)[0] or dt.date.min) <= t]
    res["week_minutes"] = sum(minutes_in(lg.value) for lg in wk)
    res["week_done"] = sum(1 for lg in wk if lg.result == "✓")
    budget = parse_hours(g.meta.get("budget"))
    res["budget_h"] = budget
    if g.measure.get("pace") == "frequency":
        f = g.measure.get("frequency") or {}
        c = freq_count(g, t)
        res["week_short"] = f"{c:g}/{gnum(f.get('per_week'))} {unit_label(f)}"
        res["week_text"] = tr("Last 7 days {c}/{per} {unit} · spent {t}", c=f"{c:g}", per=gnum(f.get("per_week")),
                              unit=unit_label(f), t=fmt_hm(res["week_minutes"]))
    else:
        bh = f"{budget:g}h" if budget else "—"
        res["week_short"] = f"{res['week_minutes'] / 60:.1f}h/{bh}".replace(".0h", "h")
        res["week_text"] = tr("Spent {t} / budget {b} · {n} done", t=fmt_hm(res["week_minutes"]), b=bh,
                              n=res["week_done"])
    res["next"] = next_task(g)
    for x in g.tasks:
        if not (x.open or x.mark == "!"):
            continue
        if x.defer >= 2:
            res["task_risks"].append(tr("{t} deferred {n} times", t=x.tid, n=x.defer))
        due = parse_date(x.fields.get("due"))[0]
        if due and due < t and x.open:
            res["task_risks"].append(tr("{t} overdue ({d})", t=x.tid, d=due.strftime("%m-%d")))
        since = parse_date(x.fields.get("since"))[0]
        if x.mark == "!" and since and (t - since).days >= 3:
            res["task_risks"].append(tr("{t} waiting on {who} for {n} days", t=x.tid,
                                        who=x.fields.get("wait", tr("someone")), n=(t - since).days))
    for p in g.phases:
        pd = parse_date(p.get("due"))[0]
        if pd and pd < t and p.get("status") != "done" and g.status == "active":
            res["risks"].append(tr("{p} phase past due ({d})", p=p["id"], d=pd.strftime("%m-%d")))
    res["risks"] = res["task_risks"] + res["risks"]
    return res


# ═══════════════════════════════════════════════════════════════ rendering
def render_card(g: Goal, mt, level="###"):
    icon = TYPE_ICON.get(g.type, "")
    nt = mt["next"]
    if nt:
        nxt = f"{g.gid}.{nt.tid} {nt.title}" + (f" · {nt.est}m" if nt.est else "")
    elif mt["progress"] >= 1:
        nxt = "—" + paren(tr("all actions done; confirm whether the goal is complete"))
    else:
        nxt = "—" + paren(tr("no next action; break one down"))
    pace = f"{mt['light']} {mt['pace_text']}".strip()
    return "\n".join([
        f"{level} {icon} {g.gid} {g.title} · {g.priority} · {g.meta.get('area', '')}",
        f"- **{tr('Progress')}** {bar(mt['progress'])}{paren(mt['progress_detail'])}",
        f"- **{tr('Pace')}** {pace}",
        f"- **{tr('This week')}** {mt['week_text']}",
        f"- **{tr('Next')}** {nxt}",
        f"- **{tr('Risks')}** {sep().join(mt['risks']) if mt['risks'] else '—'}",
    ])


def weekly_focus(vault: Vault):
    files = sorted(vault.weekly_dir.glob("*.md")) if vault.weekly_dir.exists() else []
    if not files:
        return [paren(tr("no weekly review yet")).strip()]
    text = files[-1].read_text("utf-8")
    m = re.search(r"\*\*Top 3\*\*\s*\n((?:\s*\d+\..*\n?)+)", text)
    if not m:
        return [paren(tr("latest weekly review has no Top 3")).strip()]
    return [ln.strip() for ln in m.group(1).strip().splitlines()]


def none_line():
    return paren(tr("none")).strip()


def attention_items(active, prof):
    """Shared by the Markdown board and the HTML dashboard."""
    items = []
    counts = {k: sum(1 for _, m in active if m["light"] == k) for k in ("🟢", "🟡", "🔴")}
    if counts["🔴"] >= 3:
        items.append({"icon": "⛔", "cls": "crit", "gid": "", "title": "",
                      "text": tr("{n} goals are red at once — time for a load review (L4)", n=counts["🔴"])})
    budget_sum = sum(m["budget_h"] or 0 for _, m in active)
    if budget_sum > prof.capacity * 0.8:
        items.append({"icon": "⛔", "cls": "crit", "gid": "", "title": "",
                      "text": tr("Active budgets total {b}h, over 80% of your {c}h capacity",
                                 b=f"{budget_sum:g}", c=f"{prof.capacity:g}")})
    for g, m in active:
        if m["light"] in ("🔴", "🟡"):
            items.append({"icon": m["light"], "cls": LIGHT_CLASS[m["light"]][0], "gid": g.gid, "title": g.title,
                          "text": sep().join(x for x in [m["pace_text"]] + m["risks"] if x)})
        elif m["progress"] >= 1 and not m["next"]:
            items.append({"icon": "🎉", "cls": "done", "gid": g.gid, "title": g.title,
                          "text": tr("All actions done — confirm whether to close the goal")})
        elif m["task_risks"]:
            items.append({"icon": m["light"], "cls": "note", "gid": g.gid, "title": g.title,
                          "text": sep().join(m["task_risks"])})
    return items


def render_board(vault: Vault):
    t = today()
    prof = vault.profile
    goals = vault.goals()
    rows = [(g, goal_metrics(g, t, prof)) for g in goals]
    active = [(g, m) for g, m in rows if g.status == "active"]
    active.sort(key=lambda x: (LIGHT_ORDER.get(x[1]["light"], 9), -PRIORITY_W.get(x[0].priority, 0), x[0].gid))
    week_total = sum(m["week_minutes"] for _, m in rows)
    counts = {k: sum(1 for _, m in active if m["light"] == k) for k in ("🟢", "🟡", "🔴", "⚪")}
    paused = [(g, m) for g, m in rows if g.status in ("paused", "someday", "draft")]
    out = [
        "<!-- " + tr("Generated by mishu.py — do not edit by hand; changes will be overwritten") + " -->",
        "# 📊 " + tr("Mishu Board"),
        tr("Updated {d} {wd} · week {w} · this week {spent} / capacity {cap}h", d=t.isoformat(), wd=weekday_name(t),
           w=t.isocalendar()[1], spent=fmt_hm(week_total), cap=f"{prof.capacity:g}"),
        "",
        "　".join(f"{k} {v}" for k, v in counts.items() if v or k in ("🟢", "🟡", "🔴")) + f"　⏸ {len(paused)}",
        "",
        "## ⚠️ " + tr("Needs attention"),
    ]
    att = [f"- {a['icon']} " + (f"{a['gid']} {a['title']} — " if a["gid"] else "") + a["text"]
           for a in attention_items(active, prof)]
    out += att or [none_line()]
    if not goals:
        out += ["", "> " + tr("Your vault is empty. Tell Mishu about your first goals to get started.")]
    out += ["", "## 🎯 " + tr("Goals overview"),
            "| ID | " + " | ".join(tr(h) for h in ("Goal", "Type", "Progress", "Pace", "Due", "This week", "Next")) + " |",
            "|---|---|---|---|---|---|---|---|"]
    if not active:
        out.append("| — | " + paren(tr("no active goals")).strip() + " | | | | | | |")
    for g, m in active:
        d, hard = parse_date(g.meta.get("deadline"))
        dl = f"{d:%m-%d}{'!' if hard else ''}" if d else "—"
        nt = m["next"]
        out.append(f"| {g.gid} | {g.title} | {TYPE_ICON.get(g.type)} | {bar(m['progress'])} | {m['light']} | {dl} | "
                   f"{m['week_short']} | {nt.tid + ' ' + short(nt.title) if nt else '—'} |")
    out += ["", "## 🗂 " + tr("Goal cards")]
    out += ["\n\n".join(render_card(g, m) for g, m in active)] if active else [none_line()]
    out += ["", "## 🗓 " + tr("This week's focus (from weekly review)"), *weekly_focus(vault)]
    out += ["", "## ⏸ " + tr("Paused / 💭 Someday / 📝 Drafts")]
    if paused:
        for g, m in paused:
            last = g.decisions[-1] if g.decisions else None
            out.append(f"- {m['light']} {g.gid} {g.title}" + (f" — {last.text}{paren(last.did)}" if last else ""))
    else:
        out.append(none_line())
    (vault.root / "BOARD.md").write_text("\n".join(out) + "\n", "utf-8")
    render_html(vault)


# ═══════════════════════════════════════════════════════════════ HTML dashboard (read-only view)
def _expected_progress(g: Goal, t):
    if g.measure.get("pace") != "timeline":
        return None
    start = parse_date(g.meta.get("start") or g.meta.get("created"))[0]
    dl = parse_date(g.meta.get("deadline"))[0]
    if not start or not dl or dl <= start:
        return None
    return min(1.0, max(0.0, (t - start).days / (dl - start).days))


def _review_field(text, *labels):
    for label in labels:
        m = re.search(rf"\*\*{re.escape(label)}\*\* (.*)", text)
        if m:
            return m.group(1).strip()
    return ""


def parse_daily(path: Path):
    if not path.exists():
        return None
    text = path.read_text("utf-8")
    m = REVIEW_RE.search(text)
    plan_text, review_text = (text[:m.start()], text[m.start():]) if m else (text, "")
    lines = plan_text.splitlines()
    view = {"meta": lines[1].strip() if len(lines) > 1 else "", "sections": {"main": [], "habit": [], "errand": []},
            "waiting": [], "review": None}
    section = None
    for ln in lines:
        if ln.startswith("## "):
            section = next((key for icon, key in DAILY_SECTIONS.items() if ln[3:].startswith(icon)), None)
            continue
        mm = re.match(r"^- \[ \] (G\d+\.T\d+) (.+) · (\S+?)(（.*）| \(.*\))?$", ln)
        if mm and section in ("main", "habit", "errand"):
            view["sections"][section].append({"ref": mm.group(1), "title": mm.group(2), "time": mm.group(3),
                                              "note": (mm.group(4) or "").strip(" （）()")})
        elif section == "waiting" and ln.startswith("- "):
            view["waiting"].append(ln[2:])
    if review_text:
        results = {}
        for mm in re.finditer(r"^\| (G\d+\.T\d+) \| ([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|", review_text, re.M):
            results[mm.group(1)] = {"result": mm.group(2).strip(), "rtime": mm.group(3).strip(),
                                    "reason": mm.group(4).strip(), "evidence": mm.group(5).strip(),
                                    "rnote": mm.group(6).strip()}
        planned = set()
        for items in view["sections"].values():
            for it in items:
                planned.add(it["ref"])
                it.update(results.get(it["ref"], {}))
        extra = [{"ref": r, "title": "", "time": "", "note": "", **v} for r, v in results.items() if r not in planned]
        view["review"] = {"stats": _review_field(review_text, "Stats", "统计"),
                          "tomorrow": _review_field(review_text, "Tomorrow", "明日预排"),
                          "summary": _review_field(review_text, "In one line", "一句话"), "extra": extra}
    return view


def build_view(vault: Vault):
    t = today()
    prof = vault.profile
    goals = vault.goals()
    rows = [(g, goal_metrics(g, t, prof)) for g in goals]
    active = [(g, m) for g, m in rows if g.status == "active"]
    active.sort(key=lambda x: (LIGHT_ORDER.get(x[1]["light"], 9), -PRIORITY_W.get(x[0].priority, 0), x[0].gid))
    days = [t - dt.timedelta(days=i) for i in range(13, -1, -1)]
    gv = []
    for g, m in active:
        cls, label = LIGHT_CLASS.get(m["light"], ("idle", m["light"]))
        d, hard = parse_date(g.meta.get("deadline"))
        act = []
        for day in days:
            ls = [lg for lg in g.logs if lg.date == day.isoformat()]
            act.append({"date": day.strftime("%m-%d"), "minutes": sum(minutes_in(lg.value) for lg in ls),
                        "done": sum(1 for lg in ls if lg.result == "✓")})
        f = g.measure.get("frequency")
        nt = m["next"]
        gv.append({
            "gid": g.gid, "title": g.title, "type": g.type, "type_label": type_label(g.type),
            "priority": g.priority, "area": g.meta.get("area", ""), "cls": cls, "label": tr(label),
            "progress": m["progress"], "progress_detail": m["progress_detail"], "pace_text": m["pace_text"],
            "expected": _expected_progress(g, t), "deadline": d.strftime("%m-%d") if d else None, "hard": hard,
            "week_text": m["week_text"], "risks": m["risks"], "done_when": g.meta.get("done_when", ""),
            "next": {"ref": f"{g.gid}.{nt.tid}", "title": nt.title, "est": nt.est} if nt else None,
            "freq": {"count": freq_count(g, t), "per": f.get("per_week"), "unit": unit_label(f)} if f else None,
            "metric": g.measure.get("metric"), "funnel": g.measure.get("funnel"), "units": g.measure.get("units"),
            "phases": g.phases, "activity": act, "verify": g.verify,
            "tasks": [{"tid": x.tid, "mark": x.mark, "title": x.title, "est": x.est, "phase": x.phase,
                       "defer": x.defer, "wait": x.fields.get("wait"), "every": x.fields.get("every")}
                      for x in g.tasks],
            "logs": [{**vars(lg), "reason": lg.reason} for lg in reversed(g.logs[-10:])],
            "decisions": [vars(dc) for dc in reversed(g.decisions[-5:])],
        })
    counts = {k: sum(1 for _, m in active if m["light"] == k) for k in ("🟢", "🟡", "🔴")}
    others = [{"gid": g.gid, "title": g.title, "label": tr(LIGHT_CLASS.get(m["light"], ("", ""))[1]),
               "note": g.decisions[-1].text if g.decisions else ""}
              for g, m in rows if g.status in ("paused", "someday", "draft")]
    advice = []
    ap = vault.meta_dir / "advice.jsonl"
    if ap.exists():
        for line in ap.read_text("utf-8").splitlines():
            try:
                a = json.loads(line)
            except ValueError:
                continue
            if a.get("date") == t.isoformat():
                if re.fullmatch(r"G\d{2,}", str(a.get("goal", ""))):
                    ttl = next((g.title for g in goals if g.gid == a["goal"]), "")
                    a["goal_label"] = f"{a['goal']} {ttl}"
                a["category_label"] = tr(ADVICE_CATS.get(a.get("category"), a.get("category", "")))
                advice.append(a)
    inbox_p = vault.root / "inbox.md"
    inbox = [ln[6:] for ln in inbox_p.read_text("utf-8").splitlines() if ln.startswith("- [ ] ")] \
        if inbox_p.exists() else []
    return {
        "lang": cur_lang(), "name": prof.get("name") or "", "date": t.isoformat(), "weekday": weekday_name(t),
        "week": t.isocalendar()[1], "generated": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "capacity_h": prof.capacity, "week_minutes": sum(m["week_minutes"] for _, m in rows),
        "counts": {"ok": counts["🟢"], "warn": counts["🟡"], "crit": counts["🔴"]}, "active_n": len(active),
        "goal_n": len(goals), "checkin_time": prof.get("checkin_time"),
        "attention": attention_items(active, prof), "goals": gv, "others": others,
        "daily": parse_daily(vault.daily_path(t)), "advice": advice, "inbox": inbox,
        "activity_max": max([a["minutes"] for x in gv for a in x["activity"]] + [60]),
    }


def render_html(vault: Vault):
    import dashboard
    (vault.root / "dashboard.html").write_text(dashboard.render(build_view(vault), tr), "utf-8")


# ═══════════════════════════════════════════════════════════════ advice cards
def render_advice(a: dict, aid: str, vault: Vault):
    for k in ("category", "goal", "title", "level", "facts", "judgment", "ask"):
        if not a.get(k):
            raise MishuError(tr("Advice card is missing field {k}", k=k))
    a["category"] = ADVICE_ALIAS.get(a["category"], a["category"])
    if a["category"] not in ADVICE_CATS:
        raise MishuError(tr("Advice category must be one of {v}", v="/".join(ADVICE_CATS)))
    if a["level"] not in LEVELS:
        raise MishuError(tr("Advice level must be L0-L4"))
    opts = a.get("options") or []
    if len(opts) > 3:
        raise MishuError(tr("An advice card can have at most 3 options"))
    labels = []
    for o in opts:
        if not o.get("label") or not o.get("text") or not o.get("cost"):
            raise MishuError(tr("Every option needs label, text and cost"))
        labels.append(o["label"])
    if opts and a.get("recommend") not in labels:
        raise MishuError(tr("With options, recommend is required and must be one of the option labels"))
    if a["level"] in ("L2", "L3", "L4") and not opts:
        raise MishuError(tr("{lvl} advice needs a user decision, so it must include options", lvl=a["level"]))
    goal_label = a["goal"]
    if re.fullmatch(r"G\d{2,}", a["goal"]):
        try:
            goal_label = f"{a['goal']} {short(vault.load_goal(a['goal']).title, 18)}"
        except MishuError:
            pass
    cat = tr(ADVICE_CATS[a["category"]])
    lines = [f"> 💡 **{aid} [{cat}] {goal_label} · {clean(a['title'])}** · {a['level']}",
             f"> **{tr('Facts')}** {clean(a['facts'])}", f"> **{tr('Diagnosis')}** {clean(a['judgment'])}"]
    if opts:
        lines.append(f"> **{tr('Options')}**")
        lines += [f"> {o['label']}. {clean(o['text'])} — {tr('Cost:')} {clean(o['cost'])}" for o in opts]
        rr = paren(clean(a["recommend_reason"])) if a.get("recommend_reason") else ""
        lines.append(f"> **{tr('Recommended')}** {a['recommend']}{rr}")
    lines.append(f"> **{tr('Your call')}** {clean(a['ask'])}")
    return "\n".join(lines)


def issue_advice(vault: Vault, items, limit=None):
    if isinstance(items, dict):
        items = [items]
    if limit is not None and len(items) > limit:
        raise MishuError(tr("At most {n} advice cards here (keep the highest levels)", n=limit))
    t = today()
    st = vault.state()
    key = t.strftime("%m%d")
    cards = []
    vault.meta_dir.mkdir(parents=True, exist_ok=True)
    for a in items:
        n = st["advice"].get(key, 0) + 1
        aid = f"A{key}-{n}"
        cards.append(render_advice(a, aid, vault))
        st["advice"][key] = n
        with open(vault.meta_dir / "advice.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": aid, "date": t.isoformat(), **a}, ensure_ascii=False) + "\n")
    vault.save_state(st)
    return cards


def load_advice_file(path):
    if not path:
        return []
    data = json.loads(read_stdin_or_file(path))
    return data if isinstance(data, list) else [data]


# ═══════════════════════════════════════════════════════════════ core write path
def apply_result(vault, g: Goal, t_ref, result, time=None, evidence="", note="", reason=None,
                 qty=None, date=None, confirmed=False):
    """Write one execution result back to a goal: update the action + append a log line."""
    result = RESULT_ALIAS.get(result, result)
    if result not in RESULTS or result == "=":
        raise MishuError(tr("Result must be ✓/◐/✗/➜/✂ (or done/partial/skip/moved/cancel)"))
    evidence = EVIDENCE_ALIAS.get(evidence, evidence) if evidence else ""
    if evidence and evidence not in EVIDENCE:
        raise MishuError(tr("Evidence must be 🔍/📷/🔗/💬 (or code/photo/link/verbal)"))
    if result in ("✓", "◐") and not evidence:
        raise MishuError(tr("Done/partial requires --evidence (use verbal if the user gives no evidence)"))
    if result in ("◐", "✗", "➜") and not reason:
        raise MishuError(tr("Partial/not done/moved requires a reason code --reason (T/E/U/A/B/O/P)"))
    if reason and reason not in REASONS:
        raise MishuError(tr("Reason code must be one of {v}", v="/".join(REASONS)))
    if result == "✂" and not confirmed:
        raise MishuError(tr("Cancelling an action is a structural change: needs the user's explicit OK and --confirmed"))
    task = g.task(t_ref)
    rec = task.tid in g.recurring_ids
    ref = f"{g.gid}.{task.tid}"
    if result == "✓":
        if not rec:
            task.mark = "x"
        summary = tr("{ref} logged once", ref=ref) if rec else tr("{ref} → done", ref=ref)
    elif result == "◐":
        if not rec:
            task.mark = "/"
        summary = tr("{ref} partially done", ref=ref) if rec else tr("{ref} → in progress", ref=ref)
    elif result in ("✗", "➜"):
        if rec:
            summary = tr("{ref} skipped this time (habits don't accumulate deferrals)", ref=ref)
        else:
            task.fields["defer"] = str(task.defer + 1)
            summary = tr("{ref} deferred +1 ({n} total)", ref=ref, n=task.defer)
            if task.defer >= 3:
                summary += tr(" ⚠️ reached 3 — no longer scheduled; break it down or rethink it")
    else:
        task.mark = "-"
        summary = tr("{ref} → cancelled", ref=ref)
    unit = (g.measure.get("frequency") or {}).get("unit", "")
    value = "/".join(x for x in [f"{gnum(qty)}{unit}" if qty else "", fmt_hm(parse_minutes(time)) if time else ""] if x)
    full_note = (f"[{reason}] " if reason else "") + (note or "")
    g.logs.append(Log((date or today()).isoformat(), task.tid, result, value, evidence, full_note.strip()))
    hints = []
    v = g.verify
    if result in ("✓", "◐") and v.get("method") == "repo" and v.get("when") in ("every", None) and evidence != "🔍":
        hints.append(tr("ℹ️ {gid} requires a code check (verify=repo); this entry's evidence is {e}. "
                        "Make sure it was checked, or the user explicitly chose to skip.", gid=g.gid, e=evidence))
    if result == "✓" and task.phase and not rec:
        rest = [x for x in g.tasks if x.phase == task.phase and x.mark in " /!" and x.tid not in g.recurring_ids]
        try:
            if not rest and g.phase(task.phase).get("status") == "active":
                hints.append(tr("ℹ️ All actions in phase {p} are done. After verifying, run: phase done {gid}.{p}",
                                p=task.phase, gid=g.gid))
        except MishuError:
            pass
    if g.status == "active" and not any(x.open for x in g.tasks):
        if compute_progress(g)[0] >= 1:
            hints.append(tr("🎉 All actions of {gid} are done. Ask the user whether “{dw}” is met; if so run: "
                            "set {gid} status done --confirmed --reason ...", gid=g.gid, dw=g.meta.get("done_when")))
        else:
            hints.append(tr("⚠️ {gid} has no open next action. Break new actions down with the user (task add).",
                            gid=g.gid))
    return summary, hints


# ═══════════════════════════════════════════════════════════════ commands: setup & profile
def write_vault_readme(root):
    (root / "README.md").write_text(tr(
        "# Mishu vault\n\nThis folder is managed by the Mishu skill. Data is written only through `mishu.py`.\n"
        "Read anything you like; if you edit a goal file by hand it is re-validated before the next write.\n"
        "`BOARD.md` and `dashboard.html` are generated — don't edit them.\n"), "utf-8")


def cmd_init(args):
    root = Path(args.vault).expanduser().resolve()
    set_lang(args.lang)
    if (root / "profile.md").exists():
        print(tr("Vault already exists: {root}", root=root))
    else:
        if root.exists() and any(root.iterdir()):
            raise MishuError(tr("{root} exists and is not empty; pick an empty folder", root=root))
        for sub in ("goals/_archive", "daily", "weekly", "evidence", ".mishu"):
            (root / sub).mkdir(parents=True, exist_ok=True)
        meta = dict(Profile.DEFAULTS)
        meta["lang"] = args.lang
        meta["areas"] = DEFAULT_AREAS[args.lang]
        meta.update({k: v for k, v in {
            "name": args.name, "weekly_capacity": args.capacity, "daily_default": args.daily,
            "weekend_default": args.weekend, "wip_limit": args.wip, "stale_days": args.stale, "tone": args.tone,
        }.items() if v is not None})
        for k in ("weekly_capacity", "daily_default", "weekend_default"):
            parse_hours(meta[k])
        body = "## " + tr("Background") + "\n" + paren(tr("routine, common distractions, preferences — filled in during setup")).strip() + "\n"
        (root / "profile.md").write_text("\n".join(["---", *yaml_dump(meta), "---", ""]) + body, "utf-8")
        (root / "inbox.md").write_text("# 📥 " + tr("Inbox") + "\n", "utf-8")
        write_vault_readme(root)
        v = Vault(root)
        v.save_state(v.state())
        v.log_change("init", "vault", "vault created")
        render_board(v)
        print(tr("✅ Vault created: {root}", root=root))
    if args.set_default:
        cp = config_path()
        cp.parent.mkdir(parents=True, exist_ok=True)
        cfg = json.loads(cp.read_text("utf-8")) if cp.exists() else {}
        cfg["vault"] = str(root)
        cp.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), "utf-8")
        print(tr("✅ Set as default vault ({cp})", cp=cp))


def cmd_profile(args):
    v = open_vault(args)
    p = v.profile
    if args.action == "show":
        print(p.dump())
        return
    if not args.confirmed:
        raise MishuError(tr("Changing the profile needs the user's explicit OK; add --confirmed after they agree"), 3)
    if args.action == "set":
        if args.key not in PROFILE_FIELDS:
            raise MishuError(tr("Editable fields: {v}", v=", ".join(PROFILE_FIELDS)))
        val = _value(args.value) if args.key in ("wip_limit", "stale_days", "areas") else args.value
        if args.key in ("weekly_capacity", "daily_default", "weekend_default"):
            parse_hours(val)
        if args.key == "lang" and val not in LANGS:
            raise MishuError(tr("lang must be en or zh"))
        old = p.meta.get(args.key)
        p.meta[args.key] = val
        detail = f"{args.key}: {old} → {val}; reason: {args.reason or '—'}"
    else:
        text = read_stdin_or_file(args.file).strip()
        p.body = "## " + tr("Background") + "\n" + text + "\n"
        detail = "background updated"
    p.path.write_text(p.dump(), "utf-8")
    v.log_change("profile", "profile", detail)
    if args.action == "set" and args.key == "lang":
        set_lang(val)
    render_board(v)
    print(tr("✅ Profile updated: {d}", d=detail))


def cmd_context(args):
    t = today()
    p = resolve_vault_path(getattr(args, "vault", None))
    if not p or not (p / "profile.md").exists():
        print(f"📆 Today: {t.isoformat()} {WD_EN[t.weekday()]} (week {t.isocalendar()[1]})")
        print("📁 Vault: NOT CONFIGURED → first run. Follow workflows/setup.md "
              "(create an empty vault, then onboard the user's first goals).")
        return
    v = Vault(p)
    prof = v.profile
    print(tr("📆 Today: {d} {wd} (week {w})", d=t.isoformat(), wd=weekday_name(t), w=t.isocalendar()[1]))
    print(tr("📁 Vault: {p} · language {lang}", p=p, lang=cur_lang()))
    print(tr("👤 {name} · capacity {cap}h/week · WIP limit {wip} · tone {tone} · check-in {ci}",
             name=prof.get("name") or tr("user"), cap=f"{prof.capacity:g}", wip=prof.get("wip_limit"),
             tone=prof.get("tone"), ci=prof.get("checkin_time")))
    dp = v.daily_path(t)
    if not dp.exists():
        state = tr("not planned yet")
    elif REVIEW_RE.search(dp.read_text("utf-8")):
        state = tr("check-in done")
    else:
        state = tr("planned, check-in pending")
    print(tr("📅 Today's plan: {s}", s=state))
    errors = 0
    rows = []
    for path in v.goal_paths():
        try:
            g = Goal.load(path)
            E, _ = validate_goal(g)
            errors += len(E)
            rows.append((g, goal_metrics(g, t, prof)))
        except MishuError:
            errors += 1
    active = [(g, m) for g, m in rows if g.status == "active"]
    cnt = {k: sum(1 for _, m in active if m["light"] == k) for k in ("🟢", "🟡", "🔴")}
    print(tr("🎯 Active goals: {n} · 🟢{ok} 🟡{warn} 🔴{crit}", n=len(active), ok=cnt["🟢"], warn=cnt["🟡"], crit=cnt["🔴"]))
    for g, m in sorted(active, key=lambda x: LIGHT_ORDER.get(x[1]["light"], 9)):
        print(f"   {m['light']} {g.gid} {TYPE_ICON.get(g.type)} {g.title} · {m['progress']:.0%} · {m['pace_text']}")
    inbox = (p / "inbox.md").read_text("utf-8") if (p / "inbox.md").exists() else ""
    pending = len(re.findall(r"^- \[ \]", inbox, re.M))
    print(tr("📥 Inbox: {n} pending", n=pending))
    if not v.goal_paths(archive=True):
        print(tr("🆕 The vault is empty → onboard the first batch of goals (workflows/setup.md, step 4)."))
    print(tr("✅ Data valid") if errors == 0 else tr("✗ {n} validation problems → run validate first", n=errors))


def cmd_validate(args):
    v = open_vault(args)
    total_e = 0
    for path in v.goal_paths(archive=True):
        try:
            g = Goal.load(path)
            E, W = validate_goal(g)
        except MishuError as e:
            E, W = [str(e)], []
        total_e += len(E)
        if E or W:
            print(path.name)
            for e in E:
                print(f"  ✗ {e}")
            for w in W:
                print(f"  ⚠ {w}")
    st = v.state()
    for path in v.goal_paths(archive=True):
        gid = path.name.split("-")[0]
        if gid in st["hashes"] and st["hashes"][gid] != sha(path):
            print("  ⚠ " + tr("{gid} was edited outside mishu.py (it will be re-validated on the next write)", gid=gid))
    if total_e:
        print(tr("✗ {n} errors", n=total_e))
        sys.exit(1)
    print(tr("✅ Validation passed"))


# ═══════════════════════════════════════════════════════════════ commands: goals
def build_goal_from_json(data: dict, gid: str):
    for k in ("title", "type", "area", "priority"):
        if not data.get(k):
            raise MishuError(tr("Goal draft is missing {k}", k=k))
    gtype = data["type"]
    if gtype not in TYPE_ICON:
        raise MishuError(tr("type must be one of {v}", v="/".join(TYPE_ICON)))
    t = today()
    prog, pace = TYPE_DEFAULTS[gtype]
    measure = {"progress": prog, "pace": pace}
    measure.update(data.get("measure") or {})
    verify = dict(DEFAULT_VERIFY[gtype])
    if (data.get("verify") or {}).get("repo") and not (data.get("verify") or {}).get("method"):
        verify.update({"method": "repo", "when": "every"})
    verify.update(data.get("verify") or {})
    verify = {k: verify[k] for k in ("method", "repo", "when", "fallback") if verify.get(k)}
    meta = {"id": gid, "title": data["title"], "type": gtype, "area": data["area"], "priority": data["priority"],
            "status": data.get("status", "active"), "created": t.isoformat(),
            "start": norm_date(data.get("start")) or t.isoformat()}
    if data.get("deadline"):
        meta["deadline"] = norm_date(data["deadline"])
    for k in ("why", "done_when", "budget"):
        if data.get(k):
            meta[k] = data[k]
    meta["review"] = data.get("review", "weekly")
    meta["verify"] = verify
    meta["measure"] = measure
    phases = []
    for i, p in enumerate(data.get("phases") or [], 1):
        ph = {"id": f"M{i}", "title": p["title"], "weight": p.get("weight", 1)}
        if p.get("due"):
            ph["due"] = norm_date(p["due"], allow_hard=False)
        ph["status"] = p.get("status") or ("active" if i == 1 else "todo")
        phases.append(ph)
    if phases:
        meta["phases"] = phases
    g = Goal(None, meta)
    for i, tk in enumerate(data.get("tasks") or [], 1):
        task = Task(f"T{i:02d}", " ", tk["title"], parse_minutes(tk.get("est")), tk.get("phase"))
        for k in ("due", "every", "qty", "min"):
            if tk.get(k):
                task.fields[k] = norm_date(tk[k], allow_hard=False) if k == "due" else str(tk[k])
        g.tasks.append(task)
    ftask = (measure.get("frequency") or {}).get("task")
    if isinstance(ftask, int):
        measure["frequency"]["task"] = f"T{ftask:02d}"
    g.logs.append(Log(t.isoformat(), tr("created"), "=", "", "⚙️", tr("goal created ({s})", s=meta["status"])))
    return g


def capacity_problems(vault: Vault, candidate: Goal = None, exclude=None):
    prof = vault.profile
    active = [g for g in vault.goals() if g.status == "active" and g.gid != exclude]
    if candidate:
        active.append(candidate)
    budget = sum(parse_hours(g.meta.get("budget")) or 0 for g in active)
    wip = sum(0.5 if g.type == "habit" else 1 for g in active)
    cap, limit = prof.capacity, float(prof.get("wip_limit"))
    P = []
    if budget > cap * 0.8:
        P.append(tr("Budgets total {b}h/week > capacity {c}h × 0.8 = {x}h", b=f"{budget:g}", c=f"{cap:g}",
                    x=f"{cap * 0.8:g}"))
    if wip > limit:
        P.append(tr("Active goals {w} (habits count 0.5) > WIP limit {l}", w=f"{wip:g}", l=f"{limit:g}"))
    return P, budget, wip


def cmd_add_goal(args):
    v = open_vault(args)
    data = json.loads(read_stdin_or_file(args.file))
    gid = v.next_goal_id()
    g = build_goal_from_json(data, gid)
    E, W = validate_goal(g, strict_ready=(g.status == "active"))
    cp, budget, wip = capacity_problems(v, g) if g.status == "active" else ([], 0, 0)
    mt = goal_metrics(g, today(), v.profile)
    print("—— " + tr("Goal card preview") + " ——")
    print(render_card(g, mt))
    print("\n" + tr("Type {t} · progress {p} · pace {pace} · evidence {m} ({w}, fallback {f})",
                    t=type_label(g.type), p=g.measure["progress"], pace=g.measure["pace"],
                    m=g.verify.get("method"), w=g.verify.get("when"), f=g.verify.get("fallback")))
    print(tr("Phases: {v}", v=("、" if cur_lang() == "zh" else ", ").join(p["id"] + " " + p["title"] for p in g.phases) or "—"))
    print(tr("Actions:") + "\n" + "\n".join("  " + t.dump()[2:] for t in g.tasks))
    for w in W:
        print(f"⚠ {w}")
    if E:
        print("\n" + tr("✗ Definition of Ready not met:") + "\n  - " + "\n  - ".join(E))
        sys.exit(2)
    if cp:
        print("\n" + tr("⛔ Capacity gate failed:") + "\n  - " + "\n  - ".join(cp))
        print(tr("The user must choose: lower another goal's budget / pause a goal / save this goal as someday"))
        sys.exit(3)
    if g.status == "active":
        print("\n" + tr("✅ Ready · capacity: budget {b}h/{c}h · WIP {w}/{l}", b=f"{budget:g}",
                        c=f"{v.profile.capacity:g}", w=f"{wip:g}", l=v.profile.get("wip_limit")))
    if args.dry_run:
        print("\n" + tr("(Preview only — nothing written. Re-run without --dry-run after the user confirms.)"))
        return
    v.goals_dir.mkdir(parents=True, exist_ok=True)
    v.save_goal(g, "add-goal", f"created {g.title} ({g.status})")
    if args.inbox:
        _inbox_mark(v, args.inbox, gid)
    print("\n" + tr("✅ Created {gid}: {path} — board updated", gid=gid, path=g.path.relative_to(v.root)))


def cmd_set(args):
    v = open_vault(args)
    if not args.confirmed:
        raise MishuError(tr("This is a structural change: explain it to the user, get an explicit OK, then add --confirmed"), 3)
    if not args.reason:
        raise MishuError(tr("Structural changes require --reason"))
    g = v.load_goal(args.gid, for_write=True)
    field, raw = args.field, args.value
    if field not in SET_FIELDS:
        raise MishuError(tr("Editable fields: {v} (type and measure kinds can't change — create a new goal)",
                            v=", ".join(SET_FIELDS)))
    old_status = g.status
    if field in ("start", "deadline"):
        val = norm_date(raw, allow_hard=(field == "deadline"))
    elif field == "priority":
        if raw not in PRIORITY_W:
            raise MishuError(tr("priority must be P0-P3"))
        val = raw
    elif field == "status":
        if raw not in STATUSES:
            raise MishuError(tr("status must be one of {v}", v="/".join(STATUSES)))
        val = raw
    elif field == "budget":
        parse_hours(raw)
        val = raw
    elif field.startswith("measure.") and field != "measure.funnel.target":
        val = num(raw, field)
    else:
        val = raw
    if field == "measure.funnel.target":
        funnel = g.measure.get("funnel") or []
        if not funnel:
            raise MishuError(tr("This goal has no funnel"))
        old = funnel[-1].get("target")
        val = int(num(raw))
        funnel[-1]["target"] = val
    elif "." in field:
        parts = field.split(".")
        node = g.meta
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        old = node.get(parts[-1])
        node[parts[-1]] = val
    else:
        old = g.meta.get(field)
        g.meta[field] = val
    if field == "status" and val == "active" and old_status != "active":
        cp, _, _ = capacity_problems(v, g, exclude=g.gid)
        if cp:
            raise MishuError(tr("Capacity gate failed; cannot activate:") + "\n  - " + "\n  - ".join(cp), 3)
    did = g.next_decision_id()
    g.decisions.append(Decision(today().isoformat(), did, tr("changed {f}: {o} → {n}", f=field, o=old, n=val),
                                args.reason, norm_date(args.revisit) if args.revisit else "", args.advice or ""))
    g.logs.append(Log(today().isoformat(), did, "=", "", "⚙️", f"{field} → {val}"))
    v.save_goal(g, "set", f"{field}: {old} → {val}; reason: {args.reason}")
    print(tr("✅ {gid} {f}: {o} → {n} (decision {gid}.{d} recorded)", gid=g.gid, f=field, o=old, n=val, d=did))


def cmd_decide(args):
    v = open_vault(args)
    g = v.load_goal(args.gid, for_write=True)
    did = g.next_decision_id()
    g.decisions.append(Decision(today().isoformat(), did, args.text, args.reason or "",
                                norm_date(args.revisit) if args.revisit else "", args.advice or ""))
    v.save_goal(g, "decide", f"{did} {args.text}")
    print(tr("✅ Decision {gid}.{d} recorded", gid=g.gid, d=did))


def cmd_phase(args):
    v = open_vault(args)
    if args.action == "add":
        if not args.confirmed or not args.reason:
            raise MishuError(tr("Adding a phase is structural: needs --confirmed and --reason"), 3)
        if not args.title:
            raise MishuError(tr("phase add needs --title"))
        g = v.load_goal(args.target, for_write=True)
        n = max([int(p["id"][1:]) for p in g.phases] + [0]) + 1
        ph = {"id": f"M{n}", "title": args.title, "weight": num(args.weight or 1)}
        if args.due:
            ph["due"] = norm_date(args.due, allow_hard=False)
        ph["status"] = "todo"
        g.meta.setdefault("phases", []).append(ph)
        did = g.next_decision_id()
        g.decisions.append(Decision(today().isoformat(), did, tr("added phase M{n} {t}", n=n, t=args.title), args.reason))
        v.save_goal(g, "phase-add", f"M{n} {args.title}")
        print(tr("✅ Added phase {gid}.M{n}", gid=g.gid, n=n))
        return
    m = re.fullmatch(r"(G\d{2,})\.(M\d+)", args.target.upper())
    if not m:
        raise MishuError(tr("Format must be G01.M2"))
    g = v.load_goal(m.group(1), for_write=True)
    ph = g.phase(m.group(2))
    ev = EVIDENCE_ALIAS.get(args.evidence, args.evidence) if args.evidence else ""
    if args.action == "done":
        if ev not in EVIDENCE:
            raise MishuError(tr("Completing a phase requires --evidence (code/photo/link/verbal)"))
        rest = [x for x in g.tasks if x.phase == ph["id"] and x.mark in " /!" and x.tid not in g.recurring_ids]
        if rest and not args.confirmed:
            raise MishuError(tr("Phase {p} still has open actions: {v}. If the user still wants to close it, add --confirmed",
                                p=ph["id"], v=", ".join(x.tid for x in rest)), 3)
        ph["status"] = "done"
        nxt = next((p for p in g.phases if p.get("status") == "todo"), None)
        msg = tr("{gid}.{p} → done", gid=g.gid, p=ph["id"])
        if nxt and not any(p.get("status") == "active" for p in g.phases):
            nxt["status"] = "active"
            msg += tr("; {p} {t} → in progress", p=nxt["id"], t=nxt["title"])
        g.logs.append(Log(today().isoformat(), ph["id"], "✓", "", ev, clean(args.note or tr("phase completed"))))
    else:
        ph["status"] = "active"
        msg = tr("{gid}.{p} → in progress", gid=g.gid, p=ph["id"])
        g.logs.append(Log(today().isoformat(), ph["id"], "=", "", "⚙️", tr("phase started")))
    v.save_goal(g, "phase", msg)
    print("✅ " + msg)


# ═══════════════════════════════════════════════════════════════ commands: actions & progress
def split_ref(ref):
    m = re.fullmatch(r"(G\d{2,})\.(T\d+)", ref.strip().upper())
    if not m:
        raise MishuError(tr("Item reference must look like G01.T05: {r}", r=ref))
    return m.group(1), m.group(2)


def cmd_task(args):
    v = open_vault(args)
    if args.action == "add":
        g = v.load_goal(args.target, for_write=True)
        est = parse_minutes(args.est)
        if est is None:
            raise MishuError(tr("New actions need an --est estimate"))
        if est > 120:
            raise MishuError(tr("A single action can't exceed 2h — split it into several"))
        if args.phase:
            g.phase(args.phase)
        t = Task(g.next_task_id(), " ", args.title, est, args.phase)
        if args.due:
            t.fields["due"] = norm_date(args.due, allow_hard=False)
        for k in ("every", "qty", "min"):
            if getattr(args, k):
                t.fields[k] = getattr(args, k)
        g.tasks.append(t)
        v.save_goal(g, "task-add", t.dump())
        print(tr("✅ Added {gid}.{t}: {line}", gid=g.gid, t=t.tid, line=t.dump()[2:]))
        return
    gid, tid = split_ref(args.target)
    g = v.load_goal(gid, for_write=True)
    t = g.task(tid)
    if args.action == "set":
        st = args.status
        if st not in ("todo", "doing", "blocked", "cancel"):
            raise MishuError(tr("task set only accepts todo/doing/blocked/cancel; record completion with log or checkin (needs evidence)"))
        if st == "cancel":
            if not args.confirmed or not args.reason:
                raise MishuError(tr("Cancelling needs the user's OK: add --confirmed and --reason"), 3)
            did = g.next_decision_id()
            g.decisions.append(Decision(today().isoformat(), did, tr("cancelled action {t} {title}", t=tid, title=t.title),
                                        args.reason))
        if st == "blocked":
            t.fields["wait"] = args.wait or tr("someone")
            t.fields["since"] = today().isoformat()
        elif t.mark == "!":
            t.fields.pop("wait", None)
            t.fields.pop("since", None)
        t.mark = MARK_OF[st]
        v.save_goal(g, "task-set", f"{tid} → {st}")
        print(f"✅ {gid}.{tid} → {st}")
    else:
        if not args.reason:
            raise MishuError(tr("Editing an action requires --reason (e.g. re-estimated after breakdown)"))
        changes = []
        if args.title:
            changes.append(tr("title → {v}", v=args.title))
            t.title = args.title
        if args.est:
            e = parse_minutes(args.est)
            if e > 120:
                raise MishuError(tr("A single action can't exceed 2h — split it into several"))
            changes.append(tr("estimate {a}m → {b}m", a=t.est, b=e))
            t.est = e
        if args.phase:
            g.phase(args.phase)
            changes.append(tr("phase → {v}", v=args.phase))
            t.phase = args.phase
        if args.due:
            t.fields["due"] = norm_date(args.due, allow_hard=False)
            changes.append(tr("due → {v}", v=t.fields["due"]))
        if args.min:
            t.fields["min"] = args.min
            changes.append(tr("minimum version → {v}", v=args.min))
        if args.reset_defer:
            t.fields.pop("defer", None)
            changes.append(tr("deferral count reset"))
        if not changes:
            raise MishuError(tr("Nothing to change"))
        v.save_goal(g, "task-edit", f"{tid}: {'; '.join(changes)}; reason: {args.reason}")
        print(f"✅ {gid}.{tid}: {sep().join(changes)}")


def cmd_log(args):
    v = open_vault(args)
    gid, tid = split_ref(args.target)
    g = v.load_goal(gid, for_write=True)
    date = parse_date(args.date)[0] if args.date else None
    summary, hints = apply_result(v, g, tid, args.result, args.time, args.evidence or "", args.note or "",
                                  args.reason, args.qty, date, args.confirmed)
    v.save_goal(g, "log", summary)
    print("✅ " + summary)
    for h in hints:
        print(h)


def _evidence_arg(ev):
    ev = EVIDENCE_ALIAS.get(ev, ev)
    if ev not in EVIDENCE:
        raise MishuError(tr("--evidence is required (code/photo/link/verbal)"))
    return ev


def cmd_metric(args):
    v = open_vault(args)
    g = v.load_goal(args.gid, for_write=True)
    mt = g.measure.get("metric")
    if not mt:
        raise MishuError(tr("{gid} has no metric (measure.metric)", gid=g.gid))
    ev = _evidence_arg(args.evidence)
    old = mt.get("current")
    mt["current"] = num(args.value)
    g.logs.append(Log((parse_date(args.date)[0] if args.date else today()).isoformat(), mt["name"], "=",
                      f"{gnum(mt['current'])}{mt.get('unit', '')}", ev, args.note or ""))
    v.save_goal(g, "metric", f"{mt['name']} {old} → {mt['current']}")
    prog, _ = compute_progress(g)
    print(tr("✅ {gid} {name}: {o} → {n}{unit} (progress {p})", gid=g.gid, name=mt["name"], o=gnum(old),
             n=gnum(mt["current"]), unit=mt.get("unit", ""), p=f"{prog:.0%}"))
    if g.verify.get("method") == "photo" and ev != "📷":
        print(tr("ℹ️ This goal normally uses photo evidence; this entry isn't a photo. If the user chose verbal, "
                 "that's fine — don't ask again."))


def cmd_funnel(args):
    v = open_vault(args)
    g = v.load_goal(args.gid, for_write=True)
    funnel = g.measure.get("funnel") or []
    st = next((s for s in funnel if s.get("stage") == args.stage), None)
    if not st:
        raise MishuError(tr("Unknown funnel stage: {s} (options: {v})", s=args.stage,
                            v=", ".join(s["stage"] for s in funnel)))
    ev = _evidence_arg(args.evidence)
    m = re.fullmatch(r"([+=])(\d+)", args.change)
    if not m:
        raise MishuError(tr("Change must look like +3 (add) or =5 (set)"))
    old = st.get("count", 0)
    st["count"] = old + int(m.group(2)) if m.group(1) == "+" else int(m.group(2))
    delta = st["count"] - old
    prefix = FUNNEL_PREFIXES[1] if _LANG == "zh" else FUNNEL_PREFIXES[0]
    g.logs.append(Log(today().isoformat(), prefix + args.stage, "=", f"{'+' if delta >= 0 else ''}{delta}",
                      ev, args.note or ""))
    v.save_goal(g, "funnel", f"{args.stage} {old} → {st['count']}")
    print(tr("✅ {gid} funnel “{s}”: {o} → {n}", gid=g.gid, s=args.stage, o=old, n=st["count"]))


def cmd_units(args):
    v = open_vault(args)
    g = v.load_goal(args.gid, for_write=True)
    u = g.measure.get("units")
    if not u:
        raise MishuError(tr("{gid} has no learning units (measure.units)", gid=g.gid))
    ev = _evidence_arg(args.evidence)
    old = (u.get("done"), u.get("mastered"))
    if args.done is not None:
        u["done"] = args.done
    if args.mastered is not None:
        u["mastered"] = args.mastered
    if u.get("mastered", 0) > u.get("done", 0) or u.get("done", 0) > u["total"]:
        raise MishuError(tr("Must satisfy mastered ≤ done ≤ total"))
    g.logs.append(Log(today().isoformat(), u.get("name", tr("units")), "=",
                      tr("studied {d}/mastered {m}", d=u.get("done"), m=u.get("mastered")), ev, args.note or ""))
    v.save_goal(g, "units", f"done/mastered {old} → {(u.get('done'), u.get('mastered'))}")
    print(tr("✅ {gid} {name}: studied {d} · mastered {m}/{n}", gid=g.gid, name=u.get("name", tr("units")),
             d=u.get("done"), m=u.get("mastered"), n=u["total"]))


def cmd_evidence(args):
    v = open_vault(args)
    g = v.load_goal(args.gid)
    src = Path(args.path).expanduser()
    if not src.is_file():
        raise MishuError(tr("File not found: {p}", p=src))
    v.evidence_dir.mkdir(parents=True, exist_ok=True)
    base = f"{today().isoformat()}-{g.gid}"
    n = len(list(v.evidence_dir.glob(base + "-*"))) + 1
    dst = v.evidence_dir / f"{base}-{n}{src.suffix.lower()}"
    shutil.copy2(src, dst)
    v.log_change("evidence", g.gid, dst.name)
    print(tr("✅ Evidence saved: evidence/{f} (put the filename in --note when logging)", f=dst.name))


# ═══════════════════════════════════════════════════════════════ commands: inbox
def _inbox_mark(v: Vault, n, gid=None):
    p = v.root / "inbox.md"
    lines = p.read_text("utf-8").splitlines()
    idx = [i for i, ln in enumerate(lines) if ln.startswith("- [ ] ")]
    if n < 1 or n > len(idx):
        raise MishuError(tr("Inbox has no pending item #{n}", n=n))
    i = idx[n - 1]
    lines[i] = "- [x] " + lines[i][6:] + (f" → {gid}" if gid else "")
    p.write_text("\n".join(lines) + "\n", "utf-8")
    v.log_change("inbox-done", "inbox", lines[i])


def cmd_inbox(args):
    v = open_vault(args)
    p = v.root / "inbox.md"
    if args.action == "add":
        with open(p, "a", encoding="utf-8") as f:
            f.write(f"- [ ] {today().isoformat()} {clean(args.text)}\n")
        v.log_change("inbox-add", "inbox", args.text)
        print(tr("✅ Added to inbox: {t}", t=args.text))
    elif args.action == "list":
        items = [ln for ln in p.read_text("utf-8").splitlines() if ln.startswith("- [ ] ")]
        print("\n".join(f"{i}. {ln[6:]}" for i, ln in enumerate(items, 1)) or paren(tr("inbox is empty")).strip())
    else:
        _inbox_mark(v, args.n, args.to)
        print(tr("✅ Inbox item #{n} processed", n=args.n) + (f" → {args.to}" if args.to else ""))
    if args.action != "list":
        render_html(v)


# ═══════════════════════════════════════════════════════════════ commands: views
def cmd_status(args):
    v = open_vault(args)
    t = today()
    prof = v.profile
    if args.gid:
        g = v.load_goal(args.gid)
        mt = goal_metrics(g, t, prof)
        if args.json:
            print(json.dumps(_mt_json(g, mt), ensure_ascii=False, indent=2))
            return
        print(render_card(g, mt, level="##"))
        vf = g.verify
        print("\n" + tr("Type {t} · status {s} · due {d} · budget {b} · evidence {e}", t=type_label(g.type), s=g.status,
                        d=g.meta.get("deadline") or "—", b=g.meta.get("budget") or "—", e=vf.get("method"))
              + (paren(tr("repo {r}", r=vf.get("repo"))) if vf.get("repo") else ""))
        print(tr("Definition of done: {v}", v=g.meta.get("done_when") or "—"))
        print(tr("Why: {v}", v=g.meta.get("why") or "—"))
        if g.phases:
            print(tr("Phases: {v}", v="; ".join(f"{p['id']} {p['title']}[{p['status']}]" for p in g.phases)))
        print("\n" + tr("Actions:"))
        for x in g.tasks:
            print("  " + x.dump()[2:])
        print("\n" + tr("Recent log:"))
        for lg in g.logs[-args.logs:]:
            print("  " + lg.dump()[2:])
        if g.decisions:
            print("\n" + tr("Decisions:"))
            for d in g.decisions[-5:]:
                print("  " + d.dump()[2:])
        return
    rows = [(g, goal_metrics(g, t, prof)) for g in v.goals(archive=args.all)]
    if args.json:
        print(json.dumps([_mt_json(g, m) for g, m in rows], ensure_ascii=False, indent=2))
        return
    rows.sort(key=lambda x: (x[0].status != "active", LIGHT_ORDER.get(x[1]["light"], 9), x[0].gid))
    for g, m in rows:
        nt = m["next"]
        print(f"{m['light']} {g.gid} {TYPE_ICON.get(g.type)} {g.title} · {g.status} · {m['progress']:.0%} · "
              f"{m['pace_text'] or '—'} · {tr('this week')} {m['week_short']} · {tr('next')} "
              f"{nt.tid + ' ' + nt.title if nt else '—'}")
        for r in m["risks"]:
            print(f"     ⚠ {r}")
    if not rows:
        print(paren(tr("no goals yet")).strip())


def _mt_json(g, m):
    d = {k: val for k, val in m.items() if k != "next"}
    d["next"] = f"{g.gid}.{m['next'].tid} {m['next'].title}" if m["next"] else None
    d["verify"] = g.verify
    return d


def cmd_board(args):
    v = open_vault(args)
    render_board(v)
    if args.print:
        print((v.root / "BOARD.md").read_text("utf-8"))
    else:
        print(tr("✅ Board updated: {p}", p=v.root / "BOARD.md") + "\n   " + tr("Web view: {p}", p=v.root / "dashboard.html"))
    if args.open:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        os.system(f'{opener} "{v.root / "dashboard.html"}"')


def cmd_advice(args):
    v = open_vault(args)
    cards = issue_advice(v, load_advice_file(args.file))
    render_html(v)
    print("\n\n".join(cards))


def cmd_stats(args):
    v = open_vault(args)
    t = today()
    start = t - dt.timedelta(days=args.days - 1)
    print(tr("📈 Range: {a} ~ {b} ({n} days)", a=start.isoformat(), b=t.isoformat(), n=args.days))
    for g in v.goals(archive=True):
        if args.gid and g.gid != args.gid.upper():
            continue
        logs = [lg for lg in g.logs if start <= (parse_date(lg.date)[0] or dt.date.min) <= t
                and lg.result in ("✓", "◐", "✗", "➜", "✂")]
        if not logs:
            continue
        res = {k: sum(1 for lg in logs if lg.result == k) for k in ("✓", "◐", "✗", "➜")}
        reasons, evid = {}, {}
        for lg in logs:
            if lg.reason:
                reasons[lg.reason] = reasons.get(lg.reason, 0) + 1
            if lg.evidence:
                evid[lg.evidence] = evid.get(lg.evidence, 0) + 1
        mins = sum(minutes_in(lg.value) for lg in logs)
        print(f"\n{TYPE_ICON.get(g.type)} {g.gid} {g.title}")
        print("  " + tr("Results:") + " " + "  ".join(f"{k}×{n}" for k, n in res.items() if n)
              + " · " + tr("spent {t}", t=fmt_hm(mins)))
        if reasons:
            print("  " + tr("Reasons:") + " " + "  ".join(f"{k}({tr(REASONS[k])})×{n}"
                                                          for k, n in sorted(reasons.items(), key=lambda x: -x[1])))
        if evid:
            print("  " + tr("Evidence:") + " " + "  ".join(f"{k}{tr(EVIDENCE[k])}×{n}" for k, n in evid.items()))
        deferred = [f"{x.tid}({x.defer})" for x in g.tasks if x.open and x.defer >= 2]
        if deferred:
            print("  " + tr("Repeatedly deferred:") + " " + ", ".join(deferred))
    planned = done = 0
    for i in range(args.days):
        p = v.daily_path(start + dt.timedelta(days=i))
        if p.exists():
            for row in re.findall(r"^\| (G\d+\.T\d+) \| (\S+) \|", p.read_text("utf-8"), re.M):
                planned += 1
                done += row[1] == "✓"
    if planned:
        print("\n" + tr("📅 Daily plan completion: {d}/{p} = {r}", d=done, p=planned, r=f"{done / planned:.0%}"))


# ═══════════════════════════════════════════════════════════════ commands: daily plan
def score_task(g, mt, x, t, prof):
    reasons = []
    s = PRIORITY_W.get(g.priority, 1)
    due = parse_date(x.fields.get("due"))[0]
    hard = False
    if not due and x.phase:
        try:
            due = parse_date(g.phase(x.phase).get("due"))[0]
        except MishuError:
            pass
    if not due:
        due, hard = parse_date(g.meta.get("deadline"))
    if due:
        left = (due - t).days
        u = 3 if left <= 1 else 2 if left <= 3 else 1 if left <= 7 else 0.5 if left <= 14 else 0
        if hard:
            u *= 1.5
        if u:
            s += u
            reasons.append(tr("past due") if left < 0 else tr("due in {n} days", n=left))
    s += min(2.0, mt["stale_days"] / max(1, prof.stale_days))
    if mt["stale_days"] >= prof.stale_days:
        reasons.append(tr("{n} days idle", n=mt["stale_days"]))
    if mt["light"] == "🔴":
        s += 1.5
        reasons.append(tr("goal 🔴"))
    elif mt["light"] == "🟡":
        s += 0.75
        reasons.append(tr("goal 🟡"))
    if x.mark == "/":
        s += 0.5
        reasons.append(tr("in progress"))
    phase_status = None
    if x.phase:
        try:
            phase_status = g.phase(x.phase).get("status")
        except MishuError:
            pass
    if phase_status == "todo":
        s -= 2.0
        reasons.append(tr("phase not started"))
    else:
        if phase_status == "active":
            s += 0.5
        first = next((y for y in g.tasks if y.open and y.tid not in g.recurring_ids and y.phase == x.phase), None)
        if first is x:
            s += 0.5
            reasons.append(tr("first in phase") if x.phase else tr("first in line"))
    if 0 < x.defer < 3:
        s += 0.3 * x.defer
        reasons.append(tr("deferred {n}×", n=x.defer))
    return round(s, 2), reasons


def build_candidates(v: Vault, hours, energy):
    t = today()
    prof = v.profile
    cap = int(round(hours * 60 * 0.7))
    habits, main, errands, waiting, breakdown = [], [], [], [], []
    for g in v.goals():
        if g.status != "active":
            continue
        mt = goal_metrics(g, t, prof)
        if mt["light"] == "⚪":
            continue
        rec = g.recurring_ids
        f = g.measure.get("frequency") or {}
        for x in g.tasks:
            ref = f"{g.gid}.{x.tid}"
            if x.mark == "!":
                since = parse_date(x.fields.get("since"))[0]
                waiting.append({"ref": ref, "title": x.title, "wait": x.fields.get("wait", tr("someone")),
                                "days": (t - since).days if since else None})
                continue
            if not x.open:
                continue
            item = {"ref": ref, "title": x.title, "est": x.est or 30, "min": x.fields.get("min"),
                    "goal": g.title, "type": g.type}
            if x.tid in rec:
                every = x.fields.get("every")
                if every:
                    if WEEKDAYS[t.weekday()] not in every.split(","):
                        continue
                elif f.get("task") == x.tid and freq_count(g, t) >= float(f.get("per_week") or 0):
                    continue
                item["score"], item["why"] = PRIORITY_W.get(g.priority, 1) + 2, [mt["pace_text"]]
                (habits if g.type == "habit" else main).append(item)
                continue
            if x.defer >= 3:
                breakdown.append({**item, "defer": x.defer})
                continue
            item["score"], item["why"] = score_task(g, mt, x, t, prof)
            if energy <= 2 and item["est"] > 60:
                if item["min"]:
                    item["why"].append(tr("low energy: minimum version {m}", m=item["min"]))
                else:
                    item["score"] -= 1.5
                    item["why"].append(tr("low energy: avoid big blocks"))
            (errands if g.type == "errand" or item["est"] <= 15 else main).append(item)
    for lst in (habits, main, errands):
        lst.sort(key=lambda i: -i["score"])
    used = 0
    for it in habits:
        cost = parse_minutes(it["min"]) if energy <= 2 and it["min"] else it["est"]
        if used + cost <= cap:
            it["pick"] = True
            used += cost
    picked_goals, picked = set(), 0
    for rnd in (0, 1):
        for it in main:
            if picked >= 3 or it.get("pick"):
                continue
            g_id = it["ref"].split(".")[0]
            if rnd == 0 and g_id in picked_goals:
                continue
            cost = parse_minutes(it["min"]) if energy <= 2 and it["min"] else it["est"]
            if used + cost <= cap:
                it["pick"] = True
                used += cost
                picked += 1
                picked_goals.add(g_id)
    for it in errands:
        if used + it["est"] <= cap:
            it["pick"] = True
            used += it["est"]
    return {"hours": hours, "energy": energy, "cap": cap, "used": used, "habit": habits, "main": main,
            "errand": errands, "waiting": waiting, "breakdown": breakdown}


def cmd_candidates(args):
    v = open_vault(args)
    c = build_candidates(v, args.hours, args.energy)
    if args.json:
        print(json.dumps(c, ensure_ascii=False, indent=2))
        return
    print(tr("Available {h}h · energy {e}/5 · cap {cap} · suggested total {used}", h=f"{args.hours:g}", e=args.energy,
             cap=fmt_hm(c["cap"]), used=fmt_hm(c["used"])))
    print(tr("(✔ = suggested by the rules; you may adjust, but keep within the cap and ≤3 main items)"))
    sections = (("habit", "🔁 " + tr("Habits due today")), ("main", "🎯 " + tr("Main candidates")),
                ("errand", "⚡ " + tr("Errand candidates")))
    for key, title in sections:
        print(f"\n{title}")
        for it in c[key][:12]:
            mark = "✔" if it.get("pick") else " "
            mn = " · " + tr("min {m}", m=it["min"]) if it.get("min") else ""
            why = ", ".join(w for w in it["why"] if w) or "—"
            print(f"  {mark} {it['ref']} {it['title']} · {it['est']}m{mn} · {tr('score')} {it['score']} · {why}")
        if not c[key]:
            print("  " + none_line())
    print("\n👀 " + tr("Waiting / follow-up"))
    for w in c["waiting"]:
        print("  " + tr("{ref} {title} (waiting on {who}, {n} days)", ref=w["ref"], title=w["title"], who=w["wait"],
                        n=w["days"] if w["days"] is not None else "?"))
    if not c["waiting"]:
        print("  " + none_line())
    if c["breakdown"]:
        print("\n⚠️ " + tr("Needs breakdown (deferred ≥3 times, excluded — issue an L2 advice card)"))
        for b in c["breakdown"]:
            print("  " + tr("{ref} {title} · deferred {n} times", ref=b["ref"], title=b["title"], n=b["defer"]))


def _ref_task(v, ref, cache):
    gid, tid = split_ref(ref)
    if gid not in cache:
        cache[gid] = v.load_goal(gid)
    g = cache[gid]
    return g, g.task(tid)


def cmd_plan(args):
    v = open_vault(args)
    t = today()
    path = v.daily_path(t)
    if path.exists():
        if REVIEW_RE.search(path.read_text("utf-8")):
            raise MishuError(tr("Today's check-in is already done; the plan can't be redone"))
        if not args.force:
            raise MishuError(tr("Today's plan already exists. If the user wants to re-plan, add --force"), 3)
    cache = {}
    sections = {"main": [], "habit": [], "errand": []}
    total = 0
    seen = set()
    for key in sections:
        for ref in [r for r in (getattr(args, key) or "").split(",") if r.strip()]:
            g, x = _ref_task(v, ref, cache)
            full = f"{g.gid}.{x.tid}"
            if full in seen:
                raise MishuError(tr("{r} appears twice", r=full))
            seen.add(full)
            if g.status != "active":
                raise MishuError(tr("{r} belongs to a goal that isn't active", r=full))
            if not x.open:
                raise MishuError(tr("{r} isn't open ({s})", r=full, s=x.status))
            if x.defer >= 3 and key != "habit":
                raise MishuError(tr("{r} was deferred {n} times — break it down or rethink it before scheduling", r=full, n=x.defer))
            use_min = args.energy <= 2 and x.fields.get("min")
            cost = parse_minutes(x.fields["min"]) if use_min else (x.est or 30)
            total += cost
            sections[key].append((g, x, cost, use_min))
    if len(sections["main"]) > 3:
        raise MishuError(tr("At most 3 main items"))
    cap = int(round(args.hours * 60 * 0.7))
    if total > cap:
        raise MishuError(tr("Planned total {t} exceeds the cap {c} (available × 0.7); remove something",
                            t=fmt_hm(total), c=fmt_hm(cap)))
    advices = load_advice_file(args.advice_file)
    cards = issue_advice(v, advices, limit=2) if advices else []
    prof = v.profile

    def line(g, x, cost, use_min, extra=""):
        s = f"- [ ] {g.gid}.{x.tid} {x.title} · {fmt_hm(cost)}"
        if use_min:
            s += paren(tr("minimum version; full {m}m", m=x.est))
        return s + extra

    out = [f"# 📅 {t.isoformat()} {weekday_name(t)}",
           tr("Available {h}h · energy {e}/5 · planned {p} (cap {c})", h=f"{args.hours:g}", e=args.energy,
              p=fmt_hm(total), c=fmt_hm(cap)), "",
           "## 🎯 " + tr("Main (max 3)")]
    out += [line(*it) for it in sections["main"]] or [none_line()]
    out += ["", "## 🔁 " + tr("Habits")]
    hl = []
    for g, x, cost, um in sections["habit"]:
        every = x.fields.get("every")
        if every and WEEKDAYS[t.weekday()] not in every.split(","):
            print(tr("⚠️ {gid}.{t} is scheduled for {e}; not due today (kept at the user's request)", gid=g.gid, t=x.tid, e=every))
        f = g.measure.get("frequency") or {}
        extra = paren(tr("last 7 days {c}/{p}", c=f"{freq_count(g, t):g}", p=gnum(f.get("per_week")))) \
            if f.get("task") == x.tid else ""
        hl.append(line(g, x, cost, um, extra))
    out += hl or [none_line()]
    out += ["", "## ⚡ " + tr("Errands (batch them in spare moments)")]
    out += [line(*it) for it in sections["errand"]] or [none_line()]
    out += ["", "## 👀 " + tr("Waiting / follow-up")]
    wl = []
    for g in v.goals():
        if g.status != "active":
            continue
        for x in g.tasks:
            if x.mark == "!":
                since = parse_date(x.fields.get("since"))[0]
                days = (t - since).days if since else None
                who = x.fields.get("wait", tr("someone"))
                s = f"- {g.gid}.{x.tid} {x.title}" + paren(
                    tr("waiting on {who}, {n} days", who=who, n=days) if days is not None else tr("waiting on {who}", who=who))
                if days is not None and days >= 3:
                    s += " → " + tr("follow up today")
                wl.append(s)
    out += wl or [none_line()]
    out += ["", "## 💡 " + tr("Mishu's advice (max 2)")]
    out += ["\n\n".join(cards)] if cards else [none_line()]
    if args.note:
        out += ["", f"> 📝 {clean(args.note)}"]
    v.daily_dir.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n", "utf-8")
    v.log_change("plan", t.isoformat(), f"main {len(sections['main'])} · habit {len(sections['habit'])} · "
                                         f"errand {len(sections['errand'])} · {fmt_hm(total)}")
    render_html(v)
    print(path.read_text("utf-8"))
    print(tr("✅ Wrote daily/{f} (check-in at {ci}); dashboard updated", f=path.name, ci=prof.get("checkin_time")))


def parse_plan_items(text):
    m = REVIEW_RE.search(text)
    plan = text[:m.start()] if m else text
    items, section = [], None
    for ln in plan.splitlines():
        if ln.startswith("## "):
            section = next((key for icon, key in DAILY_SECTIONS.items() if ln[3:].startswith(icon)), None)
            continue
        mm = re.match(r"^- \[ \] (G\d+\.T\d+) ", ln)
        if mm and section in ("main", "habit", "errand"):
            items.append((mm.group(1), section))
    return items


def cmd_checkin(args):
    v = open_vault(args)
    t = today()
    path = v.daily_path(t)
    if not path.exists():
        raise MishuError(tr("No plan for today. If the user didn't plan today, record progress item by item with log"))
    text = path.read_text("utf-8")
    if REVIEW_RE.search(text):
        raise MishuError(tr("Today's check-in is already done. Add or correct entries with log"))
    plan = parse_plan_items(text)
    plan_refs = {r for r, _ in plan}
    section_of = dict(plan)
    parsed = []
    for raw in args.item or []:
        parts = [p.strip() for p in raw.split("|")]
        parts += [""] * (7 - len(parts))
        ref, result, time, reason, evidence, note, qty = parts[:7]
        gid, tid = split_ref(ref)
        parsed.append((f"{gid}.{tid}", RESULT_ALIAS.get(result, result), time, reason or None,
                       EVIDENCE_ALIAS.get(evidence, evidence), note, num(qty, "qty") if qty else None))
    given = {p[0] for p in parsed}
    missing = [r for r, _ in plan if r not in given]
    if missing and not args.allow_missing:
        raise MishuError(tr("These planned items haven't been reviewed — ask the user about each: {v}",
                            v=", ".join(missing)))
    cache, summaries, hints, rows = {}, [], [], []
    for ref, result, time, reason, evidence, note, qty in parsed:
        gid, tid = split_ref(ref)
        if gid not in cache:
            cache[gid] = v.load_goal(gid, for_write=True)
        s, h = apply_result(v, cache[gid], tid, result, time or None, evidence, note, reason, qty, None, args.confirmed)
        summaries.append(s)
        hints += h
        tag = "" if ref in plan_refs else paren(tr("unplanned"))
        rows.append(f"| {ref} | {result} | {fmt_hm(parse_minutes(time)) if time else ''} | {reason or ''} | "
                    f"{evidence or ''} | {clean(note)}{tag} |")
    for r in missing:
        rows.append(f"| {r} | — |  |  |  | {tr('not reviewed')} |")
    cards = issue_advice(v, load_advice_file(args.advice_file), limit=1) if args.advice_file else []
    for g in cache.values():
        E, _ = validate_goal(g)
        if E:
            raise MishuError(tr("{gid} fails validation after write-back: {v}", gid=g.gid, v="; ".join(E)))
    for g in cache.values():
        v.save_goal(g, "checkin", f"{t.isoformat()} check-in", render=False)
    done = sum(1 for p in parsed if p[1] == "✓")
    main_total = sum(1 for _, s in plan if s == "main")
    main_done = sum(1 if p[1] == "✓" else 0.5 if p[1] == "◐" else 0 for p in parsed if section_of.get(p[0]) == "main")
    mins = sum(parse_minutes(p[2]) or 0 for p in parsed if p[2])
    tomorrow = []
    for ref in [r for r in (args.tomorrow or "").split(",") if r.strip()]:
        g, x = _ref_task(v, ref, {})
        tomorrow.append(f"{g.gid}.{x.tid}")
    heads = [tr(h) for h in ("Item", "Result", "Time", "Reason", "Evidence", "Note")]
    out = ["", "---", "## 🌙 " + tr("Evening check-in ({t})", t=dt.datetime.now().strftime("%H:%M")),
           "| " + " | ".join(heads) + " |", "|---|---|---|---|---|---|", *rows, "",
           f"**{tr('Stats')}** " + tr("done {d}/{n} · main {m}/{mt} · spent {s}", d=done, n=len(plan), m=f"{main_done:g}",
                                      mt=main_total, s=fmt_hm(mins)),
           f"**{tr('Written back')}** {sep().join(summaries) if summaries else '—'}",
           f"**{tr('Tomorrow')}** {' · '.join(tomorrow) if tomorrow else '—'}",
           f"**{tr('In one line')}** {clean(args.summary) if args.summary else '—'}"]
    if cards:
        out += ["", *cards]
    path.write_text(text.rstrip() + "\n" + "\n".join(out) + "\n", "utf-8")
    v.log_change("checkin", t.isoformat(), f"done {done}/{len(plan)}")
    render_board(v)
    print("\n".join(out))
    for h in hints:
        print(h)
    print("\n" + tr("✅ Check-in written to daily/{f}; goal files and board updated", f=path.name))


# ═══════════════════════════════════════════════════════════════ CLI
def build_parser():
    ap = argparse.ArgumentParser(prog="mishu.py", description="Mishu vault tool (the only writer)")
    ap.add_argument("--vault", help="vault path (default: MISHU_VAULT or ~/.config/mishu/config.json)")
    ap.add_argument("--today", help="simulate a date YYYY-MM-DD (testing)")
    ap.add_argument("--version", action="version", version=VERSION)
    sp = ap.add_subparsers(dest="cmd", required=True)

    p = sp.add_parser("init", help="create a vault")
    p.add_argument("--vault", dest="vault", required=True)
    p.add_argument("--lang", choices=LANGS, default="en", help="output language of this vault")
    p.add_argument("--set-default", action="store_true")
    p.add_argument("--name")
    p.add_argument("--capacity", help="total weekly capacity, e.g. 25h")
    p.add_argument("--daily", help="typical weekday availability, e.g. 3h")
    p.add_argument("--weekend", help="typical weekend availability, e.g. 5h")
    p.add_argument("--wip", type=int)
    p.add_argument("--stale", type=int)
    p.add_argument("--tone", choices=["gentle", "coach", "strict"])
    p.set_defaults(func=cmd_init)

    p = sp.add_parser("profile", help="show or edit the user profile")
    p.add_argument("action", choices=["show", "set", "background"])
    p.add_argument("key", nargs="?")
    p.add_argument("value", nargs="?")
    p.add_argument("--file", default="-", help="for background: text file, or - for stdin")
    p.add_argument("--confirmed", action="store_true")
    p.add_argument("--reason")
    p.set_defaults(func=cmd_profile)

    sp.add_parser("context", help="print a situation summary (injected when the skill starts)").set_defaults(func=cmd_context)
    sp.add_parser("validate", help="validate the vault").set_defaults(func=cmd_validate)

    p = sp.add_parser("status", help="goal status")
    p.add_argument("gid", nargs="?")
    p.add_argument("--json", action="store_true")
    p.add_argument("--all", action="store_true", help="include archived goals")
    p.add_argument("--logs", type=int, default=8)
    p.set_defaults(func=cmd_status)

    p = sp.add_parser("board", help="regenerate the board")
    p.add_argument("--print", action="store_true")
    p.add_argument("--open", action="store_true", help="open the web dashboard in a browser")
    p.set_defaults(func=cmd_board)

    p = sp.add_parser("add-goal", help="create a goal from a JSON draft (last step of intake)")
    p.add_argument("--file", default="-", help="JSON file, or - for stdin")
    p.add_argument("--dry-run", action="store_true", help="preview the goal card without writing")
    p.add_argument("--inbox", type=int, help="also mark inbox item N as processed")
    p.set_defaults(func=cmd_add_goal)

    p = sp.add_parser("set", help="structural change (needs the user's confirmation)")
    p.add_argument("gid")
    p.add_argument("field", choices=SET_FIELDS)
    p.add_argument("value")
    p.add_argument("--confirmed", action="store_true")
    p.add_argument("--reason")
    p.add_argument("--revisit")
    p.add_argument("--advice")
    p.set_defaults(func=cmd_set)

    p = sp.add_parser("decide", help="record a decision")
    p.add_argument("gid")
    p.add_argument("text")
    p.add_argument("--reason")
    p.add_argument("--revisit")
    p.add_argument("--advice")
    p.set_defaults(func=cmd_decide)

    p = sp.add_parser("phase", help="phases: done/start (progress), add (structural)")
    p.add_argument("action", choices=["done", "start", "add"])
    p.add_argument("target", help="done/start: G01.M2; add: G01")
    p.add_argument("--evidence")
    p.add_argument("--note")
    p.add_argument("--title")
    p.add_argument("--weight")
    p.add_argument("--due")
    p.add_argument("--confirmed", action="store_true")
    p.add_argument("--reason")
    p.set_defaults(func=cmd_phase)

    p = sp.add_parser("task", help="actions: add / set / edit")
    p.add_argument("action", choices=["add", "set", "edit"])
    p.add_argument("target", help="add: G01; set/edit: G01.T05")
    p.add_argument("title", nargs="?", help="add: verb-first title; set: the new status")
    p.add_argument("--status", help="set: todo/doing/blocked/cancel")
    p.add_argument("--est")
    p.add_argument("--phase")
    p.add_argument("--due")
    p.add_argument("--every")
    p.add_argument("--qty")
    p.add_argument("--min")
    p.add_argument("--wait")
    p.add_argument("--title", dest="new_title")
    p.add_argument("--reset-defer", action="store_true")
    p.add_argument("--confirmed", action="store_true")
    p.add_argument("--reason")
    p.set_defaults(func=cmd_task)

    p = sp.add_parser("log", help="record one execution result")
    p.add_argument("target", help="G01.T05")
    p.add_argument("--result", required=True, help="✓/◐/✗/➜/✂ or done/partial/skip/moved/cancel")
    p.add_argument("--time")
    p.add_argument("--qty", type=float)
    p.add_argument("--evidence", help="🔍/📷/🔗/💬 or code/photo/link/verbal")
    p.add_argument("--reason", help="T/E/U/A/B/O/P")
    p.add_argument("--note")
    p.add_argument("--date")
    p.add_argument("--confirmed", action="store_true")
    p.set_defaults(func=cmd_log)

    p = sp.add_parser("metric", help="update a metric's current value")
    p.add_argument("gid")
    p.add_argument("value")
    p.add_argument("--evidence", required=True)
    p.add_argument("--note")
    p.add_argument("--date")
    p.set_defaults(func=cmd_metric)

    p = sp.add_parser("funnel", help="update a funnel count")
    p.add_argument("gid")
    p.add_argument("stage")
    p.add_argument("change", help="+3 or =5")
    p.add_argument("--evidence", required=True)
    p.add_argument("--note")
    p.set_defaults(func=cmd_funnel)

    p = sp.add_parser("units", help="update learning units")
    p.add_argument("gid")
    p.add_argument("--done", type=int)
    p.add_argument("--mastered", type=int)
    p.add_argument("--evidence", required=True)
    p.add_argument("--note")
    p.set_defaults(func=cmd_units)

    p = sp.add_parser("evidence", help="save an evidence file (only with the user's consent)")
    p.add_argument("action", choices=["add"])
    p.add_argument("gid")
    p.add_argument("path")
    p.set_defaults(func=cmd_evidence)

    p = sp.add_parser("inbox", help="inbox")
    p.add_argument("action", choices=["add", "list", "done"])
    p.add_argument("text", nargs="?")
    p.add_argument("--n", type=int)
    p.add_argument("--to")
    p.set_defaults(func=cmd_inbox)

    p = sp.add_parser("candidates", help="today's candidates and suggested picks")
    p.add_argument("--hours", type=float, required=True)
    p.add_argument("--energy", type=int, required=True, choices=range(1, 6))
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_candidates)

    p = sp.add_parser("plan", help="write today's plan")
    p.add_argument("--hours", type=float, required=True)
    p.add_argument("--energy", type=int, required=True, choices=range(1, 6))
    p.add_argument("--main", default="")
    p.add_argument("--habit", default="")
    p.add_argument("--errand", default="")
    p.add_argument("--advice-file", help="advice card JSON (object or array), - for stdin")
    p.add_argument("--note")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_plan)

    p = sp.add_parser("checkin", help="evening check-in")
    p.add_argument("--item", action="append", help='"G01.T05|result|time|reason|evidence|note|qty", one per planned item')
    p.add_argument("--summary")
    p.add_argument("--tomorrow", help="pre-plan for tomorrow, e.g. G01.T06,G03.T03")
    p.add_argument("--advice-file")
    p.add_argument("--allow-missing", action="store_true")
    p.add_argument("--confirmed", action="store_true")
    p.set_defaults(func=cmd_checkin)

    p = sp.add_parser("advice", help="render advice cards (to show in chat)")
    p.add_argument("--file", default="-")
    p.set_defaults(func=cmd_advice)

    p = sp.add_parser("stats", help="stats: results, reason codes, evidence mix")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--gid")
    p.set_defaults(func=cmd_stats)
    return ap


def main(argv=None):
    global _TODAY
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    ap = build_parser()
    args = ap.parse_args(argv)
    if args.today:
        _TODAY = dt.date.fromisoformat(args.today)
    if args.cmd == "task":
        if args.action == "add" and not args.title:
            ap.error("task add needs a title")
        if args.action == "set":
            args.status = args.status or args.title
            if not args.status:
                ap.error("task set needs a status, e.g. task set G01.T05 blocked")
        if args.action == "edit":
            args.title = args.new_title
    if args.cmd == "inbox":
        if args.action == "add" and not args.text:
            ap.error("inbox add needs text")
        if args.action == "done" and not args.n:
            ap.error("inbox done needs --n")
    if args.cmd == "profile" and args.action == "set" and (not args.key or args.value is None):
        ap.error("profile set needs KEY VALUE")
    try:
        args.func(args)
    except MishuError as e:
        print(f"✗ {e}", file=sys.stderr)
        sys.exit(e.code)


if __name__ == "__main__":
    main()
