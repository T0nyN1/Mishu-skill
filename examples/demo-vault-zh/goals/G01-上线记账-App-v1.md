---
id: G01
title: 上线记账 App v1
type: project
area: 事业
priority: P1
status: active
created: 2026-09-01
start: 2026-09-01
deadline: 2026-11-30!
why: 作品集 + 验证独立开发能力
done_when: App Store 上架，且有 10 个真实用户在用
budget: 8h/w
review: weekly
verify:
  method: repo
  repo: ~/code/ledger-app
  when: every
  fallback: verbal
measure:
  progress: phases
  pace: timeline
phases:
  - {id: M1, title: 需求与原型, weight: 1, due: 2026-09-10, status: done}
  - {id: M2, title: 核心记账功能, weight: 2, due: 2026-10-20, status: active}
  - {id: M3, title: 打磨与上架, weight: 1, due: 2026-11-30, status: todo}
---

## 行动
- [x] T01 画出 5 个核心页面线框图 · 90m · M1
- [x] T02 确定技术栈并搭建项目骨架 · 60m · M1
- [/] T03 实现账目 CRUD 本地存储 · 120m · M2
- [ ] T04 调研 3 种 iCloud 同步方案并写对比表 · 45m · M2 · defer:3
- [ ] T05 设计分类与标签数据结构 · 60m · M2
- [!] T06 请设计朋友出 App 图标 · 15m · M2 · wait:小王 · since:2026-09-11

## 日志
- 2026-09-01 | 创建 | = |  | ⚙️ | 目标创建（active）
- 2026-09-02 | T01 | ✓ | 1h30m | 🔍 | commit 3f2a1c 线框图提交到 docs/
- 2026-09-04 | T02 | ✓ | 1h15m | 🔍 | commit 8b7d02 SwiftUI+SwiftData 骨架
- 2026-09-04 | M1 | ✓ |  | 🔍 | 线框图与骨架均已核验
- 2026-09-09 | T03 | ◐ | 1h | 🔍 | [O] commit c41e9a 模型层完成，UI 未接
- 2026-09-10 | T04 | ➜ |  |  | [T]
- 2026-09-12 | T04 | ✗ |  |  | [U] 不知道从哪开始比较
- 2026-09-14 | T04 | ✗ |  |  | [U] 还是不知道从哪比较
- 2026-09-14 | T03 | ◐ | 1h | 🔍 | [O] 子代理核验 commit e19f55：列表页已接数据，编辑页未做

## 决策
- 2026-09-13 | D01 | 砍掉多币种支持 | 原因：v1 聚焦核心记账 | 回看：2026-12-01
