"""命令行入口：python -m src.cli data/matches.csv"""

from __future__ import annotations

import argparse
import sys

from .analyzer import format_report, load_matches


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="football-stats",
        description="统计足球队比赛数据（胜平负、胜率、进失球、连胜、分组汇总）。",
    )
    parser.add_argument("csv_path", help="比赛记录 CSV 路径，例如 data/matches.csv")
    parser.add_argument(
        "--no-detail",
        action="store_true",
        help="只输出汇总，不打印逐场记录",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="把报告写入文件（默认打印到屏幕）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        matches = load_matches(args.csv_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 1

    report = format_report(matches, source=args.csv_path)
    if args.no_detail:
        report = report.split("逐场记录")[0].rstrip() + "\n"

    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(report)
        print(f"报告已写入 {args.output}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
