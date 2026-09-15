# English demo data — sourced by build_demo.sh (uses $CLI, $VAULT and on()).
on 2026-08-01 $CLI init --vault "$VAULT" --lang en --name Alex --capacity 25h --daily 3h --weekend 5h --wip 5 --tone coach

# ── a goal finished in August, so the "Completed" panel has something to show
on 2026-08-01 $CLI add-goal --file - <<'JSON'
{"title": "Launch a portfolio site", "type": "project", "area": "Career", "priority": "P2",
 "start": "2026-08-01", "deadline": "2026-08-31", "budget": "4h/w",
 "why": "Have one link to send with applications", "done_when": "Site live with 3 case studies",
 "phases": [{"title": "Build and publish", "due": "2026-08-25"}],
 "tasks": [{"title": "Pick a template and deploy it", "est": "90m", "phase": "M1"},
           {"title": "Write 3 case studies", "est": "120m", "phase": "M1"}]}
JSON
on 2026-08-05 $CLI log G01.T01 --result done --time 90m --evidence link --note "deployed to alex.dev"
on 2026-08-18 $CLI log G01.T02 --result done --time 2h --evidence link --note "3 case studies published"
on 2026-08-18 $CLI phase done G01.M1 --evidence link
on 2026-08-22 $CLI set G01 status done --confirmed --reason "Live at alex.dev with 3 case studies"

on 2026-09-01 $CLI add-goal --file - <<'JSON'
{"title": "Ship budgeting app v1", "type": "project", "area": "Career", "priority": "P1",
 "start": "2026-09-01", "deadline": "2026-11-30!", "budget": "8h/w",
 "why": "Portfolio piece + prove I can ship solo", "done_when": "Live on the App Store with 10 real users",
 "verify": {"method": "repo", "repo": "~/code/budget-app", "when": "every", "fallback": "verbal"},
 "phases": [{"title": "Requirements & prototype", "due": "2026-09-10"}, {"title": "Core expense tracking", "weight": 2, "due": "2026-10-20"},
            {"title": "Polish & launch", "due": "2026-11-30"}],
 "tasks": [{"title": "Wireframe the 5 core screens", "est": "90m", "phase": "M1"},
           {"title": "Pick the stack and scaffold the project", "est": "60m", "phase": "M1"},
           {"title": "Implement local expense CRUD", "est": "120m", "phase": "M2"},
           {"title": "Compare 3 iCloud sync options in a table", "est": "45m", "phase": "M2"},
           {"title": "Design the category & tag model", "est": "60m", "phase": "M2"},
           {"title": "Ask a designer friend for the app icon", "est": "15m", "phase": "M2"}]}
JSON

on 2026-09-01 $CLI add-goal --file - <<'JSON'
{"title": "Get down to 70 kg", "type": "habit", "area": "Health", "priority": "P1", "start": "2026-09-01", "budget": "3h/w",
 "why": "Checkup flagged my numbers; want my energy back", "done_when": "Two consecutive weeks at or below 70 kg",
 "measure": {"metric": {"name": "Weight", "unit": "kg", "baseline": 78, "target": 70, "current": 78, "direction": "down"},
             "frequency": {"task": "T01", "per_week": 4}},
 "tasks": [{"title": "Strength session (A/B alternating)", "est": "40m", "min": "10m"},
           {"title": "Weigh in and snap the scale", "est": "5m", "every": "sun"}]}
JSON

on 2026-09-01 $CLI add-goal --file - <<'JSON'
{"title": "Land a new-grad offer", "type": "pipeline", "area": "Career", "priority": "P0",
 "start": "2026-09-01", "deadline": "2026-11-15!", "budget": "5h/w",
 "why": "Start as a mobile engineer after graduation", "done_when": "Signed at least one mobile engineering offer",
 "phases": [{"title": "Polish the résumé", "due": "2026-09-07"}, {"title": "Apply in volume", "weight": 2, "due": "2026-10-15"},
            {"title": "Interviews", "weight": 2, "due": "2026-11-10"}, {"title": "Choose an offer", "due": "2026-11-15"}],
 "measure": {"funnel": [{"stage": "Applied", "count": 0}, {"stage": "Screened", "count": 0},
                        {"stage": "Interview", "count": 0}, {"stage": "Offer", "count": 0, "target": 1}],
             "frequency": {"stage": "Applied", "per_week": 10, "unit": "apps"}},
 "tasks": [{"title": "Rewrite project bullets against target JDs", "est": "90m", "phase": "M1"},
           {"title": "Build a target company list (20)", "est": "45m", "phase": "M2"},
           {"title": "Apply to 5 target companies", "est": "45m", "phase": "M2"},
           {"title": "Prepare 5 STAR behavioral stories", "est": "60m", "phase": "M3"}]}
JSON

on 2026-09-01 $CLI add-goal --file - <<'JSON'
{"title": "Finish the Rust Book", "type": "learning", "area": "Learning", "priority": "P2",
 "start": "2026-09-01", "deadline": "2026-12-31", "budget": "3.5h/w",
 "done_when": "All 20 chapters' exercises done, plus a small Rust CLI budget tool",
 "measure": {"units": {"name": "chapters", "total": 20, "done": 4, "mastered": 4}},
 "tasks": [{"title": "Read chapter 5 and do the exercises", "est": "90m"}, {"title": "Read chapter 6 and do the exercises", "est": "90m"},
           {"title": "Read chapter 7 and do the exercises", "est": "60m"}]}
JSON

on 2026-09-08 $CLI add-goal --file - <<'JSON'
{"title": "Buy a monitor arm", "type": "errand", "area": "Life", "priority": "P3", "deadline": "2026-09-20", "budget": "0.5h/w",
 "done_when": "Arm delivered and mounted", "tasks": [{"title": "Compare 3 arms on load and price", "est": "20m"}, {"title": "Place the order", "est": "10m"}]}
JSON

on 2026-09-03 $CLI inbox add "Build a personal website"
on 2026-09-10 $CLI inbox add "Get a driver's license before year end?"

on 2026-09-02 $CLI log G02.T01 --result done --time 90m --evidence code --note "commit 3f2a1c wireframes in docs/"
on 2026-09-03 $CLI log G03.T01 --result done --time 40m --evidence verbal
on 2026-09-04 $CLI log G02.T02 --result done --time 75m --evidence code --note "commit 8b7d02 SwiftUI+SwiftData scaffold"
on 2026-09-04 $CLI phase done G02.M1 --evidence code --note "wireframes and scaffold verified"
on 2026-09-05 $CLI log G04.T01 --result done --time 90m --evidence link --note "résumé v3 uploaded"
on 2026-09-05 $CLI phase done G04.M1 --evidence link
on 2026-09-05 $CLI log G03.T01 --result done --time 35m --evidence verbal
on 2026-09-06 $CLI log G05.T01 --result done --time 100m --evidence link --note "exercises in rust-book/ch05"
on 2026-09-06 $CLI units G05 --done 5 --mastered 5 --evidence link
on 2026-09-06 $CLI log G03.T02 --result done --time 5m --evidence photo
on 2026-09-06 $CLI metric G03 77.2 --evidence photo --note "scale photo checked"
on 2026-09-07 $CLI log G03.T01 --result done --time 40m --evidence verbal
on 2026-09-08 $CLI log G04.T02 --result skip --reason U --note "no idea which companies to target"
on 2026-09-09 $CLI log G02.T03 --result partial --time 60m --reason O --evidence code --note "commit c41e9a model layer done, UI not wired"
on 2026-09-09 $CLI log G03.T01 --result done --time 40m --evidence verbal
on 2026-09-10 $CLI log G04.T02 --result skip --reason U
on 2026-09-10 $CLI funnel G04 Applied +3 --evidence link --note "application screenshots"
on 2026-09-10 $CLI log G02.T04 --result moved --reason T
on 2026-09-11 $CLI task set G02.T06 blocked --wait Sam
on 2026-09-11 $CLI log G06.T01 --result done --time 20m --evidence verbal
on 2026-09-12 $CLI log G02.T04 --result skip --reason U --note "not sure where to start comparing"
on 2026-09-12 $CLI log G03.T01 --result done --time 40m --evidence verbal
on 2026-09-13 $CLI log G03.T02 --result done --time 5m --evidence photo
on 2026-09-13 $CLI metric G03 76.4 --evidence photo --note "scale photo checked, not stored"
on 2026-09-13 $CLI funnel G04 Screened +1 --evidence link --note "recruiter email"
on 2026-09-13 $CLI decide G02 "Drop multi-currency support" --reason "keep v1 focused" --revisit 2026-12-01

on 2026-09-14 $CLI plan --hours 4 --energy 3 --main G04.T02,G02.T04 --habit G03.T01 --errand G06.T02 --advice-file - <<'JSON' >/dev/null
[{"category": "adjust", "goal": "G04", "title": "Applications are behind pace", "level": "L2",
  "facts": "Last 7 days: 3/10 applications; G04.T02 deferred twice, both times reason U (unclear which companies)",
  "judgment": "The bottleneck is the missing target list, not time",
  "options": [{"label": "A", "text": "Spend 45m on the list today; keep next week's quota", "cost": "1–2 fewer applications this week"},
              {"label": "B", "text": "Lower the quota to 6 per week", "cost": "Offer likely ~2 weeks later"}],
  "recommend": "A", "recommend_reason": "already on today's main list", "ask": "Reply A or B"}]
JSON

on 2026-09-14 $CLI checkin \
  --item "G04.T02|done|50m||link|22 companies saved in Notion" \
  --item "G02.T04|skip||U||still unsure how to compare" \
  --item "G03.T01|done|35m||verbal|" \
  --item "G06.T02|done|10m||verbal|ordered, arrives Wednesday" \
  --item "G02.T03|partial|60m|O|code|sub-agent verified commit e19f55: list view wired, edit view missing" \
  --tomorrow "G02.T03,G04.T03" \
  --summary "Good day — the application block finally cleared" \
  --advice-file - <<'JSON' >/dev/null
{"category": "coach", "goal": "G02", "title": "Stuck on the iCloud sync research", "level": "L2",
 "facts": "G02.T04 deferred 3 times; 2 of them with reason U (unclear where to start)",
 "judgment": "The task is too vague: “compare 3 options” has no concrete first step or output format",
 "options": [{"label": "A", "text": "Split it: ① 25m list CloudKit / Core Data+CloudKit / a third-party SDK with doc links ② 30m fill a cost/complexity/offline table", "cost": "One more breakdown step; no extra work today"},
             {"label": "B", "text": "Skip sync in v1 and move it after M3", "cost": "No multi-device sync at launch; may hurt early retention"}],
 "recommend": "A", "recommend_reason": "sync is core; only the task definition is unclear", "ask": "Reply A or B and I'll update the plan"}
JSON
on 2026-09-14 $CLI metric G03 76.1 --evidence verbal --note "no photo today; verbal report" >/dev/null
