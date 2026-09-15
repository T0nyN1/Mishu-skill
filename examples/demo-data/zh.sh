# 中文演示数据 —— 由 build_demo.sh 调用（使用 $CLI、$VAULT 和 on()）。
on 2026-08-01 $CLI init --vault "$VAULT" --lang zh --name 小林 --capacity 25h --daily 3h --weekend 5h --wip 5 --tone coach

# ── 8 月已完成的目标，让「已完成」面板有内容可看
on 2026-08-01 $CLI add-goal --file - <<'JSON'
{"title": "上线个人作品集网站", "type": "project", "area": "事业", "priority": "P2",
 "start": "2026-08-01", "deadline": "2026-08-31", "budget": "4h/w",
 "why": "投简历时能附上一个链接", "done_when": "网站上线，并包含 3 个项目案例",
 "phases": [{"title": "搭建与发布", "due": "2026-08-25"}],
 "tasks": [{"title": "选模板并部署上线", "est": "90m", "phase": "M1"},
           {"title": "写 3 个项目案例", "est": "120m", "phase": "M1"}]}
JSON
on 2026-08-05 $CLI log G01.T01 --result done --time 90m --evidence link --note "已部署到 xiaolin.dev"
on 2026-08-18 $CLI log G01.T02 --result done --time 2h --evidence link --note "3 个案例已发布"
on 2026-08-18 $CLI phase done G01.M1 --evidence link
on 2026-08-22 $CLI set G01 status done --confirmed --reason "网站已上线，含 3 个项目案例"

on 2026-09-01 $CLI add-goal --file - <<'JSON'
{"title": "上线记账 App v1", "type": "project", "area": "事业", "priority": "P1",
 "start": "2026-09-01", "deadline": "2026-11-30!", "budget": "8h/w",
 "why": "作品集 + 验证独立开发能力", "done_when": "App Store 上架，且有 10 个真实用户在用",
 "verify": {"method": "repo", "repo": "~/code/ledger-app", "when": "every", "fallback": "verbal"},
 "phases": [{"title": "需求与原型", "due": "2026-09-10"}, {"title": "核心记账功能", "weight": 2, "due": "2026-10-20"},
            {"title": "打磨与上架", "due": "2026-11-30"}],
 "tasks": [{"title": "画出 5 个核心页面线框图", "est": "90m", "phase": "M1"},
           {"title": "确定技术栈并搭建项目骨架", "est": "60m", "phase": "M1"},
           {"title": "实现账目 CRUD 本地存储", "est": "120m", "phase": "M2"},
           {"title": "调研 3 种 iCloud 同步方案并写对比表", "est": "45m", "phase": "M2"},
           {"title": "设计分类与标签数据结构", "est": "60m", "phase": "M2"},
           {"title": "请设计朋友出 App 图标", "est": "15m", "phase": "M2"}]}
JSON

on 2026-09-01 $CLI add-goal --file - <<'JSON'
{"title": "减到 70kg", "type": "habit", "area": "健康", "priority": "P1", "start": "2026-09-01", "budget": "3h/w",
 "why": "体检指标偏高，想恢复精力", "done_when": "连续两周体重 ≤ 70kg",
 "measure": {"metric": {"name": "体重", "unit": "kg", "baseline": 78, "target": 70, "current": 78, "direction": "down"},
             "frequency": {"task": "T01", "per_week": 4}},
 "tasks": [{"title": "力量训练 A/B 组交替", "est": "40m", "min": "10m"},
           {"title": "称体重并拍照记录", "est": "5m", "every": "sun"}]}
JSON

on 2026-09-01 $CLI add-goal --file - <<'JSON'
{"title": "拿到秋招 offer", "type": "pipeline", "area": "事业", "priority": "P0",
 "start": "2026-09-01", "deadline": "2026-11-15!", "budget": "5h/w",
 "why": "毕业后进入大厂做客户端开发", "done_when": "拿到至少 1 个客户端开发 offer 并签约",
 "phases": [{"title": "简历打磨", "due": "2026-09-07"}, {"title": "集中投递", "weight": 2, "due": "2026-10-15"},
            {"title": "面试", "weight": 2, "due": "2026-11-10"}, {"title": "选择 offer", "due": "2026-11-15"}],
 "measure": {"funnel": [{"stage": "投递", "count": 0}, {"stage": "初筛通过", "count": 0},
                        {"stage": "面试", "count": 0}, {"stage": "offer", "count": 0, "target": 1}],
             "frequency": {"stage": "投递", "per_week": 10, "unit": "家"}},
 "tasks": [{"title": "按 JD 改写简历项目经历", "est": "90m", "phase": "M1"},
           {"title": "整理目标公司清单（20 家）", "est": "45m", "phase": "M2"},
           {"title": "投递 5 家目标公司", "est": "45m", "phase": "M2"},
           {"title": "准备 5 个 STAR 行为面试故事", "est": "60m", "phase": "M3"}]}
JSON

on 2026-09-01 $CLI add-goal --file - <<'JSON'
{"title": "学完 Rust Book", "type": "learning", "area": "学习", "priority": "P2",
 "start": "2026-09-01", "deadline": "2026-12-31", "budget": "3.5h/w",
 "done_when": "20 章全部完成课后练习，并用 Rust 写一个命令行记账小工具",
 "measure": {"units": {"name": "章", "total": 20, "done": 4, "mastered": 4}},
 "tasks": [{"title": "读第 5 章并完成练习", "est": "90m"}, {"title": "读第 6 章并完成练习", "est": "90m"},
           {"title": "读第 7 章并完成练习", "est": "60m"}]}
JSON

on 2026-09-08 $CLI add-goal --file - <<'JSON'
{"title": "买显示器支架", "type": "errand", "area": "生活", "priority": "P3", "deadline": "2026-09-20", "budget": "0.5h/w",
 "done_when": "支架到货并装好", "tasks": [{"title": "对比 3 款支架的承重与价格", "est": "20m"}, {"title": "下单", "est": "10m"}]}
JSON

on 2026-09-03 $CLI inbox add "想做一个个人网站"
on 2026-09-10 $CLI inbox add "年底前考个驾照？"

on 2026-09-02 $CLI log G02.T01 --result done --time 90m --evidence code --note "commit 3f2a1c 线框图提交到 docs/"
on 2026-09-03 $CLI log G03.T01 --result done --time 40m --evidence verbal
on 2026-09-04 $CLI log G02.T02 --result done --time 75m --evidence code --note "commit 8b7d02 SwiftUI+SwiftData 骨架"
on 2026-09-04 $CLI phase done G02.M1 --evidence code --note "线框图与骨架均已核验"
on 2026-09-05 $CLI log G04.T01 --result done --time 90m --evidence link --note "简历 v3 已上传云盘"
on 2026-09-05 $CLI phase done G04.M1 --evidence link
on 2026-09-05 $CLI log G03.T01 --result done --time 35m --evidence verbal
on 2026-09-06 $CLI log G05.T01 --result done --time 100m --evidence link --note "练习代码 rust-book/ch05"
on 2026-09-06 $CLI units G05 --done 5 --mastered 5 --evidence link
on 2026-09-06 $CLI log G03.T02 --result done --time 5m --evidence photo
on 2026-09-06 $CLI metric G03 77.2 --evidence photo --note "秤读数照片已查看"
on 2026-09-07 $CLI log G03.T01 --result done --time 40m --evidence verbal
on 2026-09-08 $CLI log G04.T02 --result skip --reason U --note "不知道该投哪些公司"
on 2026-09-09 $CLI log G02.T03 --result partial --time 60m --reason O --evidence code --note "commit c41e9a 模型层完成，UI 未接"
on 2026-09-09 $CLI log G03.T01 --result done --time 40m --evidence verbal
on 2026-09-10 $CLI log G04.T02 --result skip --reason U
on 2026-09-10 $CLI funnel G04 投递 +3 --evidence link --note "官网投递截图"
on 2026-09-10 $CLI log G02.T04 --result moved --reason T
on 2026-09-11 $CLI task set G02.T06 blocked --wait 小王
on 2026-09-11 $CLI log G06.T01 --result done --time 20m --evidence verbal
on 2026-09-12 $CLI log G02.T04 --result skip --reason U --note "不知道从哪开始比较"
on 2026-09-12 $CLI log G03.T01 --result done --time 40m --evidence verbal
on 2026-09-13 $CLI log G03.T02 --result done --time 5m --evidence photo
on 2026-09-13 $CLI metric G03 76.4 --evidence photo --note "秤读数照片已查看，未保存照片"
on 2026-09-13 $CLI funnel G04 初筛通过 +1 --evidence link --note "邮件通知"
on 2026-09-13 $CLI decide G02 "砍掉多币种支持" --reason "v1 聚焦核心记账" --revisit 2026-12-01

on 2026-09-14 $CLI plan --hours 4 --energy 3 --main G04.T02,G02.T04 --habit G03.T01 --errand G06.T02 --advice-file - <<'JSON' >/dev/null
[{"category": "adjust", "goal": "G04", "title": "投递节奏落后", "level": "L2",
  "facts": "近7天投递 3/10 家；G04.T02 推迟 2 次，原因都是 U（不清楚投哪家）",
  "judgment": "瓶颈是缺少目标公司清单，不是时间不够",
  "options": [{"label": "A", "text": "今天先花 45m 建清单，下周配额不变", "cost": "本周投递数再少 1-2 家"},
              {"label": "B", "text": "配额降到 6 家/周", "cost": "预计拿到 offer 的时间推迟约 2 周"}],
  "recommend": "A", "recommend_reason": "已排进今日主线", "ask": "回复 A 或 B"}]
JSON

on 2026-09-14 $CLI checkin \
  --item "G04.T02|done|50m||link|清单 22 家已存到 Notion" \
  --item "G02.T04|skip||U||还是不知道从哪比较" \
  --item "G03.T01|done|35m||verbal|" \
  --item "G06.T02|done|10m||verbal|已下单，周三到货" \
  --item "G02.T03|partial|60m|O|code|子代理核验 commit e19f55：列表页已接数据，编辑页未做" \
  --tomorrow "G02.T03,G04.T03" \
  --summary "今天效率不错，投递的心结解开了" \
  --advice-file - <<'JSON' >/dev/null
{"category": "coach", "goal": "G02", "title": "iCloud 同步调研卡住了", "level": "L2",
 "facts": "G02.T04 已推迟 3 次，其中 2 次原因是 U（不清楚从哪开始）",
 "judgment": "任务太模糊：「调研 3 种方案」没有明确的第一步和产出格式",
 "options": [{"label": "A", "text": "拆成两步：① 25m 列出 CloudKit/Core Data+CloudKit/第三方 3 个候选及官方文档链接 ② 30m 按“成本/复杂度/离线支持”填对比表", "cost": "多一次拆解，今天不增加工作量"},
             {"label": "B", "text": "v1 先不做同步，挪到 M3 之后", "cost": "上架时没有多设备同步，可能影响前 10 个用户的留存"}],
 "recommend": "A", "recommend_reason": "同步是核心体验，只是任务定义不清", "ask": "回复 A 或 B，我来更新计划"}
JSON
on 2026-09-14 $CLI metric G03 76.1 --evidence verbal --note "用户不方便拍照，口头报告" >/dev/null
