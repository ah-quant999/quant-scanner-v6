#!/usr/bin/env python3
"""
上交所每日资金净流入时间轴 — 抓取大盘主力资金单日净流入+累计
数据源：东财 push2his fflow 接口（secid=1.000001 上证指数，限 120 天历史）
输出: data/market_fund_flow.json

字段：
- daily: [{date, net_yi, super_large_yi, large_yi, medium_yi, small_yi, main_pct, small_pct}]
- cumulative: [{date, cum_yi}]  # 累计 = daily.net_yi 从最早日起累加
- last_update: ISO8601
- range: {start, end, count}

铁律：单点重试+休眠总预算 ≤2s（防 RemoteDisconnected 拖死看门狗）
"""
import json
import os
import time
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "market_fund_flow.json")

URL_HIS = "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
URL_TODAY = "https://push2.eastmoney.com/api/qt/stock/fflow/kline/get"
PARAMS = {
    "secid": "1.000001",  # 上证指数
    "fields1": "f1,f2,f3,f4",
    "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
    "klt": "101",
    "lmt": "500",
    "fqt": "0",
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://quote.eastmoney.com/zs000001.html",
    "Accept": "application/json,text/plain,*/*",
}
TIMEOUT = 12  # 单次尝试 ≤12s，总预算 ≤ 1.2s × 1 = 不重试


def fetch():
    """拉取东财 上证指数资金流日线
    主源：push2his（限 120-500 天历史），常被限流
    备源：push2 今日 kline（始终可用，但仅当日）
    两者字段一致：f51=date, f52=主力, f53=特大, f54=大, f55=中, f56=小, f57=主力%, f58=小%
    """
    # 主源：历史
    try:
        r = requests.get(URL_HIS, params=PARAMS, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if data.get("data") and data["data"].get("klines"):
            return data["data"]["klines"], "push2his"
    except Exception as e:
        print(f"  ⚠️ push2his失败: {type(e).__name__}: {str(e)[:60]}")

    # 备源：今日
    try:
        r = requests.get(URL_TODAY, params=PARAMS, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if data.get("data") and data["data"].get("klines"):
            return data["data"]["klines"], "push2"
    except Exception as e:
        print(f"  ⚠️ push2失败: {type(e).__name__}: {str(e)[:60]}")

    return [], "fail"


def parse_klines(klines):
    """klines 格式(8字段历史): '2026-01-20,-35029823488.0,24856432640.0,10173394944.0,-9701212160.0,-25328611328.0,-2.87,2.03'
    格式(6字段今日):   '2026-07-22,-2958729216.0,2196434944.0,762294272.0,-159006720.0,-2799722496.0'
    """
    daily = []
    for line in klines:
        parts = line.split(",")
        if len(parts) < 6:
            continue
        try:
            entry = {
                "date": parts[0],
                "net_yi": round(float(parts[1]) / 1e8, 2),          # 主力净流入(亿)
                "super_large_yi": round(float(parts[2]) / 1e8, 2),   # 特大单净流入(亿)
                "large_yi": round(float(parts[3]) / 1e8, 2),         # 大单净流入(亿)
                "medium_yi": round(float(parts[4]) / 1e8, 2),        # 中单净流入(亿)
                "small_yi": round(float(parts[5]) / 1e8, 2),         # 小单净流入(亿)
                "main_pct": float(parts[6]) if len(parts) >= 7 else None,
                "small_pct": float(parts[7]) if len(parts) >= 8 else None,
            }
            daily.append(entry)
        except (ValueError, IndexError):
            continue
    return daily


def compute_cumulative(daily):
    """累计 = 主力净流入 从最早到当天的累加"""
    cum = 0.0
    result = []
    for d in daily:
        cum += d["net_yi"]
        result.append({"date": d["date"], "cum_yi": round(cum, 2)})
    return result


def merge_history(existing_daily, new_daily):
    """合并历史：existing 优先保留（防改字段），新数据补到现有尾部"""
    if not existing_daily:
        return new_daily
    if not new_daily:
        return existing_daily
    existing_dates = {d["date"] for d in existing_daily}
    merged = list(existing_daily)
    for d in new_daily:
        if d["date"] not in existing_dates:
            merged.append(d)
    merged.sort(key=lambda x: x["date"])
    return merged


def main():
    print(f"📊 上交所大盘资金流时间轴 (东财 push2his fflow)")

    # 加载已有数据用于增量
    existing_daily = []
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                old = json.load(f)
            existing_daily = old.get("daily", [])
            print(f"  历史: {len(existing_daily)} 天 ({old.get('range', {}).get('start', '?')} ~ {old.get('range', {}).get('end', '?')})")
        except Exception as e:
            print(f"  ⚠️ 旧文件解析失败: {e}")

    # 拉取
    klines, source = fetch()
    if not klines:
        # 拉取失败：保留旧数据，落 fail 标记
        if existing_daily:
            cum = compute_cumulative(existing_daily)
            out = {
                "daily": existing_daily,
                "cumulative": cum,
                "last_update": datetime.now().isoformat(timespec="seconds"),
                "range": {"start": existing_daily[0]["date"], "end": existing_daily[-1]["date"], "count": len(existing_daily)},
                "fetch_status": "fail_keep_existing",
            }
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            print(f"  ⚠️ fetch失败，保留旧 {len(existing_daily)} 天")
        else:
            # 没有旧数据，写空壳
            out = {
                "daily": [],
                "cumulative": [],
                "last_update": datetime.now().isoformat(timespec="seconds"),
                "range": {"start": None, "end": None, "count": 0},
                "fetch_status": "fail_no_data",
            }
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            print(f"  ❌ fetch失败且无历史数据")
        return

    new_daily = parse_klines(klines)
    print(f"  本次拉到({source}): {len(new_daily)} 天 ({new_daily[0]['date']} ~ {new_daily[-1]['date']})")

    # 合并
    daily = merge_history(existing_daily, new_daily)
    print(f"  合并后: {len(daily)} 天")

    # 计算累计
    cumulative = compute_cumulative(daily)

    out = {
        "daily": daily,
        "cumulative": cumulative,
        "last_update": datetime.now().isoformat(timespec="seconds"),
        "range": {"start": daily[0]["date"], "end": daily[-1]["date"], "count": len(daily)},
        "fetch_status": f"ok_{source}",
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 写入 {OUTPUT_FILE} ({out['range']['start']} ~ {out['range']['end']}, {len(daily)} 天)")
    print(f"  累计: 最新 {cumulative[-1]['cum_yi']:.0f}亿, 极值 [{min(c['cum_yi'] for c in cumulative):.0f}, {max(c['cum_yi'] for c in cumulative):.0f}]")


if __name__ == "__main__":
    main()
