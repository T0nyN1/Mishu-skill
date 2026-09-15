---
id: G04
title: 拿到秋招 offer
type: pipeline
area: 事业
priority: P0
status: active
created: 2026-09-01
start: 2026-09-01
deadline: 2026-11-15!
why: 毕业后进入大厂做客户端开发
done_when: 拿到至少 1 个客户端开发 offer 并签约
budget: 5h/w
review: weekly
verify:
  method: link
  when: metric
  fallback: verbal
measure:
  progress: phases
  pace: frequency
  funnel:
    - {stage: 投递, count: 3}
    - {stage: 初筛通过, count: 1}
    - {stage: 面试, count: 0}
    - {stage: offer, count: 0, target: 1}
  frequency: {stage: 投递, per_week: 10, unit: 家}
phases:
  - {id: M1, title: 简历打磨, weight: 1, due: 2026-09-07, status: done}
  - {id: M2, title: 集中投递, weight: 2, due: 2026-10-15, status: active}
  - {id: M3, title: 面试, weight: 2, due: 2026-11-10, status: todo}
  - {id: M4, title: 选择 offer, weight: 1, due: 2026-11-15, status: todo}
---

## 行动
- [x] T01 按 JD 改写简历项目经历 · 90m · M1
- [x] T02 整理目标公司清单（20 家） · 45m · M2 · defer:2
- [ ] T03 投递 5 家目标公司 · 45m · M2
- [ ] T04 准备 5 个 STAR 行为面试故事 · 60m · M3

## 日志
- 2026-09-01 | 创建 | = |  | ⚙️ | 目标创建（active）
- 2026-09-05 | T01 | ✓ | 1h30m | 🔗 | 简历 v3 已上传云盘
- 2026-09-05 | M1 | ✓ |  | 🔗 | 阶段完成
- 2026-09-08 | T02 | ✗ |  |  | [U] 不知道该投哪些公司
- 2026-09-10 | T02 | ✗ |  |  | [U]
- 2026-09-10 | 漏斗:投递 | = | +3 | 🔗 | 官网投递截图
- 2026-09-13 | 漏斗:初筛通过 | = | +1 | 🔗 | 邮件通知
- 2026-09-14 | T02 | ✓ | 50m | 🔗 | 清单 22 家已存到 Notion

## 决策
