#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
南向资金个股明细 — 独立获取脚本

用途：小九单位网络运行（阿狸咪家IP被东方财富push2接口封禁）

运行方式:
  cd E:/workspace/stock-scanner && python fetch_south_individual.py

注意：
  1. 如果成功，会更新 data/north_fund.json 中的 south_individual 字段
  2. 需要随后运行 update_data_v2.py --fast && deploy_now.py 部署到前端
  3. 如果失败（IP仍被封），保持原状不报错

交接给小九 2026-06-24
"""
import os
import json
import datetime
from fetch_logger import record_success, record_failure

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "north_fund.json")


def fetch_south_individual():
    """获取南向资金个股净买入排行（流入TOP5 + 流出TOP5）"""
    try:
        import akshare as ak
        df = ak.stock_hsgt_individual_em(symbol="南向")
        if df is None or len(df) == 0:
            print("  ⚠️ 返回空数据")
            return None

        # 按当日成交净买额降序
        if "当日成交净买额" not in df.columns:
            print("  ⚠️ 数据无'当日成交净买额'列")
            return None

        df = df.dropna(subset=["当日成交净买额"]).copy()
        df["_net"] = df["当日成交净买额"].astype(float)
        df = df.sort_values("_net", ascending=False)

        top_buy = []
        for _, row in df.head(5).iterrows():
            top_buy.append({
                "name": str(row.get("名称", "")),
                "code": str(row.get("代码", "")),
                "net_buy": round(float(row["当日成交净买额"]), 2),
            })

        top_sell = []
        df_asc = df.sort_values("_net", ascending=True)
        for _, row in df_asc.head(5).iterrows():
            val = float(row["当日成交净买额"])
            if val >= 0:  # 全部都是流入就不展示流出
                break
            top_sell.append({
                "name": str(row.get("名称", "")),
                "code": str(row.get("代码", "")),
                "net_buy": round(val, 2),
            })

        result = {"top_buy": top_buy, "top_sell": top_sell}
        print(f"  ✅ 成功! 流入{len(top_buy)}只 流出{len(top_sell)}只")
        return result
    except Exception as e:
        print(f"  ❌ 失败: {type(e).__name__}: {str(e)[:80]}")
        record_failure(__file__, f"{type(e).__name__}: {str(e)[:120]}")
        return None


def main():
    print("=" * 50)
    print("南向资金个股明细获取脚本")
    print(f"运行时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 家用机(阿狸咪)IP被东方财富push2接口封禁，本脚本应由单位机(小九)运行
    role = ""
    try:
        with open(os.path.join(BASE_DIR, ".machine_role"), "r", encoding="utf-8") as f:
            role = f.read().strip()
    except Exception:
        pass
    if role == "ALIMI":
        print("\n⏭️ 本机为家用机(ALIMI)，IP被东方财富封禁，跳过南向个股抓取。")
        print("   数据应由单位机(小九, 早1分钟运行)提供。")
        record_success(__file__)  # 本机按设计跳过，仍记一条使审计可见
        return 0

    # 获取数据
    print("\n1. 获取南向个股明细...")
    individual = fetch_south_individual()

    if individual is None:
        print("\n⚠️ 获取失败（可能是IP被封），未修改数据文件")
        print("   建议: 换个网络环境重试，或等东方财富解封")
        return 0

    # 读取现有 north_fund.json
    print("\n2. 更新 north_fund.json...")
    data = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"  警告: 读取原文件失败 {e}，将创建新文件")

    # 更新 south_individual
    data["south_individual"] = individual
    data["_south_individual_update_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 写回文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  ✅ 已更新: {OUTPUT_FILE}")
    print(f"  流入TOP1: {individual['top_buy'][0]['name']} +{individual['top_buy'][0]['net_buy']}亿")
    record_success(__file__)

    print("\n3. 后续步骤（手动执行）:")
    print("   python update_data_v2.py --fast")
    print("   python deploy_now.py --force")
    print("\n" + "=" * 50)
    print("完成!")
    return 0


if __name__ == "__main__":
    exit(main())
