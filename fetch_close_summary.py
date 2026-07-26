#!/usr/bin/env python3
"""
收盘后汇总 — 15:00 收盘后从各数据源汇总当日数据快照，给总览/数据监控卡片用
输出: data/close_summary.json

数据源：
- nt_data.json: 12只ETF收盘价/涨跌幅/成交额
- sector_fund_flow.json: 板块当日资金流
- market_alerts.json: 当日市场异动
- inst_trade.json: 机构当日买卖

字段:
- date: YYYY-MM-DD
- update_time: ISO8601
- etf_summary: {total, up, down, total_amount_yi, total_change_pct, biggest_up, biggest_down}
- sector_top_in: 流入TOP5板块
- sector_top_out: 流出TOP5板块
- market_alerts_count: 异动总数
- inst_summary: 机构净买/卖
- generated_at: ISO8601

铁律：单点重试+休眠总预算 ≤ 2s
"""
import json
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "close_summary.json")


def load_json(name, default=None):
    if default is None:
        default = {}
    try:
        with open(os.path.join(DATA_DIR, name), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  ⚠️ {name} 加载失败: {e}")
        return default


def aggregate_etfs(nt_data):
    """汇总12只国家队ETF"""
    etfs = (nt_data.get("etfFlow") or {}).get("etfs") or []
    if not etfs:
        return None
    total_amount = sum(e.get("amount", 0) or 0 for e in etfs) / 1e8  # 元 → 亿元
    up = [e for e in etfs if (e.get("change_pct") or 0) > 0]
    down = [e for e in etfs if (e.get("change_pct") or 0) < 0]
    flat = [e for e in etfs if (e.get("change_pct") or 0) == 0]
    avg_chg = sum((e.get("change_pct") or 0) for e in etfs) / len(etfs) if etfs else 0
    sorted_by_chg = sorted(etfs, key=lambda x: x.get("change_pct") or 0, reverse=True)
    biggest_up = sorted_by_chg[0] if sorted_by_chg else None
    biggest_down = sorted_by_chg[-1] if sorted_by_chg else None
    return {
        "total": len(etfs),
        "up": len(up),
        "down": len(down),
        "flat": len(flat),
        "total_amount_yi": round(total_amount, 1),
        "avg_change_pct": round(avg_chg, 2),
        "biggest_up": {"name": biggest_up["name"], "code": biggest_up["code"], "change_pct": biggest_up.get("change_pct")} if biggest_up else None,
        "biggest_down": {"name": biggest_down["name"], "code": biggest_down["code"], "change_pct": biggest_down.get("change_pct")} if biggest_down else None,
        "update_time": nt_data.get("update_time"),
    }


def aggregate_sectors(sf_data):
    """TOP5流入/流出板块"""
    in_list = sf_data.get("sectors_in") or []
    out_list = sf_data.get("sectors_out") or []
    top_in = in_list[:5]
    top_out = out_list[:5]
    return {
        "top_in": [{"name": s.get("name", "?"), "net_yi": s.get("net", 0)} for s in top_in],
        "top_out": [{"name": s.get("name", "?"), "net_yi": s.get("net", 0)} for s in top_out],
        "update_time": sf_data.get("update_time"),
    }


def aggregate_alerts(ma_data):
    """市场异动汇总"""
    indices = ma_data.get("indices") or []
    alerts = ma_data.get("alerts") or []
    mood = ma_data.get("mood") or {}
    return {
        "count": len(alerts),
        "indices_count": len(indices),
        "mood_level": mood.get("level", mood.get("label", "中性")),
        "update_time": ma_data.get("update_time"),
    }


def aggregate_inst(inst_data):
    """机构净买卖"""
    return {
        "net_yi": inst_data.get("net_amount_yi") or inst_data.get("net_yi") or 0,
        "update_time": inst_data.get("update_time"),
    }


def main():
    print(f"📊 收盘后汇总 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 加载所有数据源
    nt = load_json("nt_data.json")
    sf = load_json("sector_fund_flow.json")
    ma = load_json("market_alerts.json")
    inst = load_json("inst_trade.json")

    # 汇总
    etf_sum = aggregate_etfs(nt)
    sec_sum = aggregate_sectors(sf)
    alert_sum = aggregate_alerts(ma)
    inst_sum = aggregate_inst(inst)

    # 决定 data_date（取最新 update_time 的日期）
    all_times = []
    for t in [etf_sum.get("update_time") if etf_sum else None,
              sec_sum.get("update_time"),
              alert_sum.get("update_time"),
              inst_sum.get("update_time")]:
        if t:
            try:
                all_times.append(datetime.strptime(t[:19], "%Y-%m-%d %H:%M:%S"))
            except Exception:
                pass
    data_date = max(all_times).strftime("%Y-%m-%d") if all_times else datetime.now().strftime("%Y-%m-%d")

    out = {
        "data_date": data_date,
        "update_time": datetime.now().isoformat(timespec="seconds"),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "etf_summary": etf_sum,
        "etf_flow_snapshot": nt.get("etfFlow") or {},  # 2026-07-22 新增：盘中ETF明细快照（收盘后用）
        "sector_summary": sec_sum,
        "market_alerts_summary": alert_sum,
        "inst_summary": inst_sum,
        "sources": {
            "nt_data": etf_sum.get("update_time") if etf_sum else None,
            "sector_fund_flow": sec_sum.get("update_time"),
            "market_alerts": alert_sum.get("update_time"),
            "inst_trade": inst_sum.get("update_time"),
        },
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 写入 {OUTPUT_FILE} (data_date={data_date})")
    if etf_sum:
        print(f"     ETF: 涨{etf_sum['up']}/跌{etf_sum['down']}/平{etf_sum['flat']}, 总额{etf_sum['total_amount_yi']}亿, 均涨{etf_sum['avg_change_pct']}%")
    if sec_sum:
        print(f"     板块: TOP5流入={len(sec_sum['top_in'])}个, TOP5流出={len(sec_sum['top_out'])}个")
    if alert_sum:
        print(f"     异动: {alert_sum['count']}条, 情绪={alert_sum['mood_level']}")


if __name__ == "__main__":
    main()
