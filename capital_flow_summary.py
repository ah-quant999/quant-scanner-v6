#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资金流向三方对比摘要
========================
从 north_fund/lhb_result/inst_trade/sector_fund_flow 四数据源聚合，
生成 北向/机构/游资 三方的「7月15日方向 + 偏好风格 + 共同买卖 + 关键信号」。
输出: data/capital_flow_summary.json → 由 update_data_v2.py 注入到 预判信号页 机游共振正下方卡片

依赖: north_fund.json, lhb_result.json, inst_trade.json, sector_fund_flow.json, industry_map.json
"""
import os, sys, json
from collections import Counter, defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def load(fn):
    try:
        return json.load(open(os.path.join(DATA_DIR, fn), encoding="utf-8"))
    except Exception:
        return {}

def code2ind(code):
    """002558 → sz_002558, 600186 → sh_600186"""
    c = str(code).strip()
    if c.startswith(("6", "9")):
        return "sh_" + c
    return "sz_" + c

def fmt_yi(v):
    """1234567.8 → 123.5亿（保留1位小数）"""
    try:
        return f"{float(v)/1e8:.1f}亿"
    except Exception:
        return str(v)

def main():
    nf = load("north_fund.json")
    lhb = load("lhb_result.json")
    inst = load("inst_trade.json")
    sf = load("sector_fund_flow.json")
    ind = load("industry_map.json")
    ind_stocks = ind.get("stocks", {})

    today = nf.get("update_time", "").split(" ")[0] or "未知"
    lhb_date = lhb.get("date", "")
    stocks = lhb.get("stocks", [])

    # ── 1. 南向/北向 ──
    south = nf.get("south_flow", {})
    south_week = nf.get("south_week", {})
    south_hist = nf.get("south_history", [])
    south_total_亿 = float(south.get("total", 0) or 0)
    south_dir = south.get("direction", "")
    # 近5日趋势
    if south_hist:
        recent = sorted(south_hist, key=lambda x: x.get("date", ""), reverse=True)[:5]
        s5_net = sum(r.get("net_buy", 0) for r in recent)
        s5_亿 = abs(s5_net)/1e8
        s5_dir_word = "净流入" if s5_net > 0 else "净流出"
        north_trend = f"连续5日{s5_dir_word}{s5_亿:.1f}亿"
    else:
        north_trend = ""
        s5_亿 = 0

    # 南向 direction 简洁文字
    south_direction = f"南向持续买入人（近5日净流入{s5_亿:.1f}亿）" if south_dir == "流入" else \
                      f"南向持续卖出（近5日净流出{s5_亿:.1f}亿）"
    south_signal_extra = f"当日南向净{south_dir}{south_total_亿:.1f}亿" if south_total_亿 else "当日无数据"

    # ── 2. 机构/主力 ──
    inst_total = nf.get("north_info", {}).get("inst_active", 0)
    inst_net_total_亿 = float(inst.get("total_net", 0) or 0)  # 亿
    if stocks:
        inst_stocks = sorted(stocks, key=lambda s: s.get("inst_net_万", 0), reverse=True)
        inst_top_buy_names = [s["name"] for s in inst_stocks if s.get("inst_net_万", 0) > 0][:3]
        inst_top_sell_names = [s["name"] for s in inst_stocks if s.get("inst_net_万", 0) < 0][:3]
    else:
        inst_top_buy_names = []
        inst_top_sell_names = []

    # 机构 direction 简洁文字（关键修复：不能直接 f-string list of dict）
    if inst_net_total_亿 > 0:
        inst_dir_word = f"净流入{inst_net_total_亿:.1f}亿"
    elif inst_net_total_亿 < 0:
        inst_dir_word = f"净流出{abs(inst_net_total_亿):.1f}亿"
    else:
        inst_dir_word = "持平"
    inst_direction = f"机构全天{inst_dir_word}，集抱高切低" if inst_net_total_亿 < 0 else f"机构全天{inst_dir_word}"

    # ── 3. 游资 ──
    if stocks:
        yz_stocks = sorted(stocks, key=lambda s: s.get("yz_net_万", 0), reverse=True)
        yz_top_buy_names = [s["name"] for s in yz_stocks if s.get("yz_net_万", 0) > 0][:3]
        yz_top_sell_names = [s["name"] for s in yz_stocks if s.get("yz_net_万", 0) < 0][:3]
        yz_buy_count = sum(1 for s in stocks if s.get("yz_net_万", 0) > 0)
        yz_sell_count = sum(1 for s in stocks if s.get("yz_net_万", 0) < 0)
    else:
        yz_top_buy_names = []
        yz_top_sell_names = []
        yz_buy_count = yz_sell_count = 0

    hot_money_direction = f"游资净买入 {yz_buy_count} 只 / 净卖出 {yz_sell_count} 只"

    # ── 4. 共同买入/卖出（三方净买都为正/负的个股） ──
    common_buy_names, common_sell_names = [], []
    for s in stocks:
        inst_n = s.get("inst_net_万", 0)
        yz_n = s.get("yz_net_万", 0)
        # 北向（龙虎榜席位）
        bk = s.get("seats", {}).get("北向", {})
        bk_n = bk.get("buy", 0) - bk.get("sell", 0)
        if inst_n > 0 and yz_n > 0 and bk_n > 0:
            common_buy_names.append(s["name"])
        elif inst_n < 0 and yz_n < 0 and bk_n < 0:
            common_sell_names.append(s["name"])

    # ── 5. 偏好风格（板块资金流趋势） ──
    trend_5d = sf.get("trend_5d", [])
    top_sectors = trend_5d[:5] if trend_5d else []
    sector_names = [s["name"] for s in top_sectors]
    inflow_sectors = [s["name"] for s in trend_5d if s.get("net_5d", 0) > 0][:5]
    outflow_sectors = [s["name"] for s in trend_5d if s.get("net_5d", 0) < 0][:5]

    # 偏好风格简洁文字
    if inflow_sectors:
        south_style = f"持续流入 {inflow_sectors[0]} 等板块（{len(inflow_sectors)}个净流入）"
    else:
        south_style = "无明显偏好"
    if inflow_sectors:
        inst_style = "、".join(inflow_sectors[:3]) if len(inflow_sectors) >= 3 else "、".join(inflow_sectors)
    else:
        inst_style = "高切低防御"
    if outflow_sectors:
        hot_money_style = f"切换到 {outflow_sectors[0]}（高低切）"
    else:
        hot_money_style = "追涨题材+次新"

    # 共同买卖：机构专用 + 游资 + 北向
    inst_common_buy = common_buy_names[:3] if common_buy_names else inst_top_buy_names
    inst_common_sell = common_sell_names[:3] if common_sell_names else outflow_sectors[:3]
    yz_common_buy = common_buy_names[:3] if common_buy_names else yz_top_buy_names
    yz_common_sell = common_sell_names[:3] if common_sell_names else outflow_sectors[:3]

    # ── 6. 关键信号 ──
    south_signal = f"{north_trend}，是否延续待观察" if south_dir == "流入" else f"{north_trend}，警惕转弱"
    inst_signal = f"仅 {len(inflow_sectors)} 个板块净流入（{'/'.join(inflow_sectors[:3]) if inflow_sectors else '无'}）" if inst_net_total_亿 < 0 else f"{len(inflow_sectors)}个板块净流入"
    hot_money_signal = "高低切加速，连板高度压制在3板" if outflow_sectors and len(outflow_sectors) > 3 else "分歧加大"

    signals = []
    if inst_net_total_亿:
        signals.append(f"机构全天{inst_dir_word}")
    if common_buy_names:
        signals.append(f"三方共振净买入: {', '.join(common_buy_names[:3])}")
    if common_sell_names:
        signals.append(f"三方共振净卖出: {', '.join(common_sell_names[:3])}")
    if sector_names:
        signals.append(f"资金偏好: {', '.join(sector_names[:3])}")
    if south_total_亿:
        signals.append(f"南向单日净{south_dir}{south_total_亿:.1f}亿")

    # ── 输出 ──
    result = {
        "date": today,
        "update_time": nf.get("update_time", "未知"),
        "north_south": {
            "direction": south_direction,
            "trend_5d": north_trend,
            "style": south_style,
            "common_buy": common_buy_names[:3],
            "common_sell": common_sell_names[:3],
            "signal": south_signal
        },
        "inst": {
            "direction": inst_direction,
            "style": inst_style,
            "common_buy": inst_common_buy,
            "common_sell": inst_common_sell,
            "signal": inst_signal
        },
        "hot_money": {
            "direction": hot_money_direction,
            "style": hot_money_style,
            "common_buy": yz_common_buy,
            "common_sell": yz_common_sell,
            "signal": hot_money_signal
        },
        "common_buy_stocks": common_buy_names,
        "common_sell_stocks": common_sell_names,
        "top_sectors": [{"name": s["name"], "net_5d": s.get("net_5d", 0)} for s in top_sectors],
        "signals": signals
    }

    out_path = os.path.join(DATA_DIR, "capital_flow_summary.json")
    json.dump(result, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[资金流向摘要] 已输出 {out_path}")
    print(f"  南向: {south_direction}")
    print(f"  机构: {inst_direction} | {inst_style}")
    print(f"  游资: {hot_money_direction} | {hot_money_style}")
    print(f"  共同买入 {len(common_buy_names)} 只: {common_buy_names}")
    print(f"  共同卖出 {len(common_sell_names)} 只: {common_sell_names}")

if __name__ == "__main__":
    main()
