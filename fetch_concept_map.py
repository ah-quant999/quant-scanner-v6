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

数据源（2026-07-28 修正）：
  直接请求东财 push2.eastmoney.com HTTP API：
    S1  /api/qt/clist/get?fs=m:90 t:3 f:!50&fields=f12,f14      概念板块列表
    S2  /api/qt/clist/get?fs=b:{概念代码} f:!50&fields=f12,f14  单个概念的成分股
  原 akshare 函数因默认 fields 过长，在本机网络下被服务端 reset，故改为精简字段直连。

用法：
  python fetch_concept_map.py                 # 增量构建 + 回填（推荐，周度任务调用）
  python fetch_concept_map.py --force         # 强制覆盖已有 concepts
"""
import os
import sys
import time
import json
import argparse
import random

import requests

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
OUT = os.path.join(DATA, "concept_map.json")
INDUSTRY_MAP = os.path.join(DATA, "industry_map.json")

# 2026-07-28：东财概念接口偶发限流/reset，增加统一重试+限流。
# 单点重试预算 <= 2s（项目铁律），这里 max_retry=2，backoff 约 0.3~1.2s。
MAX_RETRY = 2
BASE_DELAY = 0.25
CONCEPT_DELAY = 0.15  # 每个概念板块间强制休眠，降低被 reset 概率


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


def _em_fetch(url, params, label):
    """直接向东财 API 发请求，失败按 MAX_RETRY 重试。"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Referer": "https://quote.eastmoney.com/center/boardlist.html",
    }
    for attempt in range(MAX_RETRY + 1):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=(8, 20))
            r.raise_for_status()
            return r.json()["data"]
        except Exception as e:
            wait = BASE_DELAY * (2 ** attempt) + random.uniform(0, 0.3)
            if attempt < MAX_RETRY:
                print("    [RETRY] %s 第%d次失败，%.2fs后重试: %s" % (label, attempt + 1, wait, e))
                time.sleep(wait)
            else:
                print("    [DROP] %s 最终失败: %s" % (label, e))
    return None


def _fetch_all_pages(url, params, label):
    """处理东财分页 API，返回所有 diff 项列表。"""
    all_items = []
    data = _em_fetch(url, params, label)
    if data is None:
        return None
    page1 = data.get("diff") or []
    all_items.extend(page1)
    total = data.get("total", 0)
    per_page = len(page1) if page1 else 1
    total_pages = (total + per_page - 1) // per_page if per_page else 1
    for page in range(2, total_pages + 1):
        p2 = params.copy()
        p2["pn"] = str(page)
        data = _em_fetch(url, p2, "%s page %d" % (label, page))
        if data is None:
            break
        all_items.extend(data.get("diff") or [])
        time.sleep(random.uniform(0.1, 0.3))
    return all_items


def build_reverse_map(force=False):
    """遍历全部概念板块，反向聚合 code -> set(concepts)。"""
    print("[1/3] 获取东财概念板块列表 ...")
    name_items = _fetch_all_pages(
        "http://79.push2.eastmoney.com/api/qt/clist/get",
        {
            "pn": "1", "pz": "100", "po": "1", "np": "1",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2", "invt": "2", "fid": "f12",
            "fs": "m:90 t:3 f:!50",
            "fields": "f12,f14",
        },
        "概念板块列表",
    )
    if name_items is None:
        print("[FATAL] 概念板块列表获取失败，保留旧 concept_map.json")
        return None
    names = [(it["f12"], it["f14"]) for it in name_items if "f12" in it and "f14" in it]
    total = len(names)
    print("    共 %d 个概念板块" % total)

    rev = {}  # code -> set(concepts)
    failed = 0
    for i, (code, name) in enumerate(names, 1):
        cons_items = _fetch_all_pages(
            "http://29.push2.eastmoney.com/api/qt/clist/get",
            {
                "pn": "1", "pz": "100", "po": "1", "np": "1",
                "ut": "bd1d9ddb04089700cf9c27f6f7426281",
                "fltt": "2", "invt": "2", "fid": "f12",
                "fs": "b:%s f:!50" % code,
                "fields": "f12,f14",
            },
            "概念 '%s'" % name,
        )
        if cons_items is not None:
            for it in cons_items:
                c = prefix_code(it.get("f12"))
                if c:
                    rev.setdefault(c, set()).add(name)
        else:
            failed += 1
            if failed <= 10:
                print("    [WARN] 概念 '%s' 跳过" % name)
        if i % 100 == 0:
            print("    进度 %d/%d，已映射 %d 只，失败 %d 个" % (i, total, len(rev), failed))
        time.sleep(CONCEPT_DELAY)
    print("    完成：映射 %d 只，跳过失败概念 %d 个" % (len(rev), failed))
    return rev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="强制覆盖已有 concepts")
    args = ap.parse_args()

    t0 = time.time()
    rev = build_reverse_map(args.force)
    if rev is None:
        print("[EXIT] 网络/源异常，未覆盖旧数据，等待下次调度自动重试。")
        sys.exit(0)

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
