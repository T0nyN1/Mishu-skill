# -*- coding: utf-8 -*-
"""dashboard.py — renders the view model from mishu.py into a read-only, single-file HTML dashboard.

Markdown in the vault stays the single source of truth; this module only presents, never computes or writes.
Checkboxes are a convenience for the reader: they live in the browser's localStorage and are copied back to
Mishu as text. Nothing here writes to the vault.
"""
import re
from html import escape

TASK_GLYPH = {" ": ("○", "todo"), "/": ("◐", "doing"), "x": ("✓", "done"), "!": ("‖", "waiting"), "-": ("✕", "cancelled")}
RESULT_CLS = {"✓": "ok", "◐": "warn", "✗": "crit", "➜": "idle", "✂": "idle", "—": "idle"}
REASON_NAME = {"T": "No time", "E": "Low energy", "U": "Unclear", "A": "Avoiding it", "B": "Blocked",
               "O": "Underestimated", "P": "Plan changed"}

_tr = None


def _t(_msg, /, **kw):
    return _tr(_msg, **kw)


def e(s):
    return escape("" if s is None else str(s))


def pct(x):
    return f"{max(0.0, min(1.0, x or 0)) * 100:.1f}%"


def fmt_min(m):
    h, r = divmod(int(m or 0), 60)
    return f"{h}h{r}m" if h and r else (f"{h}h" if h else f"{r}m")


def sep(parts):
    return " · ".join(x for x in parts if x)


# ───────────────────────────────────────────── components
def pill(cls, label):
    return f'<span class="pill {cls}"><i aria-hidden="true"></i>{e(label)}</span>'


def checkbox(ref, title, checked, scope, disabled=False):
    """A reader-side tick. data-init records the vault's own state so only real changes are copied back."""
    return (f'<input type="checkbox" class="chk" data-scope="{scope}" data-ref="{e(ref)}" data-title="{e(title)}"'
            f' data-init="{"1" if checked else "0"}"{" checked" if checked else ""}'
            f'{" disabled" if disabled else ""} aria-label="{e(title)}">')


def progress_detail(g):
    """The funnel breakdown lives in the goal's own panel; the card keeps the current phase only."""
    tail = _t("; funnel: {f}", f="\x00").split("\x00")[0]
    return g["progress_detail"].split(tail)[0]


def progress_block(g):
    marker = ""
    if g["expected"] is not None:
        marker = (f'<span class="expect" style="left:{pct(g["expected"])}" '
                  f'title="{e(_t("expected by now: {p}", p=format(g["expected"], ".0%")))}"></span>')
    head = f'<span class="num">{g["progress"]:.0%}</span>'
    if g["expected"] is not None:
        head += f'<span class="sub">{e(_t("expected {p}", p=format(g["expected"], ".0%")))}</span>'
    head += f'<span class="sub detail">{e(progress_detail(g))}</span>'
    return (f'<div class="measure"><div class="measure-head">{head}</div>'
            f'<div class="bar" role="img" aria-label="{e(_t("Progress"))} {g["progress"]:.0%}">'
            f'<span class="fill {g["cls"]}" style="width:{pct(g["progress"])}"></span>{marker}</div></div>')


def activity_block(act, vmax):
    bars = []
    for a in act:
        h = 0 if not a["minutes"] else max(12, round(a["minutes"] / vmax * 100))
        tip = f'{a["date"]} · ' + (fmt_min(a["minutes"]) if a["minutes"] else _t("no time logged"))
        if a["done"]:
            tip += " · " + _t("{n} done", n=a["done"])
        bars.append(f'<span class="b{" zero" if not h else ""}" style="--h:{h}%" title="{e(tip)}"></span>')
    total = fmt_min(sum(a["minutes"] for a in act))
    return (f'<div class="activity"><div class="strip" role="img" aria-label="{e(_t("last 14 days: {t}", t=total))}">'
            f'{"".join(bars)}</div><span class="cap">{e(_t("last 14 days: {t}", t=total))}</span></div>')


def goal_body(g, vmax):
    nums, tasks = {}, []
    for i, t in enumerate(g["tasks"], 1):
        nums[t["tid"]] = i
        _, name = TASK_GLYPH.get(t["mark"], ("?", ""))
        meta = sep([f'{t["est"]}m' if t["est"] else "", t["phase"] or "",
                    _t(name) if t["mark"] in ("/", "!", "-") else "",
                    _t("every {d}", d=t["every"]) if t["every"] else "",
                    _t("deferred {n}×", n=t["defer"]) if t["defer"] else "",
                    _t("waiting on {who}", who=t["wait"]) if t["wait"] else ""])
        box = checkbox(f'{g["gid"]}.{t["tid"]}', t["title"], t["mark"] == "x", "task", t["mark"] == "-")
        tasks.append(f'<li class="task m-{name}">{box}<span class="n mono">{i}.</span>'
                     f'<span class="t">{e(t["title"])}</span>'
                     f'<span class="meta mono">{e(meta)}</span></li>')
    logs = []
    for lg in g["logs"]:
        note, reason = lg["note"] or "", ""
        if lg.get("reason"):
            note = note[len(lg["reason"]) + 2:].strip()
            reason = (f'<span class="rc" title="{e(_t(REASON_NAME.get(lg["reason"], "")))}">'
                      f'{e(lg["reason"])}</span>')
        ref = f'#{nums[lg["ref"]]}' if lg["ref"] in nums else lg["ref"]
        logs.append(f'<tr><td class="mono">{e(lg["date"][5:])}</td><td class="mono">{e(ref)}</td>'
                    f'<td class="r {RESULT_CLS.get(lg["result"], "")}">{e(lg["result"])}</td>'
                    f'<td class="mono">{e(lg["value"])}</td>'
                    f'<td>{reason}{e(note)}</td></tr>')
    decisions = "".join(f'<li><span class="mono">{e(d["date"][5:])} {e(d["did"])}</span> {e(d["text"])}'
                        + (f'<small>{e(_t("Reason: {r}", r=d["reason"]))}</small>' if d["reason"] else "") + "</li>"
                        for d in g["decisions"])
    phases = "".join(f'<li class="ph {e(p.get("status"))}"><span class="mono">{e(p.get("id"))}</span> {e(p.get("title"))}'
                     f'<small class="mono">{e((p.get("due") or "")[5:])}</small></li>' for p in g["phases"])
    heads = "".join(f"<th>{e(_t(h))}</th>" for h in ("Date", "Item", "Result", "Time/value", "Note"))
    return f"""<div class="more-body">
    <p class="dw"><span class="k">{e(_t("Definition of done"))}</span>{e(g["done_when"])}</p>
    {f'<ol class="phases">{phases}</ol>' if phases else ""}
    <h4>{e(_t("Actions"))}</h4><ul class="tasks">{"".join(tasks)}</ul>
    {activity_block(g["activity"], vmax)}
    <h4>{e(_t("Recent log"))}</h4>
    <div class="table-wrap"><table class="logs"><thead><tr>{heads}</tr></thead>
    <tbody>{"".join(logs)}</tbody></table></div>
    {f'<h4>{e(_t("Decisions"))}</h4><ul class="decisions">{decisions}</ul>' if decisions else ""}
  </div>"""


def goal_card(g, vmax):
    dl = ""
    if g["deadline"]:
        dl = _t("Due") + " " + g["deadline"] + (" " + _t("hard") if g["hard"] else "")
    if g["next"]:
        est = f'<span class="mono est">{g["next"]["est"]}m</span>' if g["next"]["est"] else ""
        nxt = f'<span class="t">{e(g["next"]["title"])}</span>{est}'
    elif g["progress"] >= 1:
        nxt = f'<span class="none">{e(_t("All actions done"))}</span>'
    else:
        nxt = f'<span class="none">{e(_t("No next action — break one down"))}</span>'
    pace, week = g["pace_text"], g["week_text"]
    if pace and week.startswith(pace):      # frequency goals: the pace phrase opens the week line too
        week = week[len(pace):].lstrip(" ·")
    facts = sep([pace, dl, week])
    return f"""<details class="goal s-{g["cls"]}" id="{e(g["gid"])}">
  <summary class="goal-face">
    <div class="goal-head">
      <h3 class="goal-title">{e(g["title"])}</h3>
      {pill(g["cls"], g["label"])}<span class="caret" aria-hidden="true">▾</span>
    </div>
    {progress_block(g)}
    <p class="facts">{e(facts)}</p>
    <div class="next"><span class="k">{e(_t("Next"))}</span>{nxt}</div>
  </summary>
  {goal_body(g, vmax)}
</details>"""


def plan_meta(text):
    """'Available 4h · energy 3/5 · planned 2h20m (cap 2h48m)' → 'planned 2h20m · available 4h'."""
    parts = [x.strip() for x in text.split(" · ")]
    if len(parts) != 3:
        return text
    planned = parts[2].split("（")[0].split(" (")[0].strip()
    return sep([parts[0], planned])


def daily_block(v, titles):
    d = v["daily"]
    head = (f'<div class="panel-head"><h2 id="today-h">{e(_t("Today"))}</h2>'
            f'<span class="mono date">{e(v["date"][5:])} {e(v["weekday"])}</span></div>')
    if not d:
        msg = _t("No plan for today yet.") + "<br>" + e(_t("Ask Mishu “what should I do today?” to plan it."))
        if not v["goal_n"]:
            msg = e(_t("Add your first goals, then Mishu will plan each day for you."))
        return f'<section class="today box-panel" aria-labelledby="today-h">{head}<p class="empty">{msg}</p></section>'
    rows = []
    for it in d["sections"]["main"]:
        res = it.get("result")
        cls = RESULT_CLS.get(res, "") if res else ""
        gid = it["ref"].split(".")[0]
        sub = [f'<p class="mono">{e(sep([it["ref"], titles.get(gid, ""), it.get("rtime") or it["time"]]))}</p>']
        if it.get("note"):
            sub.append(f'<p>{e(it["note"])}</p>')
        if res and res != "✓" and it.get("reason"):
            sub.append(f'<p>{e(_t("reason {c} {name}", c=it["reason"], name=_t(REASON_NAME.get(it["reason"], ""))))}</p>')
        if it.get("rnote"):
            sub.append(f'<p>{e(it["rnote"])}</p>')
        tag = f'<span class="res {cls}" title="{e(_t("recorded"))}">{e(res)}</span>' if res and res != "✓" else ""
        rows.append(f"""<li class="item{" has-r " + cls if res else ""}">
  {checkbox(it["ref"], it["title"], res == "✓", "day")}
  <details class="row"><summary><span class="t">{e(it["title"])}</span>{tag}
  <span class="time mono">{e(it.get("rtime") or it["time"])}</span></summary>
  <div class="row-body">{"".join(sub)}</div></details>
</li>""")
    body = "".join(rows) if rows else f'<li class="none">{e(_t("none"))}</li>'
    waits = []
    for w in d["waiting"]:
        if w.strip("（）() ") in ("无", "none"):
            continue
        m = re.match(r"(G\d+\.T\d+)\s+(.*)", w)
        if m:
            waits.append(f'<li class="item">{checkbox(m.group(1), m.group(2), False, "wait")}'
                         f'<span class="t">{e(m.group(2))}</span></li>')
        else:
            waits.append(f'<li class="item plain"><span class="t">{e(w)}</span></li>')
    waiting = "".join(waits)
    return f"""<section class="today box-panel" aria-labelledby="today-h">
  {head}
  <p class="today-meta mono">{e(plan_meta(d["meta"]))}</p>
  <ul class="items">{body}</ul>
  {f'<div class="wait"><h3>{e(_t("Waiting / follow-up"))}</h3><ul>{waiting}</ul></div>' if waiting else ""}
</section>"""


def advice_block(advice):
    if not advice:
        return ""
    cards = []
    for a in advice:
        opts = "".join(
            f'<li class="{"rec" if o["label"] == a.get("recommend") else ""}"><label>'
            f'<input type="radio" class="pick" name="pick-{e(a["id"])}" data-card="{e(a["id"])}"'
            f' data-msg="{e(_t("Mishu, about “{t}” ({id}): I pick {l} — {x}", t=a["title"], id=a["id"], l=o["label"], x=o["text"]))}">'
            f'<b class="mono">{e(o["label"])}</b>'
            f'<div><p>{e(o["text"])}</p><p class="cost">{e(_t("Cost: {c}", c=o["cost"]))}</p></div></label></li>'
            for o in a.get("options") or [])
        rec = ""
        if a.get("recommend"):
            reason = e(_t("({r})", r=a["recommend_reason"])) if a.get("recommend_reason") else ""
            rec = f'<p class="rec-line">{e(_t("Recommended"))} <b class="mono">{e(a["recommend"])}</b> {reason}</p>'
        cards.append(f"""<article class="advice">
  <h3>{e(a["title"])}</h3>
  <p class="goal-ref">{e(sep([a.get("goal_label") or a["goal"], a.get("category_label") or a["category"]]))}</p>
  {f'<ol class="opts">{opts}</ol>' if opts else ""}
  {rec}
  <p class="ask">{e(_t("Your call: {a}", a=a["ask"]))}</p>
  {f'<button type="button" class="adv-reply" id="reply-{e(a["id"])}" hidden data-done="{e(_t("Copied"))}">{e(_t("Reply to Mishu"))}</button>' if opts else ""}
  <details class="more"><summary>{e(_t("Facts & diagnosis"))}</summary>
    <div class="more-body"><p>{e(a["facts"])}</p><p>{e(a["judgment"])}</p></div>
  </details>
</article>""")
    return (f'<section class="advice-panel box-panel" aria-labelledby="adv-h"><div class="panel-head">'
            f'<h2 id="adv-h">{e(_t("Mishu’s advice"))}</h2><span class="mono count">{len(advice)}</span></div>'
            f'{"".join(cards)}</section>')


def completed_block(done, limit=6):
    if not done:
        return ""
    items = "".join(
        f'<li><div class="c-head"><span class="c-check" aria-hidden="true">✓</span>'
        f'<span class="t">{e(c["title"])}</span></div>'
        f'<p class="c-meta mono">{e(c["line"])}</p>'
        + (f'<p class="c-dw">{e(c["done_when"])}</p>' if c["done_when"] else "") + "</li>"
        for c in done[:limit])
    more = (f'<p class="c-more">{e(_t("{n} more — ask Mishu to look back at completed goals", n=len(done) - limit))}</p>'
            if len(done) > limit else "")
    return (f'<section class="completed box-panel" aria-labelledby="done-h"><div class="panel-head">'
            f'<h2 id="done-h">{e(_t("Completed"))}</h2><span class="mono count">{len(done)}</span></div>'
            f'<ul>{items}</ul>{more}</section>')


def welcome_block():
    steps = [
        ("Brain-dump everything on your plate", "Projects, habits, errands, job hunting, studying — just list them."),
        ("Pick the 3–5 that matter most", "The rest waits in your inbox, so nothing gets lost."),
        ("Walk each one through intake", "Mishu drafts the details; you only correct them. Capacity is checked before anything goes live."),
    ]
    items = "".join(f'<li><b>{e(_t(a))}</b><span>{e(_t(b))}</span></li>' for a, b in steps)
    return f"""<section class="welcome box-panel" aria-labelledby="welcome-h">
  <h2 id="welcome-h">{e(_t("Welcome to Mishu"))}</h2>
  <p>{e(_t("Your vault is empty. Start by telling Mishu about your first goals:"))}</p>
  <ol class="steps">{items}</ol>
  <p class="try">{e(_t("Try saying:"))} <code>{e(_t("“Help me set up my first goals.”"))}</code></p>
</section>"""


def tray_block(date):
    return f"""<div id="tray" hidden data-head="{e(_t("Mishu, here’s today ({d}):", d=date))}"
     data-foot="{e(_t("Please record this."))}">
  <p class="t"><span class="mono" id="tray-n">0</span> {e(_t("ticked"))}</p>
  <button type="button" id="tray-copy" data-done="{e(_t("Copied"))}">{e(_t("Reply to Mishu"))}</button>
  <p class="hint">{e(_t("One click copies a ready message — paste it to Mishu and it gets recorded."))}</p>
</div>"""


def render(v, tr):
    global _tr
    _tr = tr
    lang = v.get("lang", "en")
    titles = {g["gid"]: g["title"] for g in v["goals"]}
    goals_html = "".join(goal_card(g, v["activity_max"]) for g in v["goals"]) or \
        f'<p class="empty">{e(_t("No active goals yet. Tell Mishu “I want to…” to add your first one."))}</p>'
    att = []
    for a in v["attention"]:
        label = _t({"crit": "Risk", "warn": "Watch", "done": "Close?", "note": "Note"}.get(a["cls"], "Note"))
        ref = (f'<a class="id mono" href="#{e(a["gid"])}">{e(a.get("title", ""))}</a>' if a["gid"] else "")
        att.append(f'<li class="att {e(a["cls"])}"><span class="tag">{e(label)}</span><div>{ref}<p>{e(a["text"])}</p></div></li>')
    others = "".join(f'<li><span class="mono">{e(o["gid"])}</span> {e(o["title"])} <span class="lbl">{e(o["label"])}</span>'
                     + (f"<small>{e(o['note'])}</small>" if o["note"] else "") + "</li>" for o in v["others"])
    inbox = "".join(f"<li>{e(x)}</li>" for x in v["inbox"])
    cap_min = (v["capacity_h"] or 0) * 60
    used = v["week_minutes"]
    c = v["counts"]
    title = _t("{name}’s Mishu desk", name=v["name"]) if v["name"] else _t("Mishu desk")
    fonts = ("family=Noto+Serif+SC:wght@600;700&family=Noto+Sans+SC:wght@400;500;700" if lang == "zh"
             else "family=Source+Serif+4:opsz,wght@8..60,600;8..60,700&family=IBM+Plex+Sans:wght@400;500;700")
    empty = not v["goal_n"]
    primary = (welcome_block() if empty else "") + daily_block(v, titles)
    if not empty:
        primary += f"""<section class="goals" aria-labelledby="goals-h">
        <div class="sec-head"><h2 id="goals-h">{e(_t("Goals"))}</h2><span class="legend"><span class="expect-key"></span>{e(_t("expected progress by now"))}</span></div>
        {goals_html}
      </section>"""
    return f"""<!doctype html>
<html lang="{"zh-CN" if lang == "zh" else "en"}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{fonts}&family=JetBrains+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
</head>
<body data-date="{e(v["date"])}">
<div class="wrap">
  <header class="masthead">
    <div class="brand">
      <span class="seal" aria-hidden="true">秘</span>
      <div><h1>{e(title)}</h1>
      <p class="mono when">{e(_t("{d} {wd} · week {w}", d=v["date"], wd=v["weekday"], w=v["week"]))}</p></div>
    </div>
    <dl class="kpis">
      <div class="kpi wide"><dt>{e(_t("This week"))}</dt><dd><span class="mono big">{fmt_min(used)}</span><span class="mono of">/ {v["capacity_h"]:g}h</span>
        <span class="meter" aria-hidden="true"><span style="width:{pct(used / cap_min if cap_min else 0)}"></span></span></dd></div>
      <div class="kpi"><dt>{e(_t("Active goals"))}</dt><dd><span class="mono big">{v["active_n"]}</span>
        <span class="lights">{pill("ok", str(c["ok"]))}{pill("warn", str(c["warn"]))}{pill("crit", str(c["crit"]))}</span></dd></div>
    </dl>
  </header>

  <main class="layout">
    <div class="primary">
      {primary}
    </div>

    <aside class="side">
      <section class="attention box-panel" aria-labelledby="att-h">
        <div class="panel-head"><h2 id="att-h">{e(_t("Needs attention"))}</h2><span class="mono count">{len(v["attention"])}</span></div>
        {f'<ul>{"".join(att)}</ul>' if att else f'<p class="empty">{e(_t("All clear — keep going as planned."))}</p>'}
      </section>
      {advice_block(v["advice"])}
      {f'<section class="minor box-panel"><div class="panel-head"><h2>{e(_t("Needs your input"))}</h2><span class="mono count">{len(v["inbox"])}</span></div><ul>{inbox}</ul></section>' if inbox else ""}
      {f'<section class="minor box-panel"><div class="panel-head"><h2>{e(_t("Paused · Someday · Drafts"))}</h2></div><ul>{others}</ul></section>' if others else ""}
      {completed_block(v.get("completed") or [])}
    </aside>
  </main>

  <footer class="foot">{e(_t("Read-only view · generated by mishu.py at {t} · to change anything, just talk to Mishu", t=v["generated"]))}</footer>
</div>
{tray_block(v["date"])}
<script>{JS}</script>
</body>
</html>
"""


JS = r"""
(function () {
  var date = document.body.getAttribute("data-date") || "";
  var boxes = [].slice.call(document.querySelectorAll("input.chk"));
  var day = boxes.filter(function (b) { return b.getAttribute("data-scope") === "day"; });
  var tray = document.getElementById("tray");
  var num = document.getElementById("tray-n");
  var btn = document.getElementById("tray-copy");
  var touched = false;
  function ref(b) { return b.getAttribute("data-ref"); }
  function key(b) { return "mishu:" + date + ":" + ref(b); }          // ticks are a report about today
  function base(b) { return b.getAttribute("data-init") === "1"; }
  function planned(r) { return day.some(function (b) { return ref(b) === r; }); }
  // one entry per action: today's list reports every item, an action only when you moved it
  function picked() {
    var seen = {}, out = [];
    day.forEach(function (b) { seen[ref(b)] = 1; if (b.checked) out.push(b); });
    boxes.forEach(function (b) {
      if (!planned(ref(b)) && !seen[ref(b)] && b.checked !== base(b)) { seen[ref(b)] = 1; out.push(b); }
    });
    return out;
  }
  function refresh() {
    var n = picked().length;
    if (num) num.textContent = n;
    if (tray) tray.hidden = !touched || n === 0;   // nothing ticked, nothing to report
  }
  function line(b) { return (b.checked ? "✓" : "✗") + " " + ref(b) + " " + (b.getAttribute("data-title") || ""); }
  function copy(text, button) {
    var was = button.textContent;
    function ok() {
      button.textContent = button.getAttribute("data-done");
      setTimeout(function () { button.textContent = was; }, 1500);
    }
    function fallback() {
      var ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); ok(); } catch (err) {}
      document.body.removeChild(ta);
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(ok, fallback);
    } else { fallback(); }
  }
  // advice cards: pick an option, then hand the choice back to Mishu
  [].slice.call(document.querySelectorAll("input.pick")).forEach(function (r) {
    r.addEventListener("change", function () {
      var card = r.closest(".advice");
      [].slice.call(card.querySelectorAll(".opts li")).forEach(function (li) {
        li.classList.toggle("on", li.contains(r));
      });
      var b = document.getElementById("reply-" + r.getAttribute("data-card"));
      if (b) b.hidden = false;
    });
  });
  [].slice.call(document.querySelectorAll("button.adv-reply")).forEach(function (b) {
    b.addEventListener("click", function () {
      var r = b.closest(".advice").querySelector("input.pick:checked");
      if (r) copy(r.getAttribute("data-msg"), b);
    });
  });
  try {   // ticks stored by older versions of this page were never day-scoped
    for (var i = localStorage.length - 1; i >= 0; i--) {
      var k = localStorage.key(i);
      if (k && k.indexOf("mishu:task:") === 0) localStorage.removeItem(k);
    }
  } catch (err) {}
  boxes.forEach(function (b) {
    try {
      var v = localStorage.getItem(key(b));
      if (v !== null) {
        if ((v === "1") === base(b)) localStorage.removeItem(key(b));
        else { b.checked = v === "1"; touched = true; }   // ticks from earlier today: keep the tray reachable
      }
    } catch (err) {}
    b.addEventListener("change", function () {
      boxes.forEach(function (o) { if (o !== b && ref(o) === ref(b)) o.checked = b.checked; });
      try {
        if (b.checked === base(b) && !planned(ref(b))) localStorage.removeItem(key(b));
        else localStorage.setItem(key(b), b.checked ? "1" : "0");
      } catch (err) {}
      touched = true;
      refresh();
    });
  });
  refresh();
  if (btn) {
    btn.addEventListener("click", function () {
      var lines = [tray.getAttribute("data-head")];
      day.forEach(function (b) { lines.push(line(b)); });
      picked().forEach(function (b) { if (!planned(ref(b))) lines.push(line(b)); });
      lines.push(tray.getAttribute("data-foot"));
      copy(lines.join("\n"), btn);
    });
  }
})();
"""

CSS = r"""
:root{
  --ground:#EDF0EE; --surface:#FFFFFF; --paper:#FAFBF9; --sunk:#E3E8E5;
  --ink:#18201D; --muted:#58655F; --faint:#88948F; --rule:#D3DAD6; --rule-strong:#B9C3BE;
  --accent:#2D4BA0; --accent-soft:#E2E7F6;
  --ok:#2F7D4F; --ok-soft:#DCEEE2; --warn:#9C6800; --warn-soft:#F5E9CB;
  --crit:#B3392A; --crit-soft:#F6DDD8; --idle:#6F7B76; --idle-soft:#E4E9E6;
  --serif:"Noto Serif SC","Songti SC","STSong",serif;
  --sans:"Noto Sans SC","PingFang SC","Hiragino Sans GB","Microsoft YaHei",system-ui,sans-serif;
  --mono:"JetBrains Mono",ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  color-scheme:light;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#0F1412; --surface:#171D1A; --paper:#141A17; --sunk:#202824;
    --ink:#E3E9E6; --muted:#9EABA5; --faint:#6F7B76; --rule:#2A332F; --rule-strong:#3B4641;
    --accent:#98ACF2; --accent-soft:#1F2946;
    --ok:#6FC392; --ok-soft:#163323; --warn:#E2B04C; --warn-soft:#382C10;
    --crit:#F08676; --crit-soft:#3B1C17; --idle:#8F9A95; --idle-soft:#222A26;
    color-scheme:dark;
  }
}
:root[data-theme="dark"]{
  --ground:#0F1412; --surface:#171D1A; --paper:#141A17; --sunk:#202824;
  --ink:#E3E9E6; --muted:#9EABA5; --faint:#6F7B76; --rule:#2A332F; --rule-strong:#3B4641;
  --accent:#98ACF2; --accent-soft:#1F2946;
  --ok:#6FC392; --ok-soft:#163323; --warn:#E2B04C; --warn-soft:#382C10;
  --crit:#F08676; --crit-soft:#3B1C17; --idle:#8F9A95; --idle-soft:#222A26;
  color-scheme:dark;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--ground);color:var(--ink);font:14px/1.6 var(--sans)}
.mono{font-family:var(--mono);font-variant-numeric:tabular-nums;letter-spacing:-.01em}
h1,h2,h3,h4{margin:0;text-wrap:balance}
ul,ol{margin:0;padding:0;list-style:none}
dl,dd{margin:0}
a{color:var(--accent)}
a:focus-visible,summary:focus-visible,input:focus-visible,button:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:4px}
.wrap{max-width:1180px;margin:0 auto;padding-inline:24px;padding-block:28px 40px}

/* masthead */
.masthead{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:20px 40px;padding-bottom:20px;border-bottom:1px solid var(--rule-strong)}
.brand{display:flex;align-items:center;gap:14px}
.seal{display:grid;place-items:center;width:42px;height:42px;border:2px solid var(--accent);color:var(--accent);font:700 21px/1 var(--serif);border-radius:6px;transform:rotate(-4deg)}
.brand h1{font:700 24px/1.2 var(--serif);letter-spacing:.02em}
.when{margin:2px 0 0;color:var(--muted);font-size:12.5px}
.kpis{display:flex;flex-wrap:wrap;gap:12px 32px}
.kpi dt{font-size:11.5px;color:var(--muted);letter-spacing:.08em}
.kpi dd{display:flex;align-items:baseline;flex-wrap:wrap;gap:6px 8px}
.big{font-size:22px;font-weight:500;line-height:1.2}
.of{color:var(--muted);font-size:12.5px}
.meter{flex-basis:100%;height:4px;background:var(--sunk);border-radius:2px;overflow:hidden;min-width:150px}
.meter span{display:block;height:100%;background:var(--accent)}
.lights{display:flex;gap:4px}

/* layout */
.layout{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:24px;margin-top:24px;align-items:start}
.primary{display:flex;flex-direction:column;gap:20px;min-width:0}
.side{display:flex;flex-direction:column;gap:14px;position:sticky;top:20px;max-height:calc(100vh - 40px);overflow-y:auto;min-width:0}

/* rounded panels */
.box-panel{background:var(--surface);border:1px solid var(--rule);border-radius:12px;padding:16px 18px}
.panel-head{display:flex;justify-content:space-between;align-items:baseline;gap:10px;padding-bottom:10px;border-bottom:1px solid var(--rule)}
.panel-head .count{font-size:12px;color:var(--muted);background:var(--sunk);border-radius:999px;padding:0 8px;line-height:20px}
h2{font:600 16px/1.3 var(--serif);letter-spacing:.03em}
.sec-head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
.empty{color:var(--muted);margin:10px 0 0;font-size:13px}

/* status pills */
.pill{display:inline-flex;align-items:center;gap:6px;padding:1px 9px 1px 7px;border-radius:999px;font-size:12px;font-weight:500;white-space:nowrap;background:var(--idle-soft);color:var(--idle)}
.pill i{width:7px;height:7px;border-radius:50%;background:currentColor}
.pill.ok{background:var(--ok-soft);color:var(--ok)} .pill.warn{background:var(--warn-soft);color:var(--warn)} .pill.crit{background:var(--crit-soft);color:var(--crit)}

/* checkboxes */
input.chk{appearance:none;-webkit-appearance:none;width:17px;height:17px;margin:3px 0 0;border:1.5px solid var(--rule-strong);border-radius:5px;background:var(--surface);cursor:pointer;flex:none;display:grid;place-items:center}
input.chk:checked{border-color:var(--accent);background:var(--accent)}
input.chk:checked::after{content:"";width:9px;height:5px;border:2px solid #fff;border-top:0;border-right:0;transform:rotate(-45deg) translate(1px,-1px)}
input.chk:disabled{opacity:.4;cursor:default}

/* needs attention */
.attention ul{display:flex;flex-direction:column;gap:8px;margin-top:12px}
.att{display:grid;grid-template-columns:40px minmax(0,1fr);gap:10px;padding:9px 11px;border-radius:8px;background:var(--idle-soft)}
.att.crit{background:var(--crit-soft)} .att.warn{background:var(--warn-soft)} .att.done{background:var(--ok-soft)}
.att .tag{font-size:12px;font-weight:700;padding-top:1px}
.att.crit .tag{color:var(--crit)} .att.warn .tag{color:var(--warn)} .att.done .tag{color:var(--ok)} .att.note .tag{color:var(--muted)}
.att .id{text-decoration:none;font-weight:500;font-family:var(--sans);font-size:13px}
.att p{margin:2px 0 0;color:var(--muted);font-size:12.5px}

/* goal cards */
.goals{display:flex;flex-direction:column;gap:12px}
.legend{font-size:12px;color:var(--muted);display:inline-flex;align-items:center;gap:6px}
.expect-key{display:inline-block;width:2px;height:12px;background:var(--ink)}
.goal{background:var(--surface);border:1px solid var(--rule);border-radius:12px}
.goal-face{display:block;cursor:pointer;list-style:none;padding:16px 18px 14px}
.goal-face::-webkit-details-marker{display:none}
.goal[open] .goal-face{padding-bottom:6px}
.goal .more-body{padding:0 18px 12px}
.caret{color:var(--faint);font-size:11px;transition:transform .15s}
.goal[open] .caret{transform:rotate(180deg)}
.goal.s-crit{border-color:color-mix(in srgb,var(--crit) 45%,var(--rule))}
.goal-head{display:flex;align-items:baseline;gap:10px}
.goal-title{flex:1;min-width:0}
.goal-title{font:600 17px/1.4 var(--serif)}
.measure{margin-top:12px}
.measure-head{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}
.measure-head .num{font:500 18px/1 var(--mono)}
.measure-head .sub{font-size:12px;color:var(--muted)}
.measure-head .detail{margin-left:auto;text-align:right}
.bar{position:relative;height:6px;background:var(--sunk);border-radius:3px;margin-top:8px}
.bar .fill{position:absolute;inset:0 auto 0 0;border-radius:3px;background:var(--accent)}
.bar .fill.ok{background:var(--ok)} .bar .fill.warn{background:var(--warn)} .bar .fill.crit{background:var(--crit)}
.expect{position:absolute;top:-3px;bottom:-3px;width:2px;margin-left:-1px;background:var(--ink);border-radius:1px}
.facts{margin:10px 0 0;font-size:12.5px;color:var(--muted)}
.next{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-top:10px;padding-top:10px;border-top:1px dashed var(--rule)}
.next .k{font-size:12px;color:var(--muted)}
.next .t{font-weight:500}
.next .est{font-size:12px;color:var(--muted)}
.next .none{color:var(--muted)}
.activity{display:flex;align-items:flex-end;gap:10px;margin-top:6px}
.strip{display:grid;grid-template-columns:repeat(14,1fr);gap:3px;align-items:end;height:24px;width:154px}
.strip .b{height:var(--h);background:var(--accent);opacity:.7;border-radius:1.5px}
.strip .b.zero{height:2px;background:var(--rule-strong);opacity:1}
.strip .b:last-child{opacity:1}
.cap{font-size:11.5px;color:var(--faint)}

/* expandable details */
.more{margin-top:8px;border-top:1px solid var(--rule)}
.more summary{cursor:pointer;padding:8px 0 2px;font-size:12.5px;color:var(--muted);list-style:none}
.more summary::before{content:"▸";display:inline-block;width:14px;transition:transform .15s}
.more[open] summary::before{transform:rotate(90deg)}
.more summary::-webkit-details-marker{display:none}
.more-body{display:flex;flex-direction:column;gap:8px;padding:6px 0 10px}
.more h4{font:600 12.5px/1.4 var(--sans);margin-top:6px;color:var(--muted)}
.dw{margin:0;font-size:13px}
.dw.ident{color:var(--faint);font-size:11.5px}
.dw .k,.phases small{color:var(--muted);font-size:12px;margin-right:8px}
.phases{display:flex;flex-wrap:wrap;gap:6px}
.ph{font-size:12.5px;border:1px solid var(--rule);border-radius:4px;padding:1px 8px;color:var(--muted)}
.ph.active{border-color:var(--accent);color:var(--ink)}
.ph.done{text-decoration:line-through;text-decoration-color:var(--faint)}
.ph small{margin:0 0 0 6px}
.tasks{display:flex;flex-direction:column}
.task{display:grid;grid-template-columns:17px 22px minmax(0,1fr) auto;gap:8px;align-items:start;padding:5px 0;font-size:13px;border-bottom:1px solid var(--rule)}
.task:last-child{border-bottom:0}
.task .n{color:var(--faint);font-size:12px;padding-top:2px}
.task .t{padding-top:1px}
.task.m-done .t,.task.m-cancelled .t{color:var(--faint)}
.task.m-cancelled .t{text-decoration:line-through}
.task .meta{font-size:11.5px;color:var(--faint);text-align:right;padding-top:2px}
.table-wrap{overflow-x:auto}
.logs{width:100%;border-collapse:collapse;font-size:12.5px}
.logs th{text-align:left;font-weight:500;color:var(--faint);font-size:11.5px;padding:3px 10px 3px 0;border-bottom:1px solid var(--rule)}
.logs td{padding:4px 10px 4px 0;border-bottom:1px solid var(--rule);vertical-align:top;white-space:nowrap}
.logs td:last-child{white-space:normal;min-width:180px}
.logs .r.ok{color:var(--ok)} .logs .r.warn{color:var(--warn)} .logs .r.crit{color:var(--crit)}
.rc{font:500 11px/1 var(--mono);color:var(--warn);border:1px solid currentColor;border-radius:3px;padding:1px 4px;margin-right:6px}
.decisions li{font-size:13px;padding:3px 0}
.decisions small{display:block;color:var(--muted)}

/* today */
.today{padding:18px 20px}
.today .panel-head h2{font-size:18px}
.date{color:var(--muted);font-size:12.5px}
.today-meta{margin:8px 0 2px;font-size:12px;color:var(--faint)}
.items{margin-top:2px}
.item{display:grid;grid-template-columns:17px minmax(0,1fr);gap:10px;align-items:start;padding:9px 0;border-bottom:1px solid var(--rule)}
.item:last-child{border-bottom:0;padding-bottom:2px}
.box{width:17px;height:17px;margin-top:3px;border:1.5px solid var(--rule-strong);border-radius:5px;display:grid;place-items:center;font-size:11px;line-height:1;font-weight:700}
.box.ok{border-color:var(--ok);background:var(--ok);color:var(--surface)}
.box.warn{border-color:var(--warn);color:var(--warn)}
.box.crit{border-color:var(--crit);color:var(--crit)}
.box.idle{color:var(--idle)}
.row{min-width:0}
.row summary{display:flex;align-items:baseline;gap:10px;cursor:pointer;list-style:none}
.row summary::-webkit-details-marker{display:none}
.row summary::after{content:"▾";margin-left:auto;color:var(--faint);font-size:11px;transition:transform .15s}
.row[open] summary::after{transform:rotate(180deg)}
.row .t{font-weight:500}
.has-r.ok .row .t{color:var(--muted)}
.row .time{font-size:12px;color:var(--faint);white-space:nowrap}
.item.plain{grid-template-columns:minmax(0,1fr)}
.wait .item .t{font-size:12.5px;color:var(--muted);font-weight:400}
.row .res{font-size:12px;font-weight:700}
.row .res.warn{color:var(--warn)} .row .res.crit{color:var(--crit)} .row .res.idle{color:var(--idle)}
.row-body{padding:6px 0 2px;display:flex;flex-direction:column;gap:3px}
.row-body p{margin:0;font-size:12.5px;color:var(--muted)}
.items li.none{color:var(--faint);padding:8px 0;font-size:12.5px}
.wait{margin-top:12px;padding-top:8px;border-top:1px solid var(--rule)}
.wait h3{font:700 11.5px/1.4 var(--sans);letter-spacing:.1em;color:var(--faint)}
.wait li{font-size:12.5px;color:var(--muted);padding:4px 0}

/* advice cards — the choices Mishu puts to you */
.advice-panel .advice{padding:12px 0;border-bottom:1px solid var(--rule)}
.advice-panel .advice:last-child{border-bottom:0;padding-bottom:2px}
.advice h3{font:600 14px/1.45 var(--serif)}
.goal-ref{margin:2px 0 0;font-size:11.5px;color:var(--muted)}
.opts{display:flex;flex-direction:column;gap:6px;margin-top:8px}
.opts li{border:1px solid var(--rule);border-radius:6px;font-size:12.5px}
.opts label{display:grid;grid-template-columns:14px 16px minmax(0,1fr);gap:8px;align-items:start;padding:7px 9px;cursor:pointer}
.opts input.pick{margin:3px 0 0;accent-color:var(--accent)}
.opts li.rec{border-color:color-mix(in srgb,var(--accent) 45%,var(--rule))}
.opts li.on{border-color:var(--accent);background:var(--accent-soft)}
.opts b{color:var(--accent)}
.opts p{margin:0}
.opts .cost{font-size:11.5px;color:var(--muted);margin-top:2px}
.rec-line{margin:8px 0 0;font-size:12.5px;color:var(--muted)}
.ask{margin:6px 0 0;font-size:12.5px;font-weight:500}
.adv-reply{margin-top:8px;font:500 12.5px/1 var(--sans);color:var(--surface);background:var(--accent);border:0;border-radius:8px;padding:8px 12px;cursor:pointer;width:100%}
.adv-reply[hidden]{display:none}
.advice .more{margin-top:6px;border-top:0}
.advice .more-body p{margin:0;font-size:12.5px;color:var(--muted)}

/* secondary info */
.minor h2{font-size:14.5px}
.minor ul{margin-top:4px}
.minor li{padding:8px 0;border-bottom:1px solid var(--rule);font-size:13px}
.minor li:last-child{border-bottom:0;padding-bottom:0}
.minor small{display:block;color:var(--muted)}
.minor .lbl{font-size:11.5px;color:var(--muted);margin-left:6px}
.foot{margin-top:36px;padding-top:14px;border-top:1px solid var(--rule);font-size:12px;color:var(--faint)}

/* completed goals */
.completed h2{font-size:14.5px}
.completed ul{margin-top:4px}
.completed li{padding:8px 0;border-bottom:1px solid var(--rule)}
.completed li:last-child{border-bottom:0;padding-bottom:0}
.c-head{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.c-check{color:var(--ok);font-weight:700}
.c-head .t{font-weight:500;font-size:13px}
.c-meta{margin:2px 0 0;font-size:11.5px;color:var(--faint)}
.c-dw{margin:2px 0 0;font-size:12.5px;color:var(--muted)}
.c-more{margin:10px 0 0;font-size:12px;color:var(--muted)}

/* copy tray */
#tray{position:fixed;right:20px;bottom:20px;z-index:20;max-width:260px;background:var(--surface);border:1px solid var(--rule-strong);border-radius:12px;padding:12px 14px;box-shadow:0 6px 24px rgba(0,0,0,.14)}
#tray[hidden]{display:none}
#tray .t{margin:0 0 8px;font-size:13px}
#tray button{font:500 13px/1 var(--sans);color:var(--surface);background:var(--accent);border:0;border-radius:8px;padding:8px 12px;cursor:pointer;width:100%}
#tray .hint{margin:8px 0 0;font-size:11.5px;color:var(--faint);line-height:1.5}

/* English typography */
html[lang="en"]{--serif:"Source Serif 4",Georgia,"Times New Roman",serif;--sans:"IBM Plex Sans",-apple-system,"Segoe UI",system-ui,sans-serif}
html[lang="en"] .att{grid-template-columns:52px minmax(0,1fr)}

/* Empty vault onboarding */
.welcome{padding:20px 22px;border-color:var(--accent)}
.welcome h2{font-size:20px}
.welcome p{margin:8px 0 0;color:var(--muted)}
.steps{list-style:none;counter-reset:s;display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:14px}
.steps li{counter-increment:s;background:var(--sunk);border-radius:8px;padding:12px 14px;display:flex;flex-direction:column;gap:4px}
.steps li::before{content:counter(s);font:500 12px/1 var(--mono);color:var(--accent)}
.steps b{font-weight:600}
.steps span{font-size:13px;color:var(--muted)}
.try code{font-family:var(--mono);font-size:12.5px;background:var(--accent-soft);color:var(--accent);padding:2px 6px;border-radius:4px}

@media (max-width: 980px){
  /* narrow: welcome → today → attention → advice → goals → inbox */
  .layout{display:flex;flex-direction:column;gap:18px}
  .primary,.side{display:contents}
  .welcome{order:0} .today{order:1} .attention{order:2} .advice-panel{order:3} .goals{order:4} .minor{order:5} .completed{order:6}
  .side{position:static;max-height:none}
}
@media (max-width: 560px){
  .wrap{padding-inline:16px}
  .goal-face{padding:14px 14px 12px}
  .goal .more-body{padding:0 14px 10px}
  .task{grid-template-columns:17px 22px minmax(0,1fr)}
  .task .meta{grid-column:3;text-align:left}
  .measure-head .detail{margin-left:0;text-align:left;flex-basis:100%}
  .kpis{gap:12px 24px}
  #tray{left:16px;right:16px;max-width:none}
}
@media (prefers-reduced-motion: reduce){*{transition:none!important}}
"""
