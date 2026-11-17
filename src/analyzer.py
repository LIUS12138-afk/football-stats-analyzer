"""足球队比赛数据统计核心逻辑。

只依赖 Python 标准库，负责：
1. 从 CSV 读取比赛记录并校验；
2. 计算胜平负、胜率、进失球、连胜等指标；
3. 按赛事 / 月份 / 对手分组汇总；
4. 生成纯文本报告。
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable, Sequence

WIN = "W"
DRAW = "D"
LOSS = "L"

RESULT_TEXT = {WIN: "胜", DRAW: "平", LOSS: "负"}

REQUIRED_COLUMNS = ("date", "opponent", "goals_for", "goals_against")


@dataclass(frozen=True)
class Match:
    """一场比赛。"""

    date: date
    opponent: str
    goals_for: int
    goals_against: int
    competition: str = "友谊赛"

    @property
    def result(self) -> str:
        """返回 W / D / L。"""
        if self.goals_for > self.goals_against:
            return WIN
        if self.goals_for < self.goals_against:
            return LOSS
        return DRAW

    @property
    def goal_diff(self) -> int:
        return self.goals_for - self.goals_against


def load_matches(path: str | Path) -> list[Match]:
    """从 CSV 读取比赛记录，按日期升序返回。

    文件需包含表头：date,opponent,goals_for,goals_against，可选 competition。
    列名缺失或某行数据非法时抛出 ValueError，并带上行号。
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"找不到文件：{path}")

    matches: list[Match] = []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        missing = [c for c in REQUIRED_COLUMNS if c not in header]
        if missing:
            raise ValueError(f"表头缺少列：{', '.join(missing)}")

        for line_no, row in enumerate(reader, start=2):
            try:
                played_on = date.fromisoformat((row["date"] or "").strip())
                opponent = (row["opponent"] or "").strip()
                if not opponent:
                    raise ValueError("对手名不能为空")
                goals_for = _parse_goals(row["goals_for"], "goals_for")
                goals_against = _parse_goals(row["goals_against"], "goals_against")
                competition = (row.get("competition") or "").strip() or "友谊赛"
            except ValueError as exc:
                raise ValueError(f"第 {line_no} 行数据有误：{exc}") from exc
            matches.append(
                Match(
                    date=played_on,
                    opponent=opponent,
                    goals_for=goals_for,
                    goals_against=goals_against,
                    competition=competition,
                )
            )

    if not matches:
        raise ValueError(f"{path} 里没有任何比赛记录")

    matches.sort(key=lambda m: (m.date, m.opponent))
    return matches


def _parse_goals(raw: str | None, column: str) -> int:
    text = (raw or "").strip()
    if not text:
        raise ValueError(f"{column} 不能为空")
    try:
        value = int(text)
    except ValueError:
        raise ValueError(f"{column} 必须是整数，当前是 {text!r}") from None
    if value < 0:
        raise ValueError(f"{column} 不能为负数")
    return value


def results_streak(matches: Sequence[Match], wanted: str = WIN) -> int:
    """最长连续 wanted 结果的场次数（默认最长连胜）。"""
    best = current = 0
    for match in matches:
        if match.result == wanted:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def summarize(matches: Iterable[Match]) -> dict:
    """整体汇总。空列表也返回结构完整的结果（各项为 0）。"""
    matches = list(matches)
    played = len(matches)
    wins = sum(1 for m in matches if m.result == WIN)
    draws = sum(1 for m in matches if m.result == DRAW)
    losses = sum(1 for m in matches if m.result == LOSS)
    goals_for = sum(m.goals_for for m in matches)
    goals_against = sum(m.goals_against for m in matches)

    return {
        "played": played,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "win_rate": (wins / played * 100) if played else 0.0,
        "goals_for": goals_for,
        "goals_against": goals_against,
        "goal_diff": goals_for - goals_against,
        "avg_goals_for": (goals_for / played) if played else 0.0,
        "avg_goals_against": (goals_against / played) if played else 0.0,
        "longest_win_streak": results_streak(matches, WIN),
        "longest_unbeaten": _longest_unbeaten(matches),
        "first_date": matches[0].date if played else None,
        "last_date": matches[-1].date if played else None,
    }


def _longest_unbeaten(matches: Sequence[Match]) -> int:
    best = current = 0
    for match in matches:
        if match.result != LOSS:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def group_by(matches: Iterable[Match], key: str) -> dict[str, dict]:
    """按 competition / opponent / month 分组，返回 {分组名: 汇总}。"""
    matches = list(matches)
    groups: dict[str, list[Match]] = defaultdict(list)
    for match in matches:
        if key == "competition":
            name = match.competition
        elif key == "opponent":
            name = match.opponent
        elif key == "month":
            name = match.date.strftime("%Y-%m")
        else:
            raise ValueError(f"不支持的分组方式：{key}")
        groups[name].append(match)
    return {name: summarize(items) for name, items in groups.items()}


def format_report(matches: Sequence[Match], source: str = "") -> str:
    """生成给人看的纯文本报告。"""
    stats = summarize(matches)
    lines: list[str] = []
    lines.append("=" * 46)
    lines.append("足球队比赛数据报告")
    lines.append("=" * 46)
    if source:
        lines.append(f"数据来源：{source}")
    if stats["first_date"]:
        lines.append(f"统计区间：{stats['first_date']} ~ {stats['last_date']}")
    lines.append("")
    lines.append(f"总场次      {stats['played']}")
    lines.append(
        f"战绩        {stats['wins']} 胜 {stats['draws']} 平 {stats['losses']} 负"
    )
    lines.append(f"胜率        {stats['win_rate']:.1f}%")
    lines.append(
        f"进球/失球   {stats['goals_for']} / {stats['goals_against']}"
        f"   (净胜 {stats['goal_diff']:+d})"
    )
    lines.append(f"场均进球    {stats['avg_goals_for']:.2f}")
    lines.append(f"场均失球    {stats['avg_goals_against']:.2f}")
    lines.append(f"最长连胜    {stats['longest_win_streak']} 场")
    lines.append(f"最长不败    {stats['longest_unbeaten']} 场")

    for title, key in (("按赛事", "competition"), ("按月份", "month"), ("按对手", "opponent")):
        grouped = group_by(matches, key)
        lines.append("")
        lines.append(f"{title}（{len(grouped)} 个）")
        for name in sorted(grouped):
            item = grouped[name]
            lines.append(
                f"  {name:<12} {item['played']:>2} 场  "
                f"{item['wins']}胜{item['draws']}平{item['losses']}负  "
                f"胜率 {item['win_rate']:>5.1f}%  "
                f"净胜 {item['goal_diff']:+d}"
            )

    lines.append("")
    lines.append("逐场记录")
    for match in matches:
        lines.append(
            f"  {match.date}  {match.opponent:<12} "
            f"{match.goals_for}-{match.goals_against}  "
            f"{RESULT_TEXT[match.result]}  [{match.competition}]"
        )
    lines.append("")
    return "\n".join(lines)
