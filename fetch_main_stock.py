#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主力资金监控数据获取 — 使用 akshare（替代缺失的 westock-data CLI）
输出: data/main_stock.json

数据来源: akshare stock_individual_fund_flow (个股历史资金流向, 单位:元)
注: 原方案依赖 westock-data CLI (Node脚本) 在全环境均缺失, 故改用 akshare 直连东财。
"""
import os, sys, json, datetime, time
import akshare as ak

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "main_stock.json")

# 核心监控池: 大盘蓝筹 + 活跃个股
WATCHLIST = {
    # 金融
    "601398": "工商银行", "601939": "建设银行", "601288": "农业银行",
    "600036": "招商银行", "601318": "中国平安", "600030": "中信证券",
    # 白酒消费
    "600519": "贵州茅台", "000858": "五粮液", "000568": "泸州老窖",
    # 新能源
    "300750": "宁德时代", "002594": "比亚迪", "601012": "隆基绿能",
    # 科技
    "000725": "京东方A", "002475": "立讯精密", "603019": "中科曙光",
    "688981": "中芯国际", "000063": "中兴通讯",
    # 医药
    "600276": "恒瑞医药", "603259": "药明康德",
    # 资源
    "601899": "紫金矿业", "601857": "中国石油", "600028": "中国石化",
    # AI/芯片
    "688256": "寒武纪", "300308": "中际旭创", "603501": "韦尔股份",
    "688041": "海光信息",
    # 其他活跃
    "300274": "阳光电源", "600900": "长江电力", "601166": "兴业银行",
    "600809": "山西汾酒", "300502": "新易盛", "600585": "海螺水泥",
    "688111": "金山办公",
}

def fetch_akshare_flow(code):
    """用 akshare 获取个股历史资金流向, 返回 [{date, MainNetFlow(元)}]"""
    market = "sh" if code.startswith(("6", "68")) else "sz"
    try:
        df = ak.stock_individual_fund_flow(stock=code, market=market)
    except Exception as e:
        print(f"  akshare ERR {code}: {e}")
        return []
    if df is None or getattr(df, "empty", True):
        return []
    flows = []
    for _, row in df.iterrows():
        try:
            date = str(row["日期"])[:10]
            net = float(row["主力净流入-净额"])
        except (ValueError, KeyError, TypeError):
            continue
        flows.append({"date": date, "MainNetFlow": net})
    return flows

def compute_consecutive(flows, direction="in"):
    """计算连续净流入/流出天数（从最新日期往前数）"""
    if not flows:
        return 0
    sorted_flows = sorted(flows, key=lambda x: x["date"], reverse=True)
    count = 0
    for f in sorted_flows:
        if direction == "in" and f["MainNetFlow"] > 0:
            count += 1
        elif direction == "out" and f["MainNetFlow"] < 0:
            count += 1
        else:
            break
    return count

def is_trading_day():
    """简单判断周末 (暂不覆盖法定节假日, 节假日 akshare 会返回空, 不影响)"""
    return datetime.datetime.now().weekday() < 5

def main():
    print("=" * 50)
    print("  主力资金监控数据获取 (akshare)")
    print("=" * 50)
    now = datetime.datetime.now()

    # 周末/休市: 合法无数据, 不报错, 标记原因避免被误判为系统故障
    if not is_trading_day():
        result = {
            "update_time": now.strftime("%Y-%m-%d %H:%M"),
            "data_available": False,
            "top_main_in": [],
            "top_main_out": [],
            "status": "non_trading_day",
            "note": "周末/休市，无主力资金数据（合法空值，非故障）",
        }
        _save(result)
        print(f"\n⚠️ {result['note']}")
        return result

    # 工作日: 逐只抓取 (东财限流, 加小延迟)
    codes = list(WATCHLIST.keys())
    all_flows = {}
    for i, code in enumerate(codes, 1):
        flows = fetch_akshare_flow(code)
        if flows:
            all_flows[code] = flows
        if i % 10 == 0:
            print(f"  [{i}/{len(codes)}] 已获取 {len(all_flows)} 只")
        time.sleep(0.15)

    print(f"\n  共获取 {len(all_flows)} 只股票资金数据")

    # 计算最新交易日净流入排名
    stock_scores = []
    for code, name in WATCHLIST.items():
        if code not in all_flows:
            continue
        flows = all_flows[code]
        sorted_flows = sorted(flows, key=lambda x: x["date"], reverse=True)
        latest = sorted_flows[0]
        today_net = latest["MainNetFlow"]          # 取最新交易日净流入
        recent = sorted_flows[:5]
        total_5d = sum(f["MainNetFlow"] for f in recent)
        consec = compute_consecutive(flows, "in" if today_net > 0 else "out")
        stock_scores.append({
            "code": code, "name": name,
            "today_net": today_net, "total_5d": total_5d, "consec": consec,
        })

    stock_scores.sort(key=lambda x: x["today_net"], reverse=True)

    top_in, top_out = [], []
    for s in stock_scores:
        if s["today_net"] > 0 and s["consec"] >= 1:
            net_in = round(abs(s["today_net"]) / 1e8, 1)
            if net_in >= 0.5:
                top_in.append({"code": s["code"], "name": s["name"],
                               "net_in": net_in, "unit": "亿", "day_count": s["consec"]})
    top_in = top_in[:8]

    for s in sorted(stock_scores, key=lambda x: x["today_net"]):
        if s["today_net"] < 0 and s["consec"] >= 1:
            net_out = round(abs(s["today_net"]) / 1e8, 1)
            if net_out >= 0.5:
                top_out.append({"code": s["code"], "name": s["name"],
                                "net_out": net_out, "unit": "亿", "day_count": s["consec"]})
    top_out = top_out[:8]

    data_available = bool(top_in or top_out)
    result = {
        "update_time": now.strftime("%Y-%m-%d %H:%M"),
        "data_available": data_available,
        "top_main_in": top_in,
        "top_main_out": top_out,
        "status": "ok" if data_available else "no_data_today",
        "note": "" if data_available else "当日无符合阈值(>=0.5亿)的主力异动",
    }
    _save(result)
    if data_available:
        print(f"   主力净流入: {len(top_in)} 只")
        for s in top_in[:5]:
            print(f"     {s['name']} +{s['net_in']}{s['unit']} 连{s['day_count']}日")
        print(f"   主力净流出: {len(top_out)} 只")
        for s in top_out[:5]:
            print(f"     {s['name']} -{s['net_out']}{s['unit']} 连{s['day_count']}日")
    print(f"   更新时间: {result['update_time']}")
    return result

def _save(result):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 已保存: {OUTPUT_FILE}")

if __name__ == "__main__":
    from fetch_logger import record_success, record_failure
    try:
        main()
        record_success(__file__)
    except Exception as e:
        record_failure(__file__, str(e))
        raise
