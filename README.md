# football-stats-analyzer

![CI](https://github.com/LIUS12138-afk/football-stats-analyzer/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)

一个用 Python 标准库写的**足球队比赛数据统计工具**：把每场比赛记录成一行 CSV，一条命令输出胜平负、胜率、进失球、连胜/不败纪录，以及按赛事、按月、按对手的分组汇总。

零第三方依赖，克隆下来就能跑，适合球队日常复盘，也可以作为 Python 入门项目的脚手架。

## 它能回答什么问题

- 这赛季一共踢了几场，几胜几平几负，胜率多少？
- 场均进球、场均失球、净胜球是多少？
- 最长连胜、最长不败分别是几场？
- 联赛和杯赛的表现差距有多大？
- 跟哪个对手一直踢不过？
- 每个月的状态是升还是降？

## 快速开始

```bash
git clone https://github.com/LIUS12138-afk/football-stats-analyzer.git
cd football-stats-analyzer

# 用自带的 12 场样例数据跑一遍
python -m src.cli data/matches.csv
```

也可以把报告写进文件：

```bash
python -m src.cli data/matches.csv --output report.txt
python -m src.cli data/matches.csv --no-detail   # 只看汇总，不打印逐场
```

## 输出示例

```text
==============================================
足球队比赛数据报告
==============================================
数据来源：data/matches.csv
统计区间：2026-08-15 ~ 2026-11-14

总场次      12
战绩        8 胜 2 平 2 负
胜率        66.7%
进球/失球   24 / 11   (净胜 +13)
场均进球    2.00
场均失球    0.92
最长连胜    3 场
最长不败    5 场

按赛事（3 个）
  友谊赛           2 场  2胜0平0负  胜率 100.0%  净胜 +3
  杯赛            3 场  1胜1平1负  胜率  33.3%  净胜 +1
  联赛            7 场  5胜1平1负  胜率  71.4%  净胜 +9

按月份（4 个）
  2026-08       3 场  2胜1平0负  胜率  66.7%  净胜 +4
  2026-09       4 场  3胜0平1负  胜率  75.0%  净胜 +4
  2026-10       4 场  2胜1平1负  胜率  50.0%  净胜 +3
  2026-11       1 场  1胜0平0负  胜率 100.0%  净胜 +2

逐场记录
  2026-08-15  海大FC         2-1  胜  [联赛]
  2026-08-22  青岛理工         1-1  平  [联赛]
  ...
```

## 数据格式

在 `data/matches.csv` 里一行一场比赛，第一行是表头，**UTF-8 编码**（带不带 BOM 都能读）：

```csv
date,opponent,goals_for,goals_against,competition
2026-08-15,海大FC,2,1,联赛
2026-08-22,青岛理工,1,1,联赛
```

| 列 | 必填 | 说明 |
| --- | --- | --- |
| `date` | 是 | 比赛日期，`YYYY-MM-DD` |
| `opponent` | 是 | 对手名称，不能为空 |
| `goals_for` | 是 | 我方进球，非负整数 |
| `goals_against` | 是 | 对方进球，非负整数 |
| `competition` | 否 | 赛事名称，留空按「友谊赛」处理 |

读入时会做校验：缺列、日期写错、进球写成非数字、或者填了负数，都会直接报错并告诉你**是第几行**：

```text
[错误] 第 3 行数据有误：goals_for 必须是整数，当前是 '两个'
```

## 在代码里用

```python
from src.analyzer import load_matches, summarize, group_by, format_report

matches = load_matches("data/matches.csv")

stats = summarize(matches)
print(stats["win_rate"])            # 66.66...
print(stats["longest_win_streak"])  # 3

league = group_by(matches, "competition")["联赛"]
print(league["goal_diff"])          # 9

print(format_report(matches, source="data/matches.csv"))
```

## 项目结构

```text
football-stats-analyzer/
├── .github/workflows/ci.yml   # GitHub Actions：3 个 Python 版本上跑测试
├── data/matches.csv           # 样例数据（12 场）
├── src/
│   ├── analyzer.py            # 核心逻辑：读取、校验、统计、报表
│   └── cli.py                 # 命令行入口
├── tests/test_analyzer.py     # 28 个单元测试（标准库 unittest）
├── requirements.txt           # 运行零依赖；只在这里说明
├── LICENSE                    # MIT
└── README.md
```

## 测试与 CI

```bash
python -m unittest discover -s tests -v
```

当前 28 个用例覆盖：胜平负判定、净胜球、胜率与场均、连胜/不败 streak、按赛事/月份分组、非法数据报错（缺列、坏数字、负数、坏日期、空文件、文件不存在），以及样例数据的整体数值校验。

每次 `push` 到 `main` 或提交 Pull Request，GitHub Actions 会在 Python 3.9 / 3.11 / 3.13 上自动跑一遍测试，并额外执行一次 CLI 冒烟测试。

## 待办 / 可以接着做

- [ ] 支持点球大战与加时赛标记
- [ ] 导出 Markdown 表格，方便贴到周报
- [ ] 增加 `--top N` 输出射手榜（需扩展 CSV 字段）
- [ ] 生成 matplotlib 图表（可选依赖，不影响核心功能）

欢迎提 Issue 或 PR。

## License

[MIT](LICENSE)
