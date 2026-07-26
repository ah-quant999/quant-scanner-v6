#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_concept_map.py — 构建「股票→概念」反向映射，并回填 industry_map.json 的 concepts 字段
====================================================================================

数据去向：
  - data/concept_map.json      原始缓存：{update_time, total_stocks, map: {code: [concepts]}}
  - data/industry_map.json     规范个股元数据仓：每只股票补充 concepts 字段（industry 绝不覆盖）

用户铁律：
  1. 重要数据必须有备用源；东财概念成分股接口（stock_board_concept_cons_em）当前可用，
     若整体失败则跳过、沿用旧值，不阻塞、不过问。
  2. 别再丢数据：只填充 concepts 字段，industry 旧值一律保留；已有 concepts 且非空时跳过
     （除非 --force），崩溃可续跑。
  3. 概念源覆盖全市场（遍历东财全部概念板块的成分股），不局限于股池。

数据源：
  S1  akshare.stock_board_concept_name_em()      概念板块列表（495 个）
  S2  akshare.stock_board_concept_cons_em(name)   单个概念的成分股
      （少数概念可能限频失败，跳过不影响整体）

用法：
  python fetch_concept_map.py                 # 增量构建 + 回填（推荐，周度任务调用）
  python fetch_concept_map.py --force         # 强制覆盖已有 concepts
"""
import os
import sys
import time
import json
import argparse

import akshare as ak

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(DATA, "concept_map.json")
INDUSTRY_MAP = os.path.join(DATA, "industry_map.json")


def prefix_code(code):
    """裸码加 sh_/sz_/bj_ 前缀，对齐 industry_map 的 key 格式。"""
    code = str(code).strip()
    if code.startswith(("sh_", "sz_", "hk_", "bj_")):
        return code
    if len(code) == 6 and code.isdigit():
        if code.startswith("6"):
            return "sh_" + code
        if code.startswith(("0", "3")):
            return "sz_" + code
        if code.startswith(("8", "4")):
            return "bj_" + code
    return code


def build_reverse_map(force=False):
    """遍历全部概念板块，反向聚合 code -> set(concepts)。"""
    print("[1/3] 获取东财概念板块列表 ...")
    df = ak.stock_board_concept_name_em()
    names = df["板块名称"].tolist()
    total = len(names)
    print("    共 %d 个概念板块" % total)

    rev = {}  # code -> set(concepts)
    failed = 0
    for i, name in enumerate(names, 1):
        try:
            cons = ak.stock_board_concept_cons_em(symbol=name)
            for _, row in cons.iterrows():
                c = prefix_code(row.get("代码"))
                rev.setdefault(c, set()).add(name)
        except Exception as e:  # 单个概念失败不影响整体
            failed += 1
            if failed <= 5:
                print("    [WARN] 概念 '%s' 失败: %s" % (name, e))
        if i % 100 == 0:
            print("    进度 %d/%d，已映射 %d 只" % (i, total, len(rev)))
    print("    完成：映射 %d 只，跳过失败概念 %d 个" % (len(rev), failed))
    return rev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="强制覆盖已有 concepts")
    args = ap.parse_args()

    t0 = time.time()
    rev = build_reverse_map(args.force)

    # 写 concept_map.json 原始缓存
    concept_map = {k: sorted(v) for k, v in rev.items()}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(
            {
                "update_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_stocks": len(concept_map),
                "map": concept_map,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print("[2/3] 写入 concept_map.json：%d 只" % len(concept_map))

    # 合并进 industry_map.json（只动 concepts，保留 industry）
    with open(INDUSTRY_MAP, "r", encoding="utf-8") as f:
        im = json.load(f)
    stocks = im.get("stocks", {})
    filled = 0
    for key, cons in concept_map.items():
        if key in stocks:
            old = stocks[key].get("concepts") or []
            if args.force or not old:
                stocks[key]["concepts"] = cons
                filled += 1
        else:
            # 属于某概念但不在 industry_map → 新建记录（只给 concepts，industry 留空待补）
            stocks[key] = {"industry": "", "concepts": cons}
            filled += 1
    im["stocks"] = stocks
    im["total_associations"] = len(stocks)
    with open(INDUSTRY_MAP, "w", encoding="utf-8") as f:
        json.dump(im, f, ensure_ascii=False, indent=2)
    print("[3/3] 合并进 industry_map.json：填充/更新 %d 只的 concepts 字段" % filled)
    print("    耗时 %.1f 秒" % (time.time() - t0))


if __name__ == "__main__":
    main()
