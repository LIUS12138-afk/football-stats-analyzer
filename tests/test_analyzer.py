"""单元测试：python -m unittest discover -s tests -v"""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.analyzer import (  # noqa: E402
    Match,
    format_report,
    group_by,
    load_matches,
    results_streak,
    summarize,
)


def m(day: str, gf: int, ga: int, competition: str = "联赛", opponent: str = "对手") -> Match:
    return Match(
        date=date.fromisoformat(day),
        opponent=opponent,
        goals_for=gf,
        goals_against=ga,
        competition=competition,
    )


class MatchTest(unittest.TestCase):
    def test_result_win(self):
        self.assertEqual(m("2026-09-01", 2, 1).result, "W")

    def test_result_draw(self):
        self.assertEqual(m("2026-09-01", 1, 1).result, "D")

    def test_result_loss(self):
        self.assertEqual(m("2026-09-01", 0, 3).result, "L")

    def test_goal_diff(self):
        self.assertEqual(m("2026-09-01", 3, 1).goal_diff, 2)


class SummarizeTest(unittest.TestCase):
    def setUp(self):
        self.matches = [
            m("2026-08-01", 2, 1),
            m("2026-08-08", 1, 1),
            m("2026-08-15", 0, 2),
            m("2026-08-22", 3, 0),
            m("2026-08-29", 2, 0),
        ]

    def test_counts(self):
        s = summarize(self.matches)
        self.assertEqual((s["played"], s["wins"], s["draws"], s["losses"]), (5, 3, 1, 1))

    def test_win_rate(self):
        self.assertAlmostEqual(summarize(self.matches)["win_rate"], 60.0, places=6)

    def test_goals(self):
        s = summarize(self.matches)
        self.assertEqual(s["goals_for"], 8)
        self.assertEqual(s["goals_against"], 4)
        self.assertEqual(s["goal_diff"], 4)

    def test_averages(self):
        s = summarize(self.matches)
        self.assertAlmostEqual(s["avg_goals_for"], 1.6, places=6)
        self.assertAlmostEqual(s["avg_goals_against"], 0.8, places=6)

    def test_longest_win_streak(self):
        self.assertEqual(summarize(self.matches)["longest_win_streak"], 2)

    def test_longest_unbeaten(self):
        # 序列为 胜-平-负-胜-胜，最长不丢分连段是 2 场
        self.assertEqual(summarize(self.matches)["longest_unbeaten"], 2)

    def test_empty(self):
        s = summarize([])
        self.assertEqual(s["played"], 0)
        self.assertEqual(s["win_rate"], 0.0)
        self.assertEqual(s["goals_for"], 0)
        self.assertIsNone(s["first_date"])


class StreakTest(unittest.TestCase):
    def test_all_wins(self):
        self.assertEqual(results_streak([m("2026-01-01", 1, 0)] * 3), 3)

    def test_no_win(self):
        self.assertEqual(results_streak([m("2026-01-01", 0, 1)]), 0)

    def test_loss_streak(self):
        seq = [m("2026-01-01", 0, 1), m("2026-01-02", 0, 2), m("2026-01-03", 1, 0)]
        self.assertEqual(results_streak(seq, "L"), 2)


class GroupTest(unittest.TestCase):
    def test_group_by_competition(self):
        matches = [m("2026-08-01", 1, 0, "联赛"), m("2026-08-02", 0, 1, "联赛"), m("2026-08-03", 2, 0, "杯赛")]
        grouped = group_by(matches, "competition")
        self.assertEqual(set(grouped), {"联赛", "杯赛"})
        self.assertEqual(grouped["联赛"]["played"], 2)
        self.assertEqual(grouped["杯赛"]["win_rate"], 100.0)

    def test_group_by_month(self):
        matches = [m("2026-08-01", 1, 0), m("2026-09-01", 1, 1)]
        self.assertEqual(sorted(group_by(matches, "month")), ["2026-08", "2026-09"])

    def test_group_by_unknown_key(self):
        with self.assertRaises(ValueError):
            group_by([m("2026-08-01", 1, 0)], "coach")


class LoadMatchesTest(unittest.TestCase):
    def _write(self, content: str) -> Path:
        tmp = Path(tempfile.mkdtemp()) / "matches.csv"
        tmp.write_text(content, encoding="utf-8")
        return tmp

    def test_load_and_sort(self):
        path = self._write(
            "date,opponent,goals_for,goals_against,competition\n"
            "2026-09-01,B队,2,1,杯赛\n"
            "2026-08-01,A队,1,0,联赛\n"
        )
        matches = load_matches(path)
        self.assertEqual([x.opponent for x in matches], ["A队", "B队"])
        self.assertEqual(matches[0].competition, "联赛")

    def test_default_competition(self):
        path = self._write(
            "date,opponent,goals_for,goals_against\n2026-08-01,A队,1,0\n"
        )
        self.assertEqual(load_matches(path)[0].competition, "友谊赛")

    def test_bom_and_quotes(self):
        tmp = Path(tempfile.mkdtemp()) / "bom.csv"
        tmp.write_text(
            "date,opponent,goals_for,goals_against\n2026-08-01,\"A, B队\",2,1\n",
            encoding="utf-8-sig",
        )
        self.assertEqual(load_matches(tmp)[0].opponent, "A, B队")

    def test_missing_column(self):
        path = self._write("date,opponent,goals_for\n2026-08-01,A队,1\n")
        with self.assertRaises(ValueError) as ctx:
            load_matches(path)
        self.assertIn("goals_against", str(ctx.exception))

    def test_bad_number_reports_line(self):
        path = self._write(
            "date,opponent,goals_for,goals_against\n"
            "2026-08-01,A队,1,0\n"
            "2026-08-02,B队,两个,0\n"
        )
        with self.assertRaises(ValueError) as ctx:
            load_matches(path)
        self.assertIn("第 3 行", str(ctx.exception))

    def test_negative_goals(self):
        path = self._write("date,opponent,goals_for,goals_against\n2026-08-01,A队,-1,0\n")
        with self.assertRaises(ValueError):
            load_matches(path)

    def test_empty_file(self):
        path = self._write("date,opponent,goals_for,goals_against\n")
        with self.assertRaises(ValueError):
            load_matches(path)

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            load_matches(Path(tempfile.mkdtemp()) / "不存在.csv")

    def test_bad_date(self):
        path = self._write("date,opponent,goals_for,goals_against\n2026-13-40,A队,1,0\n")
        with self.assertRaises(ValueError):
            load_matches(path)


class ReportTest(unittest.TestCase):
    def test_report_contains_key_sections(self):
        report = format_report([m("2026-08-01", 2, 1), m("2026-08-08", 0, 1)], source="demo.csv")
        for text in ("胜率", "最长连胜", "按赛事", "逐场记录", "demo.csv"):
            self.assertIn(text, report)

    def test_sample_data_file(self):
        sample = Path(__file__).resolve().parent.parent / "data" / "matches.csv"
        if not sample.exists():
            self.skipTest("样例数据缺失")
        matches = load_matches(sample)
        stats = summarize(matches)
        self.assertEqual(stats["played"], 12)
        self.assertEqual((stats["wins"], stats["draws"], stats["losses"]), (8, 2, 2))
        self.assertEqual(stats["goals_for"], 24)
        self.assertEqual(stats["goal_diff"], 13)


if __name__ == "__main__":
    unittest.main()
