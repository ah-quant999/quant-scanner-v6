#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资金流向三方对比摘要
========================
从 north_fund/lhb_result/inst_trade/sector_fund_flow 四数据源聚合，
生成 北向/机构/游资 三方的「7月15日方向 + 偏好风格 + 共同买卖 + 关键信号」。
输出: data/capital_flow_summary.json → 由 update_data_v2.py 注入到暂未上架卡片

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
    north_direction = f"{south.get('direction','')} {south.get('total',0)}{south.get('unit','')}"
    # 近5日趋势
    if south_hist:
        recent = sorted(south_hist, key=lambda x: x.get("date", ""), reverse=True)[:5]
        s5_net = sum(r.get("net_buy", 0) for r in recent)
        s5_direction = "流入" if s5_net > 0 else "流出"
        north_trend = f"近5日{s5_direction}{abs(s5_net):.0f}亿"
    else:
        north_trend = ""

    # ── 2. 机构/主力 ──
    inst_total = nf.get("north_info", {}).get("inst_active", 0)
    inst_net_total = inst.get("total_net", 0)  # 亿
    if stocks:
        inst_stocks = sorted(stocks, key=lambda s: s.get("inst_net_万", 0), reverse=True)
        inst_top_buy = [s for s in inst_stocks if s["inst_net_万"] > 0]
        inst_top_sell = [s for s in inst_stocks if s["inst_net_万"] < 0]
    else:
        inst_top_buy = []
        inst_top_sell = []

    # ── 3. 游资 ──
    if stocks:
        yz_stocks = sorted(stocks, key=lambda s: s.get("yz_net_万", 0), reverse=True)
        yz_top_buy = [s for s in yz_stocks if s["yz_net_万"] > 0]
        yz_top_sell = [s for s in yz_stocks if s["yz_net_万"] < 0]
    else:
        yz_top_buy = []
        yz_top_sell = []

    # ── 4. 共同买入/卖出（三方净买都为正/负的个股） ──
    common_buy, common_sell = [], []
    for s in stocks:
        inst_n = s.get("inst_net_万", 0)
        yz_n = s.get("yz_net_万", 0)
        # 北向（龙虎榜席位）
        bk = s.get("seats", {}).get("北向", {})
        bk_n = bk.get("buy", 0) - bk.get("sell", 0)
        if inst_n > 0 and yz_n > 0 and bk_n > 0:
            common_buy.append(s["name"])
        elif inst_n < 0 and yz_n < 0 and bk_n < 0:
            common_sell.append(s["name"])

    # ── 5. 偏好风格（板块资金流趋势） ──
    trend_5d = sf.get("trend_5d", [])
    top_sectors = trend_5d[:5] if trend_5d else []
    sector_names = [s["name"] for s in top_sectors]

    # ── 6. 关键信号 ──
    signals = []
    if inst_net_total > 0:
        signals.append(f"机构全天净买入{inst_net_total:.1f}亿")
    else:
        signals.append(f"机构全天净卖出{abs(inst_net_total):.1f}亿")
    if common_buy:
        signals.append(f"三方共振净买入: {', '.join(common_buy[:3])}")
    if common_sell:
        signals.append(f"三方共振净卖出: {', '.join(common_sell[:3])}")
    if sector_names:
        signals.append(f"资金偏好: {', '.join(sector_names[:3])}")
    if south_hist:
        last = south_hist[-1].get("net_buy", 0)
        signals.append(f"南向单日净{last:.0f}亿")

    # ── 输出 ──
    result = {
        "date": today,
        "update_time": nf.get("update_time", "未知"),
        "north_south": {
            "direction": north_direction,
            "trend_5d": north_trend,
            "style": "南向持续买入（近5日净流入偏消费+科技）",
            "common_buy": common_buy[:3],
            "common_sell": common_sell[:3],
            "signal": f"当日南向净{south.get('direction','')}{south.get('total',0)}亿，{north_trend}"
        },
        "inst": {
            "direction": f"机构净买入 {inst_top_buy[:3]} / 净卖出 {inst_top_sell[:3]}",
            "style": "偏好名单中的龙头（药/科技/金融）",
            "common_buy": [s["name"] for s in inst_top_buy[:3]],
            "common_sell": [s["name"] for s in inst_top_sell[:3]],
            "signal": f"机构净额{inst_net_total:.1f}亿"
        },
        "hot_money": {
            "direction": f"游资净买入 {len(yz_top_buy)} 只 / 净卖出 {len(yz_top_sell)} 只",
            "style": "追涨题材+次新",
            "common_buy": [s["name"] for s in yz_top_buy[:3]],
            "common_sell": [s["name"] for s in yz_top_sell[:3]],
            "signal": ""
        },
        "common_buy_stocks": common_buy,
        "common_sell_stocks": common_sell,
        "top_sectors": [{"name": s["name"], "net_5d": s.get("net_5d", 0)} for s in top_sectors],
        "signals": signals
    }

    out_path = os.path.join(DATA_DIR, "capital_flow_summary.json")
    json.dump(result, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[资金流向摘要] 已输出 {out_path}")
    print(f"  南向: {north_direction}")
    print(f"  机构净额: {inst_net_total:.1f}亿, 上榜 {len(stocks)} 只")
    print(f"  共同买入 {len(common_buy)} 只: {common_buy}")
    print(f"  共同卖出 {len(common_sell)} 只: {common_sell}")

if __name__ == "__main__":
    main()
