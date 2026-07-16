#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资金流向三方对比摘要 v2
========================
从 north_fund/lhb_result/inst_trade/sector_fund_flow/industry_map 五数据源聚合，
生成 南向/北向龙虎榜席位/机构席位/游资 三方的「方向 + 偏好风格 + 共同买卖 + 关键信号」。

口径说明（参考北向资金日历）：
- 港交所自 2024-05-13 起停更北向资金实时交易数据，2024-08-16 起停更每日净流入数据。
- 本卡片中的"北向"仅指龙虎榜披露的北向席位净买卖，覆盖当日上龙虎榜的异动股，不等同全市场北向资金。
- 机构/游资同样来自龙虎榜席位，非全市场机构/游资全貌。

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

def fmt_yi(v):
    """原始金额（元）→ 1.2亿 / 1.2万"""
    try:
        val = float(v)
        if abs(val) >= 1e8:
            return f"{val/1e8:.1f}亿"
        if abs(val) >= 1e4:
            return f"{val/1e4:.1f}万"
        return f"{val:.0f}"
    except Exception:
        return str(v)

def fmt_yi_unit(v, unit="亿"):
    """已经以 unit 为单位的数值，保留1位小数"""
    try:
        return f"{float(v):.1f}{unit}"
    except Exception:
        return str(v)

def code2ind(code):
    c = str(code).strip()
    if c.startswith(("6", "9")):
        return "sh_" + c
    return "sz_" + c

def stock_industries(stocks_map, code):
    """返回个股关联的概念/行业列表（去重）"""
    if not stocks_map:
        return []
    info = stocks_map.get(code2ind(code)) or stocks_map.get(str(code), {})
    industries = []
    if isinstance(info, dict):
        for k in ["concept", "concepts", "industry", "industry_name"]:
            v = info.get(k)
            if isinstance(v, str) and v:
                industries.extend([x.strip() for x in v.split(",") if x.strip()])
            elif isinstance(v, list):
                industries.extend([str(x).strip() for x in v if str(x).strip()])
    return list(dict.fromkeys(industries))[:5]

def seats_top(stocks, seat_name, n=3):
    """从龙虎榜 seats 中按某席位净额取 Top N 买入/卖出，返回 [(name, net_yuan, code)]"""
    buy_rows, sell_rows = [], []
    for s in stocks:
        seat = s.get("seats", {}).get(seat_name, {})
        # seats 字段单位为"万"，统一转成元输出
        buy = float(seat.get("buy", 0) or 0) * 1e4
        sell = float(seat.get("sell", 0) or 0) * 1e4
        net = buy - sell
        name = s.get("name", s.get("code", ""))
        code = s.get("code", "")
        if net > 0:
            buy_rows.append((name, net, code))
        elif net < 0:
            sell_rows.append((name, net, code))
    buy_rows.sort(key=lambda x: x[1], reverse=True)
    sell_rows.sort(key=lambda x: x[1])
    return buy_rows[:n], sell_rows[:n]

def format_names(rows, with_money=True):
    """rows = [(name, net, code)] → ['A (+x.x亿)', 'B (+y.y亿)']"""
    if not rows:
        return []
    if with_money:
        return [f"{name}（{fmt_yi(net)}）" for name, net, code in rows]
    return [name for name, net, code in rows]

def sector_style_from_stocks(stocks, stocks_map, n=3):
    """根据一组个股的行业/概念映射，取出现次数最多的前 N 个板块"""
    counter = Counter()
    for s in stocks:
        code = s.get("code", "")
        industries = stock_industries(stocks_map, code)
        for ind in industries:
            counter[ind] += 1
    if not counter:
        return []
    return [name for name, _ in counter.most_common(n)]

def main():
    nf = load("north_fund.json")
    lhb = load("lhb_result.json")
    inst = load("inst_trade.json")
    sf = load("sector_fund_flow.json")
    ind = load("industry_map.json")
    ind_stocks = ind.get("stocks", {})

    today = nf.get("update_time", "").split(" ")[0] or lhb.get("date", "") or "未知"
    stocks = lhb.get("stocks", [])

    # ── 1. 南向资金（港股通，唯一可靠的全市场数据源） ──
    south = nf.get("south_flow", {})
    south_week = nf.get("south_week", {})
    south_total_亿 = float(south.get("total", 0) or 0)
    south_dir = south.get("direction", "")

    # 近5日净流入：直接用 south_week（north_fund.json 已汇总），避免历史单位换算错误
    if south_week and south_week.get("days"):
        s5_亿 = float(south_week.get("total", 0) or 0)
        s5_days = int(south_week.get("days", 5))
        s5_dir_word = "净流入" if s5_亿 > 0 else "净流出"
        north_trend = f"连续{s5_days}日{s5_dir_word}{abs(s5_亿):.1f}亿"
    else:
        # 兜底：从历史数组取最近5日，net_buy 字段已是以亿为单位
        south_hist = nf.get("south_history", [])
        if south_hist:
            recent = sorted(south_hist, key=lambda x: x.get("date", ""), reverse=True)[:5]
            s5_net = sum(float(r.get("net_buy", 0) or 0) for r in recent)
            s5_亿 = abs(s5_net)
            s5_days = len(recent)
            s5_dir_word = "净流入" if s5_net > 0 else "净流出"
            north_trend = f"连续{s5_days}日{s5_dir_word}{s5_亿:.1f}亿"
        else:
            north_trend = ""
            s5_亿 = 0

    if south_dir == "流入":
        south_direction = f"南向持续买入（近5日净流入{s5_亿:.1f}亿）"
    elif south_dir == "流出":
        south_direction = f"南向持续卖出（近5日净流出{s5_亿:.1f}亿）"
    else:
        south_direction = f"南向持平（近5日净{s5_dir_word}{s5_亿:.1f}亿）"

    south_signal_extra = f"当日南向净{south_dir}{south_total_亿:.1f}亿" if south_total_亿 else "当日无数据"

    # 5日板块偏好
    trend_5d = sf.get("trend_5d", [])
    inflow_sectors = [s["name"] for s in trend_5d if s.get("net_5d", 0) > 0][:5]
    outflow_sectors = [s["name"] for s in trend_5d if s.get("net_5d", 0) < 0][:5]
    if inflow_sectors:
        south_style = f"5日持续流入：{ '、'.join(inflow_sectors[:3]) }"
    else:
        south_style = "无明显偏好"

    # ── 2. 北向龙虎榜席位（不是全市场北向，是龙虎榜异动股的北向席位） ──
    bx_buy, bx_sell = seats_top(stocks, "北向", n=3)
    bx_net_total = sum(net for _, net, _ in bx_buy) + sum(net for _, net, _ in bx_sell)  # sell 为负
    bx_dir_word = "净流入" if bx_net_total > 0 else "净流出"
    bx_direction = f"龙虎榜北向席位{bx_dir_word}{fmt_yi(abs(bx_net_total))}（仅覆盖异动股）"
    bx_style_sectors = sector_style_from_stocks([s for s in stocks if s.get("seats", {}).get("北向")], ind_stocks, n=3)
    bx_style = f"偏好：{ '、'.join(bx_style_sectors[:3]) }" if bx_style_sectors else "未形成集中偏好"
    bx_signal = f"北向席位净买入 {len(bx_buy)} 只 / 净卖出 {len(bx_sell)} 只"

    # ── 3. 机构席位（龙虎榜机构专用席位） ──
    inst_buy, inst_sell = seats_top(stocks, "机构", n=3)
    inst_net_total = sum(net for _, net, _ in inst_buy) + sum(net for _, net, _ in inst_sell)
    inst_dir_word = "净流入" if inst_net_total > 0 else "净流出"
    inst_direction = f"机构席位{inst_dir_word}{fmt_yi(abs(inst_net_total))}（龙虎榜专用席位）"
    inst_style_sectors = sector_style_from_stocks([s for s in stocks if s.get("seats", {}).get("机构")], ind_stocks, n=3)
    inst_style = f"偏好：{ '、'.join(inst_style_sectors[:3]) }" if inst_style_sectors else "高切低防御"
    inst_signal = f"机构席位净买入 {len(inst_buy)} 只 / 净卖出 {len(inst_sell)} 只"

    # ── 4. 游资（龙虎榜未识别席位 + 涨停敢死队特征） ──
    yz_buy, yz_sell = seats_top(stocks, "未识别", n=3)
    yz_net_total = sum(net for _, net, _ in yz_buy) + sum(net for _, net, _ in yz_sell)
    yz_dir_word = "净流入" if yz_net_total > 0 else "净流出"
    yz_direction = f"游资席位{yz_dir_word}{fmt_yi(abs(yz_net_total))}（未识别席位）"
    yz_style_sectors = sector_style_from_stocks([s for s in stocks if s.get("seats", {}).get("未识别")], ind_stocks, n=3)
    yz_style = f"偏好：{ '、'.join(yz_style_sectors[:3]) }" if yz_style_sectors else "追涨题材+次新"
    yz_signal = f"游资席位净买入 {len(yz_buy)} 只 / 净卖出 {len(yz_sell)} 只"

    # ── 5. 三方共振（北向席位、机构席位、游资席位 同方向） ──
    # 这里用 lhb_result 里的原始字段 inst_net_万/yz_net_万 与 北向席位 net 再判断一次，更稳健
    common_buy, common_sell = [], []
    for s in stocks:
        inst_n = s.get("inst_net_万", 0) or 0
        yz_n = s.get("yz_net_万", 0) or 0
        bx_seat = s.get("seats", {}).get("北向", {})
        bx_n = (bx_seat.get("buy", 0) or 0) - (bx_seat.get("sell", 0) or 0)
        # 单位统一：inst/yz 是万，bx 是元；统一为元比较方向
        inst_yuan = inst_n * 1e4
        yz_yuan = yz_n * 1e4
        if inst_yuan > 0 and yz_yuan > 0 and bx_n > 0:
            common_buy.append((s.get("name", s.get("code", "")), s.get("code", "")))
        elif inst_yuan < 0 and yz_yuan < 0 and bx_n < 0:
            common_sell.append((s.get("name", s.get("code", "")), s.get("code", "")))

    common_buy_names = [name for name, code in common_buy]
    common_sell_names = [name for name, code in common_sell]

    # ── 6. 关键信号汇总 ──
    signals = []
    if south_total_亿:
        signals.append(f"南向单日净{south_dir}{south_total_亿:.1f}亿")
    if north_trend:
        signals.append(north_trend)
    if common_buy_names:
        signals.append(f"三方共振净买入：{', '.join(common_buy_names[:3])}")
    if common_sell_names:
        signals.append(f"三方共振净卖出：{', '.join(common_sell_names[:3])}")
    if inflow_sectors:
        signals.append(f"5日资金偏好：{', '.join(inflow_sectors[:3])}")
    if bx_buy:
        signals.append(f"北向席位买入：{format_names(bx_buy[:2], with_money=False)}")
    if inst_buy:
        signals.append(f"机构席位买入：{format_names(inst_buy[:2], with_money=False)}")
    if yz_buy:
        signals.append(f"游资席位买入：{format_names(yz_buy[:2], with_money=False)}")

    # ── 7. 输出 ──
    result = {
        "date": today,
        "update_time": nf.get("update_time", lhb.get("update_time", "未知")),
        "data_note": "龙虎榜席位数据，仅覆盖当日价格/换手率异动的上榜个股；全市场北向/机构/游资净流向已不可获取",
        "north_south": {
            "direction": south_direction,
            "trend_5d": north_trend,
            "style": south_style,
            "common_buy": format_names(bx_buy),
            "common_sell": format_names(bx_sell),
            "signal": f"{south_signal_extra}｜{north_trend}"
        },
        "inst": {
            "direction": inst_direction,
            "style": inst_style,
            "common_buy": format_names(inst_buy),
            "common_sell": format_names(inst_sell),
            "signal": inst_signal
        },
        "hot_money": {
            "direction": yz_direction,
            "style": yz_style,
            "common_buy": format_names(yz_buy),
            "common_sell": format_names(yz_sell),
            "signal": yz_signal
        },
        "common_buy_stocks": common_buy_names,
        "common_sell_stocks": common_sell_names,
        "top_sectors": [{"name": s["name"], "net_5d": s.get("net_5d", 0)} for s in trend_5d[:5]],
        "signals": signals,
        # 新增：各维度原始 Top 列表供前端扩展使用
        "raw": {
            "bx_buy": [(name, fmt_yi(net), code) for name, net, code in bx_buy],
            "bx_sell": [(name, fmt_yi(net), code) for name, net, code in bx_sell],
            "inst_buy": [(name, fmt_yi(net), code) for name, net, code in inst_buy],
            "inst_sell": [(name, fmt_yi(net), code) for name, net, code in inst_sell],
            "yz_buy": [(name, fmt_yi(net), code) for name, net, code in yz_buy],
            "yz_sell": [(name, fmt_yi(net), code) for name, net, code in yz_sell],
        }
    }

    out_path = os.path.join(DATA_DIR, "capital_flow_summary.json")
    json.dump(result, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"[资金流向摘要] 已输出 {out_path}")
    print(f"  南向: {south_direction}")
    print(f"  北向席位: {bx_direction}")
    print(f"  机构席位: {inst_direction}")
    print(f"  游资席位: {yz_direction}")
    print(f"  三方共振买入: {common_buy_names}")
    print(f"  三方共振卖出: {common_sell_names}")

if __name__ == "__main__":
    main()
