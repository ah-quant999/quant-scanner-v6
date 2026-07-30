#!/usr/bin/env python3
"""v8 数据构建脚本 — 从共享 data/ 注入真实JSON到 v8/index.html 模板"""

import json, os, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
V8_DIR = REPO / "v8"
TEMPLATE = V8_DIR / "index.html"
OUTPUT = V8_DIR / "dist" / "index.html"
CAL_TEMPLATE = V8_DIR / "calendar.html"
CAL_OUTPUT = V8_DIR / "dist" / "calendar.html"

# 需要注入到页面的数据源（key=window变量名, value=data目录文件名）
DATA_SOURCES = {
    "ETF_INTRADAY_HEAT": "etf_intraday_heat.json",
    "SECTOR_FUND_FLOW":  "sector_fund_flow.json",
    "SCAN_DATA":         "scan_data.json",
    "GOLD_POOL":         "gold_pool.json",
    "STOCK_LIST":        "stock_names.json",
    "RECOMMEND":         "recommend.json",
    "MACRO_DATA":        "macro_data.json",
    "NT_DATA":           "nt_data.json",
    "LHB_DATA":          "lhb_data.json",
    "CONCEPT_RANKING":   "concept_ranking.json",
    "MARGIN_DATA":       "margin_data.json",
    "CFFEX_HOLDINGS":    "cffex_holdings.json",
    "IPO_DATA":          "ipo_score.json",
    "CRISIS_DATA":       "crisis_data.json",
    "V8_CAL":            "calendar.json",
    "CRDS_CARD_DATA":    "crds_result.json",
    # ===== 选股策略四模块数据源 =====
    "TRIPLE_CONSENSUS":       "triple_consensus.json",
    "TRIPLE_TRACK":           "triple_track.json",
    "TRIPLE_HISTORY":         "triple_resonance_history.json",
    "COCKPIT_TIER_RECOMMEND": "cockpit_tier_recommend_alimi.json",
    "TOP10_DAILY":            "top10_daily.json",
    "COCKPIT_ADVICE":         "cockpit_advice.json",
    "SH_FIB":                 "sh_index_fib.json",
    "SZ_FIB":                 "sz_index_fib.json",
    "SECTOR_RS":              "sector_rs.json",
    "LHB_DATA":               "lhb_result.json",
    "INST_TRADE":             "inst_trade.json",
    "NORTH_FUND":             "north_fund.json",
    "MARKET_ALERTS":          "market_alerts.json",
    "MARKET_FUND_FLOW_DATA":  "market_fund_flow.json",
    "ETF_SUBSCRIPTION":       "etf_subscription.json",
    "W52_HIGH":               "52w_high.json",
    "LIMIT_UP_HEATMAP":       "limit_up_heatmap.json",
    "HERDING_DATA":           "herding_data.json",
    "VOLATILITY":             "volatility_watch.json",
    "CAPITAL_FLOW_DATA":      "capital_flow_summary.json",
    "MAHORO":                 "maharo_signals.json",
    "CANDIDATE":              "candidate_pool.json",
    "BACKTEST_COMPREHENSIVE": "backtest_comprehensive.json",
    "COCKPIT_BACKTEST":       "cockpit_backtest.json",
    "BACKTEST_TDX":           "backtest_tdx.json",
    "EXPERIMENT":             "experiment.json",
    # ===== ETF量能脉冲 + 日监控 =====
    "ETF_PULSE":              "etf_pulse.json",
    "ETF_DAILY_MONITOR":      "etf_daily_monitor.json",
}

# calendar.html 专用数据
CAL_DATA = {"V8_CAL": "calendar.json"}

def load_json(path):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def load_latest_volatility():
    """查找 experiment/ 下最新的 volatility_watch_*.json 并返回"""
    exp_dir = DATA / "experiment"
    if not exp_dir.exists():
        return {}
    files = sorted(exp_dir.glob("volatility_watch_*.json"), reverse=True)
    if not files:
        return {}
    return load_json(files[0])

def build():
    os.makedirs(V8_DIR / "dist", exist_ok=True)

    with open(TEMPLATE, encoding='utf-8') as f:
        html = f.read()

    # 在 </head> 前注入数据块
    data_blocks = []
    for var, file in DATA_SOURCES.items():
        # 特殊处理：波动率从 experiment/ 目录取最新文件
        if var == "VOLATILITY":
            jd = load_latest_volatility()
        else:
            jd = load_json(DATA / file)
        json_str = json.dumps(jd, ensure_ascii=False, default=str)
        data_blocks.append(f'<script>window.{var} = {json_str};</script>')

    inject_script = '\n'.join(data_blocks) + '\n'

    # 插入到 </head> 前
    html = html.replace('</head>', inject_script + '</head>')

    # 写入输出
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ v8 数据注入完成")
    print(f"   数据源: {len(DATA_SOURCES)} 个")
    print(f"   输出: {OUTPUT}")
    print(f"   大小: {len(html):,} 字符")

    # 同时构建 calendar.html
    if CAL_TEMPLATE.exists():
        with open(CAL_TEMPLATE, encoding='utf-8') as f:
            cal_html = f.read()
        cal_blocks = []
        for var, file in CAL_DATA.items():
            jd = load_json(DATA / file)
            json_str = json.dumps(jd, ensure_ascii=False, default=str)
            cal_blocks.append(f'<script>window.{var} = {json_str};</script>')
        cal_inject = '\n'.join(cal_blocks) + '\n'
        # calendar.html 的占位符在第一个 <script> 块（V8_CAL = {...} 占位）前注入
        cal_html = cal_html.replace(
            '<script>\n// 数据占位（由 update_calendar.py 注入）\nwindow.V8_CAL = {weeks:[],legend:[],update_time:\'\'};\n</script>',
            cal_inject + '<script>\n// 数据占位（由 update_calendar.py 注入）\nwindow.V8_CAL = {weeks:[],legend:[],update_time:\'\'};\n</script>'
        )
        with open(CAL_OUTPUT, 'w', encoding='utf-8') as f:
            f.write(cal_html)
        print(f"✅ calendar 数据注入完成")
        print(f"   输出: {CAL_OUTPUT}")
        print(f"   大小: {len(cal_html):,} 字符")

if __name__ == '__main__':
    build()
