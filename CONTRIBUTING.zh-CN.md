# 贡献指南

[English](CONTRIBUTING.md) · **简体中文**

感谢你愿意改进 Mishu！

## 开发环境

- Python 3.9+。**不引入第三方依赖**：`mishu.py`、`i18n.py`、`dashboard.py`、`guard.py` 只使用标准库。
- 动手修改前，先跑一遍测试，确认现有测试全部通过：
  ```bash
  python3 -m unittest discover -s tests -v
  ```
- 如果要在已经调用过 `/mishu` 的 Claude Code 会话里修改 skill，需要先开启开发模式：`touch ~/.config/mishu/dev_mode`。

## 设计原则（提交前请对照）

1. **Markdown 是唯一数据源。** 新功能不能引入第二份状态，网页看板保持只读。
2. **数字由脚本算，判断由 AI 做。** 能用确定性规则表达的约束，要写进 `mishu.py`，不能只写在提示词里。
3. **格式统一。** 新增的输出必须使用范式规范（[中文](docs/zh-CN/paradigm-spec.md) / [EN](docs/en/paradigm-spec.md)）里的词汇表和固定区块。修改规范时，要同时更新两种语言的版本和 `skill/mishu/references/vocabulary.md`。
4. **始终双语。** 所有面向用户的文字都要通过 `tr()`（网页看板里用 `_t()`）输出：代码里写英文原文，并在 `i18n.py` 中补上中文。缺少翻译时 `tests/test_mishu.py` 会报错。
5. **写入权限不能放松。** 结构级修改必须带 `--confirmed --reason`，并自动记录一条决策；日志只能追加。
6. **尊重用户。** 请求证据时要给用户留退路，不唠叨、不说教；照片默认不保存。
7. **首次使用必须是空库。** `examples/` 里的内容不能进入用户的档案库。

## 提交改动

- 修改了 `mishu.py` 的行为，请在 `tests/test_mishu.py` 中补充测试。
- 修改了渲染逻辑，请运行 `bash examples/build_demo.sh` 重新生成演示档案库，并一起提交。
- 界面变化较大时，请更新 `docs/images/` 中的截图。
- 在 `CHANGELOG.md` 的 "Unreleased" 一节写上改动说明。
