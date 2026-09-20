#!/usr/bin/env python3
"""Mishu regression tests: python3 -m unittest discover -s tests -v"""
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skill" / "mishu" / "scripts"
CLI = SCRIPTS / "mishu.py"
GUARD = SCRIPTS / "guard.py"
sys.path.insert(0, str(SCRIPTS))
import mishu  # noqa: E402
from i18n import ZH  # noqa: E402

PROJECT = {
    "title": "Test project", "type": "project", "area": "Career", "priority": "P1", "start": "2026-09-01",
    "deadline": "2026-10-31", "budget": "5h/w", "done_when": "Shipped", "why": "testing",
    "phases": [{"title": "Phase one", "due": "2026-09-20"}, {"title": "Phase two", "due": "2026-10-31"}],
    "tasks": [{"title": "Write code A", "est": "60m", "phase": "M1"}, {"title": "Write code B", "est": "30m", "phase": "M1"},
              {"title": "Write code C", "est": "45m", "phase": "M2"}],
}
HABIT = {
    "title": "Test habit", "type": "habit", "area": "Health", "priority": "P2", "start": "2026-09-01", "budget": "2h/w",
    "done_when": "Reach 70", "measure": {"metric": {"name": "Weight", "unit": "kg", "baseline": 80, "target": 70,
                                                  "current": 80, "direction": "down"},
                                       "frequency": {"task": "T01", "per_week": 3}},
    "tasks": [{"title": "Run", "est": "30m", "min": "10m"}],
}


ERRAND = {
    "title": "Buy a keyboard", "type": "errand", "area": "Life", "priority": "P3", "start": "2026-09-01",
    "deadline": "2026-09-25", "budget": "0.5h/w", "done_when": "Keyboard on my desk",
    "tasks": [{"title": "Compare 3 keyboards", "est": "30m"}, {"title": "Place the order", "est": "10m"}],
}


class Base(unittest.TestCase):
    LANG = "en"

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.vault = self.tmp / "vault"
        self.env = dict(os.environ, MISHU_CONFIG=str(self.tmp / "cfg" / "config.json"), MISHU_TODAY="2026-09-10")
        self.env.pop("MISHU_VAULT", None)
        self.run_cli("init", "--vault", str(self.vault), "--set-default", "--capacity", "20h", "--lang", self.LANG)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_cli(self, *args, stdin=None, ok=True, today=None):
        env = dict(self.env)
        if today:
            env["MISHU_TODAY"] = today
        r = subprocess.run([sys.executable, str(CLI), *args], input=stdin, capture_output=True, text=True, env=env)
        if ok and r.returncode != 0:
            self.fail(f"command failed {args}: {r.stdout}\n{r.stderr}")
        return r

    def add(self, data, today="2026-09-01"):
        return self.run_cli("add-goal", "--file", "-", stdin=json.dumps(data, ensure_ascii=False), today=today)

    def goal_file(self, gid):
        return next((self.vault / "goals").glob(f"{gid}-*.md"))


class TestYaml(unittest.TestCase):
    def test_roundtrip(self):
        meta = {"id": "G01", "title": "A title: with, punctuation", "deadline": "2026-11-30!", "budget": "8h/w",
                "verify": {"method": "repo", "repo": "~/code/x"},
                "measure": {"progress": "metric", "metric": {"name": "体重", "baseline": 78, "current": 76.4}},
                "phases": [{"id": "M1", "title": "Phase, one", "weight": 1, "status": "done"}],
                "areas": ["Career", "学习"], "empty": None, "flag": True, "num_str": "123"}
        self.assertEqual(mishu.yaml_load("\n".join(mishu.yaml_dump(meta))), meta)


class TestI18n(unittest.TestCase):
    def test_every_translatable_string_has_chinese(self):
        missing = []
        for f in ("mishu.py", "dashboard.py"):
            tree = ast.parse((SCRIPTS / f).read_text("utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and getattr(node.func, "id", None) in ("tr", "_t") and node.args:
                    a = node.args[0]
                    if isinstance(a, ast.Constant) and isinstance(a.value, str) and a.value not in ZH:
                        missing.append(a.value)
        vocab = [*mishu.TYPE_NAME.values(), *mishu.RESULTS.values(), *mishu.EVIDENCE.values(), *mishu.REASONS.values(),
                 *mishu.ADVICE_CATS.values(), *[v[1] for v in mishu.LIGHT_CLASS.values()]]
        missing += [k for k in vocab if k not in ZH]
        self.assertEqual(missing, [])

    def test_placeholders_match(self):
        for k, v in ZH.items():
            self.assertEqual(sorted(re.findall(r"\{(\w+)\}", k)), sorted(re.findall(r"\{(\w+)\}", v)), k)


class TestWriteRules(Base):
    def test_goal_file_roundtrip_is_stable(self):
        self.add(PROJECT)
        p = self.goal_file("G01")
        self.assertEqual(mishu.Goal.load(p).dump(), p.read_text("utf-8"))

    def test_structural_change_requires_confirmation(self):
        self.add(PROJECT)
        before = self.goal_file("G01").read_text("utf-8")
        r = self.run_cli("set", "G01", "deadline", "2026-12-31", ok=False)
        self.assertEqual(r.returncode, 3)
        self.assertEqual(self.goal_file("G01").read_text("utf-8"), before)
        self.run_cli("set", "G01", "deadline", "2026-12-31", "--confirmed", "--reason", "user agreed to extend")
        text = self.goal_file("G01").read_text("utf-8")
        self.assertIn("deadline: 2026-12-31", text)
        self.assertIn("| D01 | changed deadline", text)

    def test_done_requires_evidence_and_skip_requires_reason(self):
        self.add(PROJECT)
        self.assertIn("--evidence", self.run_cli("log", "G01.T01", "--result", "done", ok=False).stderr)
        self.assertIn("--reason", self.run_cli("log", "G01.T01", "--result", "skip", ok=False).stderr)
        self.run_cli("log", "G01.T01", "--result", "done", "--time", "60m", "--evidence", "verbal")
        self.assertIn("- [x] T01", self.goal_file("G01").read_text("utf-8"))

    def test_cancel_requires_confirmation(self):
        self.add(PROJECT)
        self.assertEqual(self.run_cli("task", "set", "G01.T02", "cancel", ok=False).returncode, 3)

    def test_task_over_two_hours_rejected(self):
        self.add(PROJECT)
        self.assertIn("2h", self.run_cli("task", "add", "G01", "Build a huge feature", "--est", "3h", ok=False).stderr)

    def test_readiness_and_capacity_gate(self):
        r = self.run_cli("add-goal", "--file", "-", stdin=json.dumps(dict(PROJECT, done_when="")), ok=False)
        self.assertEqual(r.returncode, 2)
        r = self.run_cli("add-goal", "--file", "-", stdin=json.dumps(dict(PROJECT, budget="17h/w")), ok=False)
        self.assertEqual(r.returncode, 3)
        self.assertFalse(list((self.vault / "goals").glob("G*.md")))

    def test_external_edit_detection(self):
        self.add(PROJECT)
        p = self.goal_file("G01")
        p.write_text(p.read_text("utf-8").replace("why: testing", "why: edited by hand"), "utf-8")
        self.assertIn("edited outside", self.run_cli("log", "G01.T01", "--result", "done", "--evidence", "verbal").stdout)
        p.write_text(p.read_text("utf-8").replace("type: project", "type: nonsense"), "utf-8")
        r = self.run_cli("log", "G01.T02", "--result", "done", "--evidence", "verbal", ok=False)
        self.assertEqual(r.returncode, 5)


class TestFirstRun(Base):
    def test_new_vault_is_empty_and_onboards(self):
        self.assertEqual(list((self.vault / "goals").glob("G*.md")), [])
        ctx = self.run_cli("context").stdout
        self.assertIn("vault is empty", ctx)
        html = (self.vault / "dashboard.html").read_text("utf-8")
        self.assertIn("Welcome to Mishu", html)
        self.assertIn("Your vault is empty", (self.vault / "BOARD.md").read_text("utf-8"))

    def test_context_without_vault_points_to_setup(self):
        env = dict(self.env, MISHU_CONFIG=str(self.tmp / "nothing" / "config.json"))
        r = subprocess.run([sys.executable, str(CLI), "context"], capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0)
        self.assertIn("NOT CONFIGURED", r.stdout)


class TestMetricsAndPlan(Base):
    def test_progress_and_pace(self):
        self.add(PROJECT)
        self.add(HABIT)
        self.run_cli("log", "G01.T01", "--result", "done", "--time", "60m", "--evidence", "code", today="2026-09-05")
        self.run_cli("metric", "G02", "76", "--evidence", "photo", today="2026-09-08")
        st = {d["gid"]: d for d in json.loads(self.run_cli("status", "--json").stdout)}
        self.assertAlmostEqual(st["G01"]["progress"], (60 / 90) / 2, places=3)
        self.assertAlmostEqual(st["G02"]["progress"], 0.4, places=3)
        self.assertEqual(st["G02"]["light"], "🔴")

    def test_plan_constraints(self):
        self.add(PROJECT)
        self.assertIn("exceeds the cap", self.run_cli("plan", "--hours", "1", "--energy", "3", "--main",
                                                      "G01.T01,G01.T02", ok=False).stderr)
        for _ in range(3):
            self.run_cli("log", "G01.T02", "--result", "skip", "--reason", "U")
        self.assertIn("deferred", self.run_cli("plan", "--hours", "4", "--energy", "3", "--main", "G01.T02", ok=False).stderr)
        self.assertIn("Needs breakdown", self.run_cli("candidates", "--hours", "4", "--energy", "3").stdout)

    def test_time_cap_has_no_float_rounding_error(self):
        self.add(PROJECT)
        self.assertIn("cap 2h6m", self.run_cli("candidates", "--hours", "3", "--energy", "3").stdout)

    def test_plan_and_checkin(self):
        self.add(PROJECT)
        self.add(HABIT)
        self.run_cli("plan", "--hours", "4", "--energy", "3", "--main", "G01.T01", "--habit", "G02.T01")
        self.assertIn("haven't been reviewed",
                      self.run_cli("checkin", "--item", "G01.T01|done|60m||code|commit abc", ok=False).stderr)
        self.run_cli("checkin", "--item", "G01.T01|done|60m||code|commit abc", "--item", "G02.T01|skip||E||")
        daily = (self.vault / "daily" / "2026-09-10.md").read_text("utf-8")
        self.assertIn("## 🌙 Evening check-in", daily)
        self.assertIn("| G01.T01 | ✓ | 1h |  | 🔍 | commit abc |", daily)
        self.assertIn("already done", self.run_cli("checkin", "--item", "G01.T01|done|60m||code|x", ok=False).stderr)

    def test_dashboard_html_is_generated_and_escaped(self):
        self.add(dict(PROJECT, title="<script>alert(1)</script> project"))
        self.run_cli("plan", "--hours", "4", "--energy", "3", "--main", "G01.T01")
        html = (self.vault / "dashboard.html").read_text("utf-8")
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt; project", html)
        self.assertNotIn("<script>alert(1)", html)
        self.assertIn("G01.T01", html)

    def test_advice_card_rules(self):
        card = {"category": "adjust", "goal": "global", "title": "t", "level": "L2", "facts": "f", "judgment": "j",
                "options": [{"label": "A", "text": "x"}], "recommend": "A", "ask": "reply A"}
        self.assertIn("cost", self.run_cli("advice", "--file", "-", stdin=json.dumps(card), ok=False).stderr)
        card["options"][0]["cost"] = "c"
        self.assertIn("A0910-1 [Adjust] global", self.run_cli("advice", "--file", "-", stdin=json.dumps(card)).stdout)


class TestFixes(Base):
    def test_candidates_keep_action_order_within_a_goal(self):
        self.add(ERRAND)
        c = json.loads(self.run_cli("candidates", "--hours", "0.5", "--energy", "3", "--json").stdout)
        picks = {i["ref"]: bool(i.get("pick")) for i in c["errand"]}
        self.assertFalse(picks["G01.T01"])          # 30m doesn't fit into the 21m cap…
        self.assertFalse(picks["G01.T02"])          # …so "place the order" must not jump ahead of it
        later = next(i for i in c["errand"] if i["ref"] == "G01.T02")
        self.assertIn("after G01.T01", later["why"])
        c = json.loads(self.run_cli("candidates", "--hours", "1", "--energy", "3", "--json").stdout)
        self.assertTrue(all(i.get("pick") for i in c["errand"]))

    def test_inbox_renumbering_is_shown(self):
        self.run_cli("inbox", "add", "first")
        self.run_cli("inbox", "add", "second")
        out = self.run_cli("inbox", "done", "--n", "1").stdout
        self.assertIn("1. ", out)
        self.assertIn("second", out)


class TestDashboardUI(Base):
    """The dashboard is a view: it shows today's main items, and its ticks never reach the vault."""

    def html(self):
        return (self.vault / "dashboard.html").read_text("utf-8")

    def test_today_shows_main_items_only_with_checkboxes(self):
        self.add(PROJECT)
        self.add(HABIT)
        self.run_cli("plan", "--hours", "4", "--energy", "3", "--main", "G01.T01", "--habit", "G02.T01")
        html = self.html()
        today = html[html.index('class="today'):html.index('<section class="goals')]
        self.assertIn('data-scope="day" data-ref="G01.T01"', today)
        self.assertNotIn("G02.T01", today)            # habits stay in the daily file
        self.assertNotIn("Evening check-in", today)
        self.assertIn("Run", (self.vault / "daily" / "2026-09-10.md").read_text("utf-8"))

    def test_goal_details_drop_evidence_and_number_actions(self):
        self.add(PROJECT)
        html = self.html()
        self.assertNotIn("Evidence", html)
        self.assertNotIn(">T01<", html)               # actions are numbered, not called T01
        self.assertIn('<span class="n mono">1.</span>', html)
        self.assertIn('data-scope="task" data-ref="G01.T01"', html)

    def test_advice_options_are_selectable(self):
        self.add(PROJECT)
        card = {"category": "adjust", "goal": "G01", "title": "Behind pace", "level": "L2", "facts": "f",
                "judgment": "j", "options": [{"label": "A", "text": "Cut scope", "cost": "less"},
                                             {"label": "B", "text": "Extend", "cost": "later"}],
                "recommend": "A", "ask": "Reply A or B"}
        self.run_cli("plan", "--hours", "4", "--energy", "3", "--main", "G01.T01",
                     "--advice-file", "-", stdin=json.dumps([card]))
        html = self.html()
        self.assertIn('class="pick"', html)
        self.assertIn("I pick A — Cut scope", html)
        self.assertIn('class="adv-reply"', html)

    def test_dashboard_is_the_only_place_ticks_live(self):
        self.add(PROJECT)
        self.run_cli("plan", "--hours", "4", "--energy", "3", "--main", "G01.T01")
        self.assertIn("localStorage", self.html())
        self.assertNotIn("checked", (self.vault / "goals" / "G01-test-project.md").read_text("utf-8"))


class TestCompleted(Base):
    def finish_errand(self):
        self.add(ERRAND)
        self.run_cli("log", "G01.T01", "--result", "done", "--time", "30m", "--evidence", "verbal", today="2026-09-05")
        self.run_cli("log", "G01.T02", "--result", "done", "--time", "10m", "--evidence", "verbal", today="2026-09-06")
        self.run_cli("set", "G01", "status", "done", "--confirmed", "--reason", "keyboard arrived", today="2026-09-08")

    def test_done_goal_is_stamped_archived_and_listed(self):
        self.finish_errand()
        archived = next((self.vault / "goals" / "_archive").glob("G01-*.md")).read_text("utf-8")
        self.assertIn("completed: 2026-09-08", archived)
        out = self.run_cli("done").stdout
        self.assertIn("G01", out)
        self.assertIn("09-01 → 09-08 · 8 days · spent 40m · 2 actions done", out)
        self.assertIn("Closing note: keyboard arrived", out)
        data = json.loads(self.run_cli("done", "--json").stdout)
        self.assertEqual(data[0]["completed"], "2026-09-08")

    def test_completed_goals_on_board_and_dashboard(self):
        self.finish_errand()
        self.run_cli("board")
        board = (self.vault / "BOARD.md").read_text("utf-8")
        self.assertIn("## ✅ Completed", board)
        self.assertIn("✅ G01 📦 Buy a keyboard", board)
        html = (self.vault / "dashboard.html").read_text("utf-8")
        self.assertIn('class="completed box-panel"', html)
        self.assertIn("Keyboard on my desk", html)

    def test_reopening_clears_completion_date(self):
        self.finish_errand()
        self.run_cli("task", "add", "G01", "Buy a wrist rest", "--est", "15m", today="2026-09-09")
        self.run_cli("set", "G01", "status", "active", "--confirmed", "--reason", "one more thing", today="2026-09-09")
        self.assertNotIn("completed:", self.goal_file("G01").read_text("utf-8"))


class TestChinese(Base):
    LANG = "zh"

    def test_chinese_advice_card_has_no_stray_space(self):
        card = {"category": "adjust", "goal": "全局", "title": "测试", "level": "L2", "facts": "f", "judgment": "j",
                "options": [{"label": "A", "text": "方案", "cost": "少一点"}], "recommend": "A", "ask": "回复 A"}
        out = self.run_cli("advice", "--file", "-", stdin=json.dumps(card, ensure_ascii=False)).stdout
        self.assertIn("代价：少一点", out)
        self.assertIn("需要你", out)

    def test_outputs_follow_vault_language(self):
        self.add(dict(PROJECT, title="测试项目", area="事业"))
        text = self.goal_file("G01").read_text("utf-8")
        self.assertIn("## 行动", text)
        self.run_cli("plan", "--hours", "4", "--energy", "3", "--main", "G01.T01")
        self.run_cli("checkin", "--item", "G01.T01|partial|30m|O|verbal|做了一半")
        daily = (self.vault / "daily" / "2026-09-10.md").read_text("utf-8")
        self.assertIn("## 🎯 主线（最多 3 项）", daily)
        self.assertIn("## 🌙 晚间回顾", daily)
        self.assertIn("# 📊 秘书看板", (self.vault / "BOARD.md").read_text("utf-8"))
        self.assertIn("秘书台", (self.vault / "dashboard.html").read_text("utf-8"))
        r = self.run_cli("set", "G01", "deadline", "2026-12-31", ok=False)
        self.assertIn("结构性修改", r.stderr)

    def test_chinese_files_parse_after_language_switch(self):
        self.add(dict(PROJECT, title="测试项目"))
        self.run_cli("decide", "G01", "砍掉多币种", "--reason", "聚焦")
        self.run_cli("profile", "set", "lang", "en", "--confirmed", "--reason", "switch")
        self.run_cli("log", "G01.T01", "--result", "done", "--evidence", "verbal")
        text = self.goal_file("G01").read_text("utf-8")
        self.assertIn("## Actions", text)
        self.assertIn("Reason: 聚焦", text)


class TestGuard(Base):
    def guard(self, tool, tool_input, dev=False):
        flag = self.tmp / "cfg" / "dev_mode"
        if dev:
            flag.write_text("1")
        elif flag.exists():
            flag.unlink()
        payload = {"tool_name": tool, "tool_input": tool_input, "cwd": str(self.tmp)}
        return subprocess.run([sys.executable, str(GUARD)], input=json.dumps(payload), capture_output=True,
                              text=True, env=self.env)

    def test_blocks_direct_vault_writes(self):
        self.assertEqual(self.guard("Write", {"file_path": str(self.vault / "BOARD.md")}).returncode, 2)
        self.assertEqual(self.guard("Edit", {"file_path": str(self.vault / "goals" / "G01-x.md")}).returncode, 2)
        self.assertEqual(self.guard("Bash", {"command": f"echo hi > {self.vault}/BOARD.md"}).returncode, 2)
        self.assertEqual(self.guard("Bash", {"command": f"sed -i '' 's/a/b/' {self.vault}/goals/G01.md"}).returncode, 2)
        self.assertEqual(self.guard("Bash", {"command": f"rm -rf {self.vault}/daily"}).returncode, 2)

    def test_allows_reads_and_the_cli(self):
        self.assertEqual(self.guard("Bash", {"command": f"cat {self.vault}/BOARD.md"}).returncode, 0)
        cmd = f"python3 {CLI} checkin --item 'G01.T01|done|60m||code|x' 2>/dev/null"
        self.assertEqual(self.guard("Bash", {"command": cmd}).returncode, 0)
        self.assertEqual(self.guard("Write", {"file_path": str(self.tmp / "other.txt")}).returncode, 0)

    def test_skill_dir_protected_unless_dev_mode(self):
        target = {"file_path": str(CLI)}
        self.assertEqual(self.guard("Edit", target).returncode, 2)
        self.assertEqual(self.guard("Edit", target, dev=True).returncode, 0)
        self.assertEqual(self.guard("Write", {"file_path": str(self.vault / "x.md")}, dev=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
