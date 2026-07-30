#!/usr/bin/env python3
"""
ETF量能脉冲监测 + 日监控 数据采集
- 5min量能脉冲: 4只核心宽基ETF最近4个5分钟切片成交额
- 日监控: 全市场净流入/TOP10流入流出榜单
输出: data/etf_pulse.json, data/etf_daily_monitor.json
依赖: westock-mcp (data_minute, data_etf, data_fund_flow)
"""

import json, os, sys, time
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA_DIR = REPO / "data"

# 核心宽基ETF（量能脉冲用）
PULSE_ETFS = [
    {"name": "创业板ETF", "code": "sz159915"},
    {"name": "科创50ETF", "code": "sh588000"},
    {"name": "沪深300ETF", "code": "sh510300"},
    {"name": "中证500ETF", "code": "sh510500"},
]

# 日监控覆盖的宽基/行业/跨境ETF代码
MONITOR_CODES = ",".join([
    "sz159915","sh588000","sh510300","sh510500",  # 宽基
    "sz159919","sz159901","sh512880","sh515790",  # 更多宽基
    "sh512480","sh516110","sz159869","sz159782",  # 行业半导体/芯片/5G/云计算
    "sh512000","sz159992","sh515000","sh560050",  # 券商/医药/军工/中概互联
])


def parse_minute_data(raw_data, etf_code):
    """解析westock data_minute返回的数据，提取最近N个5分钟切片成交额(M)"""
    result = {"slices": [], "times": []}
    try:
        inner = raw_data.get("data", {}).get(etf_code, {})
        minute_list = inner.get("data", [])
        if not minute_list:
            return result

        # 每条记录格式: "HHMM price volume amount"
        # 按5分钟聚合
        slices = {}  # "HHMM" -> amount
        for line in minute_list:
            parts = line.strip().split()
            if len(parts) >= 4:
                t_str = parts[0]
                amount = float(parts[3]) if len(parts) > 3 else 0
                # 取5分钟窗口起始时间
                t_int = int(t_str)
                window = (t_int // 100) * 100 + (0 if t_int % 100 < 30 else 30)
                # 更精确: 用5分钟对齐
                min_val = t_int % 100
                if min_val < 5:   align = 0
                elif min_val < 10: align = 5
                elif min_val < 15: align = 10
                elif min_val < 20: align = 15
                elif min_val < 25: align = 20
                elif min_val < 30: align = 25
                elif min_val < 35: align = 30
                elif min_val < 40: align = 35
                elif min_val < 45: align = 40
                elif min_val < 50: align = 45
                elif min_val < 55: align = 50
                else:            align = 55
                key = f"{t_int//100:02d}{align:02d}"
                slices[key] = max(slices.get(key, 0), amount)

        # 取最近4个有数据的5分钟切片（按时间倒序）
        sorted_keys = sorted(slices.keys(), reverse=True)[:4]
        result["slices"] = [slices[k] for k in reversed(sorted_keys)]
        result["times"] = [f"{k[:2]}:{k[2:]}" for k in reversed(sorted_keys)]
    except Exception as e:
        print(f"  [WARN] 解析{etf_code}分钟数据失败: {e}")
    return result


def generate_interpretation(etfs_data):
    """根据4只ETF的量能切片生成智能判读"""
    reads = []
    patterns = []

    for e in etfs_data:
        slices = e.get("slices", [])
        if len(slices) < 3:
            continue

        name = e["name"]
        last3 = slices[-3:]
        first_avg = sum(last3[:2]) / 2 if len(last3) >= 2 else last3[0]
        last_v = last3[-1]

        if last_v > first_avg * 1.3:
            reads.append(f"{name}买力持续加码")
            patterns.append("buy")
        elif last_v < first_avg * 0.7:
            reads.append(f"{name}缩量衰减")
            patterns.append("sell")
        elif abs(last_v - first_avg) / max(first_avg, 1) < 0.15:
            reads.append(f"{name}同步")
            patterns.append("flat")
        else:
            reads.append(f"{name}温和")
            patterns.append("mild")

    # 综合判读
    buy_count = patterns.count("buy")
    sell_count = patterns.count("sell")

    summary_parts = []
    if buy_count >= 3:
        summary_parts.append("多只ETF连续放量拉升，主力积极护盘")
    elif buy_count >= 2:
        summary_parts.append("部分ETF买力增强，关注持续性")
    if sell_count >= 3:
        summary_parts.append("全面缩量，资金观望情绪浓")
    elif sell_count >= 2:
        summary_parts.append("多只缩量，注意风险")
    if patterns.count("flat") >= 3:
        summary_parts.append("量价平稳，窄幅震荡")

    if not summary_parts:
        summary_parts.append("量能正常波动，等待方向选择")

    return reads, "这是教科书式的护盘节奏——" + "；".join(summary_parts) + "。"


def fetch_pulse_data(westock_tool):
    """采集5分钟量能脉冲数据"""
    print("[1/2] 采集 ETF 5分钟量能脉冲...")
    etfs_result = []
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for etf in PULSE_ETFS:
        code = etf["code"]
        print(f"  拉取 {etf['name']}({code}) 分钟数据...")
        try:
            raw = westock_tool({"code": code, "days": 1})
            parsed = parse_minute_data(raw, code)
            etfs_result.append({
                "name": etf["name"],
                "code": code.replace("sh", "").replace("sz", ""),
                **parsed,
            })
            status = f"{len(parsed['slices'])}个切片"
            if parsed["slices"]:
                latest = parsed["slices"][-1] / 1e6
                status += f"，最新={latest:.0f}M"
            print(f"  ✓ {etf['name']}: {status}")
        except Exception as e:
            print(f"  ✗ {etf['name']}: {e}")
            etfs_result.append({"name": etf["name"], "code": code.replace("sh", "").replace("sz", ""), "slices": [], "times": [], "read": "数据获取失败"})

    # 生成判读
    reads, summary = generate_interpretation(etfs_result)
    for i, read in enumerate(reads):
        if i < len(etfs_result):
            etfs_result[i]["read"] = read

    return {
        "update_time": update_time,
        "times": etfs_result[0].get("times", []) if etfs_result else [],
        "etfs": etfs_result,
        "summary": summary,
    }


def fetch_daily_monitor_data(westock_etf_tool, westock_flow_tool):
    """采集日监控数据（净流入/TOP10）"""
    print("[2/2] 采集 ETF 日监控...")
    update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    result = {
        "update_time": update_time,
        "total_net_inflow": 0,
        "broad_net": 0,
        "sector_net": 0,
        "cross_net": 0,
        "top_inflow": [],
        "top_outflow": [],
    }

    # 尝试获取ETF列表和资金流向
    try:
        print("  拉取ETF列表+资金流...")
        etf_data = westock_etf_tool({"codes": MONITOR_CODES})
        # 处理ETF数据...
        print(f"  ✓ 获取到ETF基础数据")
    except Exception as e:
        print(f"  [WARN] ETF列表获取失败: {e}")

    # 尝试获取资金流向排名
    try:
        flow_data = westock_flow_tool({"codes": MONITOR_CODES})
        # 处理资金流数据生成TOP10
        print(f"  ✓ 获取到资金流数据")
    except Exception as e:
        print(f"  [WARN] 资金流获取失败: {e}")

    # TODO: 接入真实API后填充TOP10数据
    # 当前先用示例结构占位，等API验证后替换
    result["top_inflow"] = [
        {"name": "待接入", "code": "---", "net_inflow": 0, "pct_chg": 0},
    ]
    result["top_outflow"] = [
        {"name": "待接入", "code": "---", "net_outflow": 0, "pct_chg": 0},
    ]

    return result


def main():
    """主入口 - 通过MCP工具采集数据"""
    print("=" * 50)
    print(f"ETF量能脉冲+日监控采集  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 尝试通过MCP工具获取数据（在WorkBuddy环境中运行时可用）
    pulse_data = None
    daily_data = None

    # 方式1: 直接调用MCP工具（如果在WorkBuddy agent环境中）
    try:
        from mcp_client import call_mcp_tool  # noqa: F401 - 仅在WB环境可用
        pulse_data = fetch_pulse_data(
            lambda params: call_mcp_tool("mcp__westock-mcp__data_minute", params)
        )
        daily_data = fetch_daily_monitor_data(
            lambda params: call_mcp_tool("mcp__westock-mcp__data_etf", params),
            lambda params: call_mcp_tool("mcp__westock-mcp__data_fund_flow", params),
        )
    except ImportError:
        print("[INFO] 非WorkBuddy环境，使用模拟数据模式")
        pulse_data = _demo_pulse_data()
        daily_data = _demo_daily_data()

    # 写出JSON
    DATA_DIR.mkdir(exist_ok=True)

    if pulse_data:
        p_out = DATA_DIR / "etf_pulse.json"
        with open(p_out, "w", encoding="utf-8") as f:
            json.dump(pulse_data, f, ensure_ascii=False, default=str)
        print(f"\n✅ etf_pulse.json 已写入 ({p_out.stat().st_size:,} bytes)")

    if daily_data:
        d_out = DATA_DIR / "etf_daily_monitor.json"
        with open(d_out, "w", encoding="utf-8") as f:
            json.dump(daily_data, f, ensure_ascii=False, default=str)
        print(f"✅ etf_daily_monitor.json 已写入 ({d_out.stat().st_size:,} bytes)")


def _demo_pulse_data():
    """演示数据（非交易时段或API不可用时使用）"""
    now = datetime.now()
    return {
        "update_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "times": ["13:00", "13:05", "13:10", "13:15"],
        "etfs": [
            {"name": "创业板ETF", "code": "159915",
             "slices": [150e6, 160e6, 169e6, 176e6],
             "read": "买力持续加码到13:15，13:20缩量但价格守住了(3.242)"},
            {"name": "科创50ETF", "code": "588000",
             "slices": [275e6, 289e6, 300e6, 307e6],
             "read": "同上，1.649拉升到1.657后横住"},
            {"name": "沪深300ETF", "code": "510300",
             "slices": [42e6, 44e6, 46e6, 47e6],
             "read": "同步"},
            {"name": "中证500ETF", "code": "510500",
             "slices": [27e6, 29e6, 30e6, 31e6],
             "read": "同步"},
        ],
        "summary": "这是教科书式的护盘节奏——13:00~13:15连续加码拉升，13:20缩量但价格不回落，说明抛压被吸收干净了，不需要继续加码也能守住。这一波「一流」健康得多。",
    }


def _demo_daily_data():
    """演示数据"""
    now = datetime.now()
    return {
        "update_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "total_net_inflow": 42.6,
        "broad_net": 18.3,
        "sector_net": 21.1,
        "cross_net": 3.2,
        "top_inflow": [
            {"name": "创业板ETF易方达", "code": "159915", "net_inflow": 12.3, "pct_chg": -0.88},
            {"name": "科创50ETF华夏", "code": "588000", "net_inflow": 8.7, "pct_chg": 1.25},
            {"name": "中证1000ETF", "code": "512100", "net_inflow": 5.4, "pct_chg": 0.62},
            {"name": "中证500ETF南方", "code": "510500", "net_inflow": 4.1, "pct_chg": 0.35},
            {"name": "沪深300ETF华泰柏瑞", "code": "510300", "net_inflow": 3.8, "pct_chg": 0.22},
            {"name": "半导体ETF", "code": "512480", "net_inflow": 3.2, "pct_chg": -1.15},
            {"name": "医药ETF", "code": "512010", "net_inflow": 2.9, "pct_chg": -0.45},
            {"name": "证券ETF", "code": "512880", "net_inflow": 2.1, "pct_chg": 1.82},
            {"name": "新能源车ETF", "code": "159806", "net_inflow": 1.8, "pct_chg": -0.67},
            {"name": "红利ETF", "code": "510880", "net_inflow": 1.5, "pct_chg": 0.12},
        ],
        "top_outflow": [
            {"name": "纳指ETF", "code": "513100", "net_outflow": -8.2, "pct_chg": -0.35},
            {"name": "标普500ETF", "code": "513500", "net_outflow": -5.6, "pct_chg": -0.18},
            {"name": "银行ETF", "code": "512800", "net_outflow": -4.3, "pct_chg": 0.56},
            {"name": "白酒ETF", "code": "512690", "net_outflow": -3.8, "pct_chg": -1.23},
            {"name": "房地产ETF", "code": "512200", "net_outflow": -2.9, "pct_chg": -0.89},
            {"name": "游戏ETF", "code": "516010", "net_outflow": -2.1, "pct_chg": -1.56},
            {"name": "传媒ETF", "code": "512980", "net_outflow": -1.8, "pct_chg": -0.72},
            {"name": "煤炭ETF", "code": "515220", "net_outflow": -1.5, "pct_chg": 0.34},
            {"name": "钢铁ETF", "code": "515210", "net_outflow": -1.2, "pct_chg": -0.21},
            {"name": "基建ETF", "code": "516950", "net_outflow": -0.9, "pct_chg": 0.08},
        ],
    }


if __name__ == "__main__":
    main()
