#!/usr/bin/env python3
"""
fetch_etf_daily_monitor.py
股票型ETF日监控（华宝风格）——从 westock MCP 拉取真实数据
输出: data/etf_daily_monitor.json
数据源: westock data_etf（全市场ETF列表+资金流）+ data_fund_flow（单只净流入）
规则：
  - 不造假，无数据时 no_data=true
  - TOP10 按净流入排序，含涨跌幅
  - 分类统计：宽基/行业主题/跨境
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
os.makedirs(DATA_DIR, exist_ok=True)


def fetch_via_westock():
    """通过 akshare fund_etf_spot_em 拉取全市场ETF主力净流入数据。
    数据含：名称/代码/最新价/涨跌幅/主力净流入-净额/成交额等
    """
    try:
        import akshare as ak

        print("  [etf_daily] 使用 akshare fund_etf_spot_em 拉取ETF全量数据...")
        df = ak.fund_etf_spot_em()
        if df is not None and len(df) > 0:
            # 转换为记录列表，保留关键字段
            records = []
            for _, row in df.iterrows():
                net = row.get("主力净流入-净额")
                if net is None or (isinstance(net, float) and str(net) == 'nan'):
                    continue
                records.append({
                    "name": str(row.get("名称", "")),
                    "code": str(row.get("代码", "")),
                    "net_inflow": float(net) / 1e4,  # 元→万元
                    "pct_chg": float(row.get("涨跌幅", 0)) if row.get("涨跌幅") else 0,
                    "amount": float(row.get("成交额", 0)) / 1e8 if row.get("成交额") else 0,  # 元→亿
                    "turnover": float(row.get("换手率", 0)) if row.get("换手率") else 0,
                })
            return records
    except ImportError:
        print("  [etf_daily] akshare 不可用")
    except Exception as e:
        print(f"  [etf_daily] 拉取失败: {e}")

    return None


def classify_etf(name):
    """简单分类：宽基/行业主题/跨境"""
    broad_kw = ["300", "500", "1000", "50", "180", "创业板", "科创", "A500", "综指", "上证", "沪深", "中证"]
    cross_kw = ["港股", "恒生", "H股", "纳指", "标普", "德国", "日本", "印度", "越南", "美国", "MSCI", "富时"]
    for kw in cross_kw:
        if kw in name:
            return "跨境"
    for kw in broad_kw:
        if kw in name:
            return "宽基"
    return "行业/主题"


def main():
    print("📊 股票型ETF日监控数据抓取...")

    records = fetch_via_westock()

    if not records or len(records) == 0:
        # 无真实数据，写 no_data 标记
        result = {
            "no_data": True,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "note": "数据源暂不可用（非交易时段或API限流），不填充模拟数据"
        }
    else:
        # 分类统计
        broad_net = sum(r["net_inflow"] for r in records if classify_etf(r["name"]) == "宽基")
        sector_net = sum(r["net_inflow"] for r in records if classify_etf(r["name"]) == "行业/主题")
        cross_net = sum(r["net_inflow"] for r in records if classify_etf(r["name"]) == "跨境")

        top_inflow = sorted([r for r in records if r["net_inflow"] > 0], key=lambda x: x["net_inflow"], reverse=True)[:10]
        top_outflow = sorted([r for r in records if r["net_inflow"] < 0], key=lambda x: x["net_inflow"])[:10]

        result = {
            "no_data": False,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_net_inflow": round(sum(r["net_inflow"] for r in records), 2),
            "broad_net": round(broad_net, 2),
            "sector_net": round(sector_net, 2),
            "cross_net": round(cross_net, 2),
            "top_inflow": [{"name": r["name"], "code": r["code"], "net_inflow": round(r["net_inflow"], 2), "pct_chg": round(r["pct_chg"], 2)} for r in top_inflow],
            "top_outflow": [{"name": r["name"], "code": r["code"], "net_outflow": round(r["net_inflow"], 2), "pct_chg": round(r["pct_chg"], 2)} for r in top_outflow],
            "source": "akshare fund_etf_fund_daily_rank",
        }

    out_path = DATA_DIR / "etf_daily_monitor.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    status = "无数据(no_data)" if result.get("no_data") else f'{len(result.get("top_inflow", []))}流入/{len(result.get("top_outflow", []))}流出'
    print(f"  ✅ 已保存：{out_path} ({status})")


if __name__ == "__main__":
    main()
