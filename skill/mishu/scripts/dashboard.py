# -*- coding: utf-8 -*-
"""dashboard.py — renders the view model from mishu.py into a read-only, single-file HTML dashboard.

Markdown in the vault stays the single source of truth; this module only presents, never computes or writes.
"""
from html import escape

TASK_GLYPH = {" ": ("○", "todo"), "/": ("◐", "doing"), "x": ("✓", "done"), "!": ("‖", "waiting"), "-": ("✕", "cancelled")}
RESULT_CLS = {"✓": "ok", "◐": "warn", "✗": "crit", "➜": "idle", "✂": "idle", "—": "idle"}
EVIDENCE_NAME = {"🔍": "Code check", "📷": "Photo", "🔗": "Link/file", "💬": "Verbal", "⚙️": "System"}
REASON_NAME = {"T": "No time", "E": "Low energy", "U": "Unclear", "A": "Avoiding it", "B": "Blocked",
               "O": "Underestimated", "P": "Plan changed"}
VERIFY_NAME = {"repo": "Code check", "photo": "Photo", "link": "Link/file", "verbal": "Verbal"}

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


# ───────────────────────────────────────────── components
def pill(cls, label):
    return f'<span class="pill {cls}"><i aria-hidden="true"></i>{e(label)}</span>'


def progress_block(g):
    marker = head = ""
    if g["expected"] is not None:
        marker = (f'<span class="expect" style="left:{pct(g["expected"])}" '
                  f'title="{e(_t("expected by now: {p}", p=format(g["expected"], ".0%")))}"></span>')
    head = f'<span class="num">{g["progress"]:.0%}</span>'
    if g["expected"] is not None:
        head += f'<span class="sub">{e(_t("expected {p}", p=format(g["expected"], ".0%")))}</span>'
    return (f'<div class="measure"><div class="measure-head">{head}</div>'
            f'<div class="bar" role="img" aria-label="{e(_t("Progress"))} {g["progress"]:.0%}">'
            f'<span class="fill {g["cls"]}" style="width:{pct(g["progress"])}"></span>{marker}</div>'
            f'<p class="detail">{e(g["progress_detail"])}</p></div>')


def freq_block(f):
    per = f["per"] or 0
    count = f["count"] or 0
    if per <= 14:
        dots = "".join(f'<span class="dot{" on" if i < count else ""}"></span>' for i in range(int(per)))
        vis = f'<div class="dots" aria-hidden="true">{dots}</div>'
    else:
        vis = f'<div class="bar thin"><span class="fill" style="width:{pct(count / per if per else 0)}"></span></div>'
    return (f'<div class="freq"><span class="k">{e(_t("last 7 days"))}</span>{vis}'
            f'<span class="v mono">{count:g}/{per:g} {e(f["unit"])}</span></div>')


def metric_block(mt):
    if not mt:
        return ""
    return (f'<div class="metric mono"><span>{e(_t("baseline"))} {e(mt.get("baseline"))}</span><span class="arrow">→</span>'
            f'<b>{e(mt.get("current"))}{e(mt.get("unit"))}</b><span class="arrow">→</span>'
            f'<span>{e(_t("target"))} {e(mt.get("target"))}</span></div>')


def funnel_block(funnel):
    if not funnel:
        return ""
    parts = []
    for st in funnel:
        tgt = f'<small>/{e(st["target"])}</small>' if st.get("target") else ""
        parts.append(f'<li><span class="k">{e(st["stage"])}</span><span class="v mono">{e(st.get("count", 0))}{tgt}</span></li>')
    return f'<ol class="funnel">{"".join(parts)}</ol>'


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


def goal_details(g):
    tasks = []
    for t in g["tasks"]:
        glyph, name = TASK_GLYPH.get(t["mark"], ("?", ""))
        meta = [x for x in [f'{t["est"]}m' if t["est"] else "", t["phase"] or "",
                            _t("every {d}", d=t["every"]) if t["every"] else "",
                            _t("deferred {n}×", n=t["defer"]) if t["defer"] else "",
                            _t("waiting on {who}", who=t["wait"]) if t["wait"] else ""] if x]
        tasks.append(f'<li class="task m-{name}"><span class="g" title="{e(_t(name))}">{glyph}</span>'
                     f'<span class="id mono">{e(t["tid"])}</span><span class="t">{e(t["title"])}</span>'
                     f'<span class="meta mono">{e(" · ".join(meta))}</span></li>')
    logs = []
    for lg in g["logs"]:
        note = lg["note"] or ""
        reason = ""
        if lg.get("reason"):
            note = note[len(lg["reason"]) + 2:].strip()
            reason = (f'<span class="rc" title="{e(_t(REASON_NAME.get(lg["reason"], "")))}">'
                      f'{e(lg["reason"])}</span>')
        logs.append(f'<tr><td class="mono">{e(lg["date"][5:])}</td><td class="mono">{e(lg["ref"])}</td>'
                    f'<td class="r {RESULT_CLS.get(lg["result"], "")}">{e(lg["result"])}</td>'
                    f'<td class="mono">{e(lg["value"])}</td>'
                    f'<td title="{e(_t(EVIDENCE_NAME[lg["evidence"]])) if lg["evidence"] in EVIDENCE_NAME else ""}">{e(lg["evidence"])}</td>'
                    f'<td>{reason}{e(note)}</td></tr>')
    decisions = "".join(f'<li><span class="mono">{e(d["date"][5:])} {e(d["did"])}</span> {e(d["text"])}'
                        + (f'<small>{e(_t("Reason"))}: {e(d["reason"])}</small>' if d["reason"] else "") + "</li>"
                        for d in g["decisions"])
    phases = "".join(f'<li class="ph {e(p.get("status"))}"><span class="mono">{e(p.get("id"))}</span> {e(p.get("title"))}'
                     f'<small class="mono">{e((p.get("due") or "")[5:])}</small></li>' for p in g["phases"])
    verify = g["verify"] or {}
    vtxt = _t(VERIFY_NAME[verify["method"]]) if verify.get("method") in VERIFY_NAME else "—"
    heads = "".join(f"<th>{e(_t(h))}</th>" for h in ("Date", "Item", "Result", "Time/value", "Evidence", "Note"))
    return f"""<details class="more">
  <summary>{e(_t("Actions, log & decisions"))}</summary>
  <div class="more-body">
    <p class="dw"><span class="k">{e(_t("Definition of done"))}</span>{e(g["done_when"])}</p>
    <p class="dw"><span class="k">{e(_t("Evidence"))}</span>{e(vtxt)}{" · " + e(verify.get("repo")) if verify.get("repo") else ""}</p>
    {f'<ol class="phases">{phases}</ol>' if phases else ""}
    <h4>{e(_t("Actions"))}</h4><ul class="tasks">{"".join(tasks)}</ul>
    <h4>{e(_t("Recent log"))}</h4>
    <div class="table-wrap"><table class="logs"><thead><tr>{heads}</tr></thead>
    <tbody>{"".join(logs)}</tbody></table></div>
    {f'<h4>{e(_t("Decisions"))}</h4><ul class="decisions">{decisions}</ul>' if decisions else ""}
  </div>
</details>"""


def goal_card(g, vmax):
    dl = "—"
    if g["deadline"]:
        dl = e(g["deadline"]) + (f'<b class="hard" title="{e(_t("hard deadline"))}">{e(_t("hard"))}</b>' if g["hard"] else "")
    if g["next"]:
        est = f'<span class="mono est">{g["next"]["est"]}m</span>' if g["next"]["est"] else ""
        nxt = f'<span class="id mono">{e(g["next"]["ref"])}</span><span class="t">{e(g["next"]["title"])}</span>{est}'
    elif g["progress"] >= 1:
        nxt = f'<span class="none">{e(_t("All actions done"))}</span>'
    else:
        nxt = f'<span class="none">{e(_t("No next action — break one down"))}</span>'
    risks = "".join(f"<li>{e(r)}</li>" for r in g["risks"])
    extra = (freq_block(g["freq"]) if g["freq"] else "") + metric_block(g["metric"]) + funnel_block(g["funnel"])
    return f"""<article class="goal s-{g["cls"]}" id="{e(g["gid"])}">
  <header class="goal-head">
    <div class="ident"><span class="gid mono">{e(g["gid"])}</span><span class="type">{e(g["type_label"])}</span><span class="pri mono">{e(g["priority"])}</span><span class="area">{e(g["area"])}</span></div>
    {pill(g["cls"], g["label"])}
  </header>
  <h3 class="goal-title">{e(g["title"])}</h3>
  <div class="goal-body">
    <div class="col-a">{progress_block(g)}{extra}</div>
    <dl class="facts">
      <div><dt>{e(_t("Pace"))}</dt><dd>{e(g["pace_text"]) or "—"}</dd></div>
      <div><dt>{e(_t("Due"))}</dt><dd class="mono">{dl}</dd></div>
      <div><dt>{e(_t("This week"))}</dt><dd>{e(g["week_text"])}</dd></div>
    </dl>
  </div>
  <div class="next"><span class="k">{e(_t("Next"))}</span>{nxt}</div>
  {f'<ul class="risks">{risks}</ul>' if risks else ""}
  {activity_block(g["activity"], vmax)}
  {goal_details(g)}
</article>"""


def daily_block(v):
    d = v["daily"]
    head = (f'<div class="panel-head"><h2 id="today-h">{e(_t("Today"))}</h2>'
            f'<span class="mono date">{e(v["date"][5:])} {e(v["weekday"])}</span></div>')
    if not d:
        msg = _t("No plan for today yet.") + "<br>" + e(_t("Ask Mishu “what should I do today?” to plan it."))
        if not v["goal_n"]:
            msg = e(_t("Add your first goals, then Mishu will plan each day for you."))
        return f'<section class="today box-panel" aria-labelledby="today-h">{head}<p class="empty">{msg}</p></section>'
    names = {"main": _t("Main"), "habit": _t("Habits"), "errand": _t("Errands")}
    groups = []
    for key, label in names.items():
        rows = []
        for it in d["sections"][key]:
            res = it.get("result")
            cls = RESULT_CLS.get(res, "") if res else ""
            sub = []
            if it.get("note"):
                sub.append(e(it["note"]))
            if res and res != "✓" and it.get("reason"):
                sub.append(e(_t("reason {c} {name}", c=it["reason"], name=_t(REASON_NAME.get(it["reason"], "")))))
            if it.get("rnote"):
                sub.append(e(it["rnote"]))
            rows.append(f"""<li class="item{" has-r " + cls if res else ""}">
  <span class="box {cls}" aria-label="{e(res or _t("not reviewed"))}">{e(res) if res else ""}</span>
  <div class="it"><div class="line"><span class="id mono">{e(it["ref"])}</span><span class="t">{e(it["title"])}</span></div>
  {f'<div class="sub">{" · ".join(sub)}</div>' if sub else ""}</div>
  <span class="time mono">{e(it.get("rtime") or it["time"])}</span>
</li>""")
        body = "".join(rows) if rows else f'<li class="none">{e(_t("none"))}</li>'
        hint = f'<small>{e(_t("max 3"))}</small>' if key == "main" else ""
        groups.append(f'<div class="grp g-{key}"><h3>{e(label)}{hint}</h3><ul>{body}</ul></div>')
    waiting = "".join(f"<li>{e(w)}</li>" for w in d["waiting"] if w.strip("（）() ") not in ("无", "none"))
    rv = d["review"]
    if rv:
        extra = "".join(f'<li><span class="box {RESULT_CLS.get(x["result"], "")}">{e(x["result"])}</span>'
                        f'<span class="id mono">{e(x["ref"])}</span> {e(x["rnote"].replace("（计划外）", "").replace(" (unplanned)", ""))}'
                        f'<small class="tag-extra">{e(_t("unplanned"))}</small></li>' for x in rv["extra"])
        summary = rv["summary"] if rv["summary"] not in ("", "—") else ""
        review = f"""<div class="review">
  <h3>{e(_t("Evening check-in"))}</h3>
  <p class="stats mono">{e(rv["stats"])}</p>
  {f'<ul class="extra">{extra}</ul>' if extra else ""}
  <dl><div><dt>{e(_t("Tomorrow"))}</dt><dd class="mono">{e(rv["tomorrow"])}</dd></div>
  {f'<div><dt>{e(_t("In one line"))}</dt><dd>{e(summary)}</dd></div>' if summary else ""}</dl>
</div>"""
    else:
        review = f'<p class="pending">{e(_t("Evening check-in: around {t}, tell Mishu “let’s review today”.", t=v["checkin_time"]))}</p>'
    return f"""<section class="today box-panel" aria-labelledby="today-h">
  {head}
  <p class="today-meta mono">{e(d["meta"])}</p>
  <div class="groups">
    {"".join(groups)}
    {f'<div class="grp g-wait"><h3>{e(_t("Waiting / follow-up"))}</h3><ul class="wait">{waiting}</ul></div>' if waiting else ""}
  </div>
  {review}
</section>"""


def advice_block(advice):
    if not advice:
        return ""
    cards = []
    for a in advice:
        opts = "".join(f'<li class="{"rec" if o["label"] == a.get("recommend") else ""}"><b class="mono">{e(o["label"])}</b>'
                       f'<div><p>{e(o["text"])}</p><p class="cost">{e(_t("Cost:"))} {e(o["cost"])}</p></div></li>'
                       for o in a.get("options") or [])
        rec = ""
        if a.get("recommend"):
            reason = (": " + e(a["recommend_reason"])) if a.get("recommend_reason") else ""
            rec = f'<p class="rec-line">{e(_t("Recommended"))} <b class="mono">{e(a["recommend"])}</b>{reason}</p>'
        cards.append(f"""<article class="advice">
  <header><span class="aid mono">{e(a["id"])}</span><span class="cat">{e(a.get("category_label") or a["category"])}</span><span class="lvl mono">{e(a["level"])}</span></header>
  <h3><span class="goal-ref">{e(a.get("goal_label") or a["goal"])}</span>{e(a["title"])}</h3>
  <dl><div><dt>{e(_t("Facts"))}</dt><dd>{e(a["facts"])}</dd></div><div><dt>{e(_t("Diagnosis"))}</dt><dd>{e(a["judgment"])}</dd></div></dl>
  {f'<ol class="opts">{opts}</ol>' if opts else ""}
  {rec}
  <p class="ask">{e(_t("Your call"))}: {e(a["ask"])}</p>
</article>""")
    return f'<section class="advice-list" aria-labelledby="adv-h"><h2 id="adv-h">{e(_t("Mishu’s advice"))}</h2>{"".join(cards)}</section>'


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


def render(v, tr):
    global _tr
    _tr = tr
    lang = v.get("lang", "en")
    goals_html = "".join(goal_card(g, v["activity_max"]) for g in v["goals"]) or \
        f'<p class="empty">{e(_t("No active goals yet. Tell Mishu “I want to…” to add your first one."))}</p>'
    att = []
    for a in v["attention"]:
        label = _t({"crit": "Risk", "warn": "Watch", "done": "Close?", "note": "Note"}.get(a["cls"], "Note"))
        ref = (f'<a class="id mono" href="#{e(a["gid"])}">{e(a["gid"])}</a><span class="t">{e(a.get("title", ""))}</span>'
               if a["gid"] else "")
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
    primary = (welcome_block() if empty else "") + daily_block(v) + advice_block(v["advice"])
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
<body>
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
      <div class="kpi"><dt>{e(_t("Inbox"))}</dt><dd><span class="mono big">{len(v["inbox"])}</span><span class="of">{e(_t("to process"))}</span></dd></div>
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
      {f'<section class="minor box-panel"><div class="panel-head"><h2>{e(_t("Inbox"))}</h2><span class="mono count">{len(v["inbox"])}</span></div><ul>{inbox}</ul></section>' if inbox else ""}
      {f'<section class="minor box-panel"><div class="panel-head"><h2>{e(_t("Paused · Someday · Drafts"))}</h2></div><ul>{others}</ul></section>' if others else ""}
    </aside>
  </main>

  <footer class="foot">{e(_t("Read-only view · generated by mishu.py at {t} · to change anything, just talk to Mishu", t=v["generated"]))}</footer>
</div>
</body>
</html>
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
a:focus-visible,summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:4px}
.wrap{max-width:1280px;margin:0 auto;padding-inline:24px;padding-block:28px 40px}

/* masthead */
.masthead{display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:20px 40px;padding-bottom:22px;border-bottom:1px solid var(--rule-strong)}
.brand{display:flex;align-items:center;gap:14px}
.seal{display:grid;place-items:center;width:44px;height:44px;border:2px solid var(--accent);color:var(--accent);font:700 22px/1 var(--serif);border-radius:6px;transform:rotate(-4deg)}
.brand h1{font:700 26px/1.2 var(--serif);letter-spacing:.02em}
.when{margin:2px 0 0;color:var(--muted);font-size:12.5px}
.kpis{display:flex;flex-wrap:wrap;gap:12px 36px}
.kpi dt{font-size:11.5px;color:var(--muted);letter-spacing:.08em}
.kpi dd{display:flex;align-items:baseline;flex-wrap:wrap;gap:6px 8px}
.big{font-size:24px;font-weight:500;line-height:1.2}
.of{color:var(--muted);font-size:12.5px}
.meter{flex-basis:100%;height:4px;background:var(--sunk);border-radius:2px;overflow:hidden;min-width:160px}
.meter span{display:block;height:100%;background:var(--accent)}
.lights{display:flex;gap:4px}

/* layout */
.layout{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:28px;margin-top:28px;align-items:start}
.primary{display:flex;flex-direction:column;gap:24px;min-width:0}
.side{display:flex;flex-direction:column;gap:16px;position:sticky;top:20px;max-height:calc(100vh - 40px);overflow-y:auto;min-width:0}

/* rounded panels shared by Today, Needs attention, Inbox */
.box-panel{background:var(--surface);border:1px solid var(--rule);border-radius:12px;padding:16px 18px}
.panel-head{display:flex;justify-content:space-between;align-items:baseline;gap:10px;padding-bottom:10px;border-bottom:1px solid var(--rule)}
.panel-head .count{font-size:12px;color:var(--muted);background:var(--sunk);border-radius:999px;padding:0 8px;line-height:20px}
h2{font:600 17px/1.3 var(--serif);letter-spacing:.03em}
.sec-head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
.empty{color:var(--muted);margin:10px 0 0}

/* status pills */
.pill{display:inline-flex;align-items:center;gap:6px;padding:1px 9px 1px 7px;border-radius:999px;font-size:12px;font-weight:500;white-space:nowrap;background:var(--idle-soft);color:var(--idle)}
.pill i{width:7px;height:7px;border-radius:50%;background:currentColor}
.pill.ok{background:var(--ok-soft);color:var(--ok)} .pill.warn{background:var(--warn-soft);color:var(--warn)} .pill.crit{background:var(--crit-soft);color:var(--crit)}

/* needs attention */
.attention ul{display:flex;flex-direction:column;gap:8px;margin-top:12px}
.att{display:grid;grid-template-columns:44px minmax(0,1fr);gap:10px;padding:10px 12px;border-radius:8px;background:var(--idle-soft)}
.att.crit{background:var(--crit-soft)} .att.warn{background:var(--warn-soft)} .att.done{background:var(--ok-soft)}
.att .tag{font-size:12px;font-weight:700;padding-top:1px}
.att.crit .tag{color:var(--crit)} .att.warn .tag{color:var(--warn)} .att.done .tag{color:var(--ok)} .att.note .tag{color:var(--muted)}
.att .id{text-decoration:none;font-size:12.5px;margin-right:8px}
.att .t{font-weight:500}
.att p{margin:2px 0 0;color:var(--muted);font-size:13px}

/* goal cards */
.goals{display:flex;flex-direction:column;gap:14px}
.legend{font-size:12px;color:var(--muted);display:inline-flex;align-items:center;gap:6px}
.expect-key{display:inline-block;width:2px;height:12px;background:var(--ink)}
.goal{background:var(--surface);border:1px solid var(--rule);border-radius:12px;padding:18px 20px 12px}
.goal.s-crit{border-color:color-mix(in srgb,var(--crit) 45%,var(--rule))}
.goal-head{display:flex;justify-content:space-between;align-items:center;gap:10px}
.ident{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px;color:var(--muted)}
.gid{color:var(--ink);font-weight:500;font-size:13px}
.type{border:1px solid var(--rule-strong);border-radius:4px;padding:0 5px;line-height:18px}
.goal-title{font:600 19px/1.35 var(--serif);margin:6px 0 14px}
.goal-body{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,1fr);gap:18px 28px}
.col-a{display:flex;flex-direction:column;gap:10px;min-width:0}
.measure-head{display:flex;align-items:baseline;gap:10px}
.measure-head .num{font:500 22px/1 var(--mono)}
.measure-head .sub{font-size:12px;color:var(--muted)}
.bar{position:relative;height:8px;background:var(--sunk);border-radius:4px;margin-top:8px}
.bar .fill{position:absolute;inset:0 auto 0 0;border-radius:4px;background:var(--accent)}
.bar .fill.ok{background:var(--ok)} .bar .fill.warn{background:var(--warn)} .bar .fill.crit{background:var(--crit)}
.bar.thin{height:5px;flex:1;margin:0}
.expect{position:absolute;top:-4px;bottom:-4px;width:2px;margin-left:-1px;background:var(--ink);border-radius:1px}
.detail{margin:6px 0 0;font-size:12.5px;color:var(--muted)}
.freq{display:flex;align-items:center;gap:10px;font-size:12.5px}
.freq .k{color:var(--muted);white-space:nowrap}
.dots{display:flex;gap:4px;flex-wrap:wrap}
.dot{width:10px;height:10px;border-radius:50%;border:1.5px solid var(--rule-strong)}
.dot.on{background:var(--ink);border-color:var(--ink)}
.freq .v{margin-left:auto;white-space:nowrap}
.metric{display:flex;align-items:baseline;gap:8px;font-size:12.5px;color:var(--muted);flex-wrap:wrap}
.metric b{color:var(--ink);font-size:14px}
.arrow{color:var(--faint)}
.funnel{display:flex;flex-wrap:wrap;gap:0;font-size:12.5px}
.funnel li{display:flex;flex-direction:column;padding:4px 14px 4px 0;margin-right:14px;border-right:1px solid var(--rule)}
.funnel li:last-child{border-right:0}
.funnel .k{color:var(--muted);font-size:11.5px}
.funnel .v{font-size:15px}
.funnel small{color:var(--faint)}
.facts{display:flex;flex-direction:column;gap:8px;font-size:13px}
.facts div{display:grid;grid-template-columns:38px minmax(0,1fr);gap:8px}
.facts dt{color:var(--muted);font-size:12px;padding-top:1px}
.hard{font:700 10.5px/1 var(--sans);color:var(--crit);border:1px solid currentColor;border-radius:3px;padding:1px 3px;margin-left:6px;vertical-align:1px}
.next{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-top:14px;padding-top:12px;border-top:1px dashed var(--rule)}
.next .k{font-size:12px;color:var(--muted)}
.next .id{font-size:12.5px;color:var(--accent)}
.next .t{font-weight:500}
.next .est{font-size:12px;color:var(--muted)}
.next .none{color:var(--muted)}
.risks{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.risks li{font-size:12px;color:var(--warn);background:var(--warn-soft);border-radius:4px;padding:1px 7px}
.activity{display:flex;align-items:flex-end;gap:10px;margin-top:12px}
.strip{display:grid;grid-template-columns:repeat(14,1fr);gap:3px;align-items:end;height:26px;width:168px}
.strip .b{height:var(--h);background:var(--accent);opacity:.75;border-radius:1.5px}
.strip .b.zero{height:2px;background:var(--rule-strong);opacity:1}
.strip .b:last-child{opacity:1}
.cap{font-size:11.5px;color:var(--faint)}

/* expandable details */
.more{margin-top:10px;border-top:1px solid var(--rule)}
.more summary{cursor:pointer;padding:9px 0 3px;font-size:12.5px;color:var(--muted);list-style:none}
.more summary::before{content:"▸";display:inline-block;width:14px;transition:transform .15s}
.more[open] summary::before{transform:rotate(90deg)}
.more summary::-webkit-details-marker{display:none}
.more-body{display:flex;flex-direction:column;gap:8px;padding:6px 0 10px}
.more h4{font:600 13px/1.4 var(--sans);margin-top:8px;color:var(--muted)}
.dw{margin:0;font-size:13px}
.dw .k,.phases small{color:var(--muted);font-size:12px;margin-right:8px}
.phases{display:flex;flex-wrap:wrap;gap:6px}
.ph{font-size:12.5px;border:1px solid var(--rule);border-radius:4px;padding:1px 8px;color:var(--muted)}
.ph.active{border-color:var(--accent);color:var(--ink)}
.ph.done{text-decoration:line-through;text-decoration-color:var(--faint)}
.ph small{margin:0 0 0 6px}
.tasks{display:flex;flex-direction:column}
.task{display:grid;grid-template-columns:18px 34px minmax(0,1fr) auto;gap:8px;padding:4px 0;font-size:13px;border-bottom:1px solid var(--rule)}
.task:last-child{border-bottom:0}
.task .g{color:var(--muted);text-align:center}
.task.m-done .t,.task.m-cancelled .t{color:var(--faint)}
.task.m-cancelled .t{text-decoration:line-through}
.task.m-done .g{color:var(--ok)} .task.m-doing .g{color:var(--accent)} .task.m-waiting .g{color:var(--warn)}
.task .id{color:var(--muted);font-size:12px}
.task .meta{font-size:11.5px;color:var(--faint);text-align:right}
.table-wrap{overflow-x:auto}
.logs{width:100%;border-collapse:collapse;font-size:12.5px}
.logs th{text-align:left;font-weight:500;color:var(--faint);font-size:11.5px;padding:3px 10px 3px 0;border-bottom:1px solid var(--rule)}
.logs td{padding:4px 10px 4px 0;border-bottom:1px solid var(--rule);vertical-align:top;white-space:nowrap}
.logs td:last-child{white-space:normal;min-width:180px}
.logs .r.ok{color:var(--ok)} .logs .r.warn{color:var(--warn)} .logs .r.crit{color:var(--crit)}
.rc{font:500 11px/1 var(--mono);color:var(--warn);border:1px solid currentColor;border-radius:3px;padding:1px 4px;margin-right:6px}
.decisions li{font-size:13px;padding:3px 0}
.decisions small{display:block;color:var(--muted)}

/* today: first in the main column, groups side by side */
.today{padding:18px 22px 18px}
.today .panel-head h2{font-size:19px}
.groups{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:4px 28px}
.groups .g-main{grid-column:1/-1}
.date{color:var(--muted);font-size:12.5px}
.today-meta{margin:4px 0 6px;font-size:12px;color:var(--muted)}
.grp{margin-top:12px}
.grp h3{font:700 12px/1.4 var(--sans);letter-spacing:.12em;color:var(--muted);display:flex;gap:8px;align-items:baseline;padding-bottom:4px;border-bottom:1px solid var(--rule)}
.grp h3 small{font-weight:400;letter-spacing:0;color:var(--faint)}
.item{display:grid;grid-template-columns:20px minmax(0,1fr) auto;gap:10px;align-items:start;padding:8px 0;border-bottom:1px dashed var(--rule)}
.item:last-child{border-bottom:0}
.box{width:18px;height:18px;margin-top:2px;border:1.5px solid var(--rule-strong);border-radius:4px;display:grid;place-items:center;font-size:12px;line-height:1;font-weight:700}
.box.ok{border-color:var(--ok);background:var(--ok);color:var(--surface)}
.box.warn{border-color:var(--warn);color:var(--warn)}
.box.crit{border-color:var(--crit);color:var(--crit)}
.box.idle{color:var(--idle)}
.it .line{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}
.it .id{font-size:11.5px;color:var(--accent)}
.it .t{font-weight:500}
.has-r.ok .t{color:var(--muted)}
.it .sub{font-size:12px;color:var(--muted);margin-top:2px}
.item .time{font-size:12px;color:var(--muted);white-space:nowrap;padding-top:2px}
.grp li.none{color:var(--faint);padding:6px 0;font-size:12.5px}
.wait li{font-size:12.5px;color:var(--muted);padding:5px 0}
.review{margin-top:16px;padding:12px 14px;border-radius:8px;background:var(--sunk)}
.review h3{font:600 14px/1.4 var(--serif)}
.stats{margin:4px 0 8px;font-size:12.5px}
.review .extra li{display:flex;gap:8px;align-items:center;font-size:12.5px;color:var(--muted);padding:3px 0}
.tag-extra{margin-left:auto;font-size:11px;border:1px solid var(--rule-strong);border-radius:3px;padding:0 4px;white-space:nowrap}
.review dl{display:flex;flex-direction:column;gap:4px;font-size:13px}
.review dl div{display:grid;grid-template-columns:64px minmax(0,1fr);gap:8px}
.review dt{color:var(--muted);font-size:12px}
.pending{margin:14px 0 0;font-size:12.5px;color:var(--muted)}

/* advice cards */
.advice-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}
.advice-list h2{grid-column:1/-1}
.advice{background:var(--surface);border:1px solid var(--rule);border-radius:12px;padding:14px 16px}
.advice header{display:flex;gap:8px;align-items:center;font-size:11.5px;color:var(--muted)}
.advice .cat{color:var(--accent);font-weight:700}
.advice .lvl{margin-left:auto;border:1px solid var(--rule-strong);border-radius:3px;padding:0 4px}
.advice h3{font:600 15px/1.4 var(--serif);margin:6px 0 8px}
.goal-ref{display:block;font:400 11.5px/1.4 var(--sans);color:var(--muted)}
.advice dl{display:flex;flex-direction:column;gap:4px;font-size:13px}
.advice dl div{display:grid;grid-template-columns:32px minmax(0,1fr);gap:6px}
.advice dt{color:var(--muted);font-size:12px}
.opts{display:flex;flex-direction:column;gap:6px;margin-top:10px}
.opts li{display:grid;grid-template-columns:22px minmax(0,1fr);gap:8px;padding:8px 10px;border:1px solid var(--rule);border-radius:6px;font-size:13px}
.opts li.rec{border-color:var(--accent);background:var(--accent-soft)}
.opts b{color:var(--accent)}
.opts p{margin:0}
.opts .cost{font-size:12px;color:var(--muted)}
.rec-line{margin:10px 0 0;font-size:13px}
.ask{margin:4px 0 0;font-size:13px;font-weight:500}

/* secondary info */
.minor h2{font-size:15px}
.minor ul{margin-top:4px}
.minor li{padding:8px 0;border-bottom:1px solid var(--rule);font-size:13px}
.minor li:last-child{border-bottom:0;padding-bottom:0}
.minor small{display:block;color:var(--muted)}
.minor .lbl{font-size:11.5px;color:var(--muted);margin-left:6px}
.foot{margin-top:40px;padding-top:14px;border-top:1px solid var(--rule);font-size:12px;color:var(--faint)}

/* English typography */
html[lang="en"]{--serif:"Source Serif 4",Georgia,"Times New Roman",serif;--sans:"IBM Plex Sans",-apple-system,"Segoe UI",system-ui,sans-serif}
html[lang="en"] .advice dl div{grid-template-columns:72px minmax(0,1fr)}
html[lang="en"] .facts div{grid-template-columns:72px minmax(0,1fr)}
html[lang="en"] .review dl div{grid-template-columns:88px minmax(0,1fr)}
html[lang="en"] .att{grid-template-columns:56px minmax(0,1fr)}

/* Empty vault onboarding */
.welcome{padding:22px 24px;border-color:var(--accent)}
.welcome h2{font-size:21px}
.welcome p{margin:8px 0 0;color:var(--muted)}
.steps{list-style:none;counter-reset:s;display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:14px}
.steps li{counter-increment:s;background:var(--sunk);border-radius:8px;padding:12px 14px;display:flex;flex-direction:column;gap:4px}
.steps li::before{content:counter(s);font:500 12px/1 var(--mono);color:var(--accent)}
.steps b{font-weight:600}
.steps span{font-size:13px;color:var(--muted)}
.try code{font-family:var(--mono);font-size:12.5px;background:var(--accent-soft);color:var(--accent);padding:2px 6px;border-radius:4px}

@media (max-width: 980px){
  /* narrow: welcome → today → attention → advice → goals → inbox */
  .layout{display:flex;flex-direction:column;gap:20px}
  .primary,.side{display:contents}
  .welcome{order:0} .today{order:1} .attention{order:2} .advice-list{order:3} .goals{order:4} .minor{order:5}
  .side{position:static;max-height:none}
}
@media (max-width: 560px){
  .wrap{padding-inline:16px}
  .goal{padding:16px 14px 10px}
  .goal-body{grid-template-columns:minmax(0,1fr)}
  .task{grid-template-columns:18px 34px minmax(0,1fr)}
  .task .meta{grid-column:3;text-align:left}
  .kpis{gap:12px 24px}
}
@media (prefers-reduced-motion: reduce){*{transition:none!important}}
"""
