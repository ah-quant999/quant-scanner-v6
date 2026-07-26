#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
maintain_industry_map.py — 个股元数据周度维护（补足新股票 / 删除退市股 / 回填股池）
====================================================================================

职责（对应用户铁律「每周补足新股票的一切、删除退市股的一切」）：
  1. 删除退市股：industry_map / candidate_pool / gold_pool 中「不在 stock_names 宇宙」的
     股票一律清除（退市、更名、暂停上市都不再出现在 stock_names 里）。
  2. 补足新股票：
     - 概念：合并 concept_map.json（由 fetch_concept_map.py 生成）进 industry_map；
     - 行业：对仍缺 industry 的股票用 BaoStock 轻量补抓（best-effort，失败留空待周日全量重建）；
  3. 回填股池：把 industry / board / concepts / sectors 注入 candidate_pool.json 与
     gold_pool.json，使规范股池文件本身「行业、板块、概念齐备」。

铁律：
  - 只增删/补字段，绝不破坏既有有效数据；industry 旧值保留。
  - 任何单步失败不阻塞整体，打印告警继续。
  - 全部动作幂等，可重复运行。

用法：
  python maintain_industry_map.py                  # 完整维护（合并概念 + 删退 + 补行业 + enrich 股池）
  python maintain_industry_map.py --rebuild-concept # 先重跑 fetch_concept_map.py 再合并（周度任务用）
  python maintain_industry_map.py --dry-run        # 只打印将要删除/补齐的数量，不落盘
"""
import os
import sys
import time
import json
import re
import argparse
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
STOCK_NAMES = os.path.join(DATA, "stock_names.json")
INDUSTRY_MAP = os.path.join(DATA, "industry_map.json")
CONCEPT_MAP = os.path.join(DATA, "concept_map.json")
CANDIDATE = os.path.join(DATA, "candidate_pool.json")
GOLD = os.path.join(DATA, "gold_pool.json")
FETCH_CONCEPT = os.path.join(BASE, "fetch_concept_map.py")


def log(msg):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), msg))


def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def key_of(full_code):
    """sh600000 / sz000001 / hk00700 -> sh_600000"""
    m = re.match(r"(sh|sz|hk|bj)(\d+)", str(full_code))
    return "%s_%s" % (m.group(1), m.group(2)) if m else str(full_code)


def derive_board(code, market):
    """从代码推导交易所板块（板_label 缺失时兜底）。"""
    c = str(code)
    if market == "hk":
        return "港股"
    if c.startswith("688") or c.startswith("8") or c.startswith("4"):
        if c.startswith("688"):
            return "科创板"
        return "北交所"
    if market == "sh":
        return "主板"
    if market == "sz":
        return "创业板" if c.startswith("3") else "主板"
    return "主板"


def build_universe():
    """返回 (key_set, bare_set) 当前上市股票宇宙。"""
    d = load_json(STOCK_NAMES, [])
    keys, bare = set(), set()
    for it in d:
        k = key_of(it.get("full_code", ""))
        keys.add(k)
        bare.add(str(it.get("code", "")))
    return keys, bare


def backfill_industry_baostock(missing_keys):
    """用 BaoStock 轻量补抓缺失 industry（best-effort）。返回 {key: industry}。"""
    if not missing_keys:
        return {}
    try:
        import baostock as bs
    except Exception as e:
        log("[WARN] BaoStock 不可用，跳过行业补抓: %s" % e)
        return {}
    out = {}
    try:
        bs.login()
        for k in missing_keys:
            pc = k.split("_", 1)[1] if "_" in k else k
            try:
                rs = bs.query_stock_industry(pc)
                ind = ""
                while rs.error_code == "0" and rs.next():
                    ind = rs.get_row_data()[1] if len(rs.get_row_data()) > 1 else ind
                if ind:
                    out[k] = ind
            except Exception:
                pass
        bs.logout()
    except Exception as e:
        log("[WARN] BaoStock 登录失败: %s" % e)
    return out


def enrich_pool(stocks_dict, im_stocks, universe_keys):
    """给股池 dict（key->record）注入 industry/board/concepts/sectors，并返回 enriched 数量。"""
    n = 0
    for key, rec in stocks_dict.items():
        if not isinstance(rec, dict):
            continue
        # 行业 + 概念（来自 industry_map）
        im = im_stocks.get(key)
        if im:
            ind = im.get("industry")
            cons = im.get("concepts") or []
            if ind:
                rec["industry"] = ind
            if cons:
                rec["concepts"] = cons
        # 板块（board_label 优先，否则推导）
        board = rec.get("board_label") or rec.get("board")
        if not board:
            board = derive_board(rec.get("code", ""), rec.get("market", ""))
            rec["board_label"] = board
        rec["board"] = board
        # 标签聚合
        tags = []
        if rec.get("industry"):
            tags.append(rec["industry"])
        tags.extend(rec.get("concepts") or [])
        if tags:
            rec["sectors"] = tags
        n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild-concept", action="store_true", help="先重跑 fetch_concept_map.py")
    ap.add_argument("--dry-run", action="store_true", help="只统计不落盘")
    args = ap.parse_args()

    universe_keys, universe_bare = build_universe()
    log("宇宙股票数: %d" % len(universe_keys))

    # 0. 可选：重建概念映射
    if args.rebuild_concept and os.path.exists(FETCH_CONCEPT):
        log("重跑 fetch_concept_map.py ...")
        subprocess.run([sys.executable, FETCH_CONCEPT], check=False)

    # 1. 合并 concept_map -> industry_map（concepts 字段）
    cm = load_json(CONCEPT_MAP, {})
    cm_map = cm.get("map", {}) if isinstance(cm, dict) else {}
    im = load_json(INDUSTRY_MAP, {"stocks": {}})
    im_stocks = im.get("stocks", {})
    if cm_map:
        for k, cons in cm_map.items():
            if k in im_stocks:
                if not im_stocks[k].get("concepts"):
                    im_stocks[k]["concepts"] = cons
            else:
                im_stocks[k] = {"industry": "", "concepts": cons}
        im["stocks"] = im_stocks
        log("合并 concept_map：%d 只概念映射" % len(cm_map))

    # 2. 删除退市股（不在宇宙）
    purge_im = [k for k in im_stocks if k not in universe_keys and str(k).split("_", 1)[-1] not in universe_bare]
    for k in purge_im:
        im_stocks.pop(k, None)
    log("industry_map 将删除退市股: %d 只" % len(purge_im))

    # 3. 补行业（缺 industry 且仍在宇宙的）
    missing_ind = [k for k in im_stocks if k in universe_keys and not im_stocks[k].get("industry")]
    log("缺 industry 且仍在宇宙: %d 只，尝试 BaoStock 补抓" % len(missing_ind))
    back = backfill_industry_baostock(missing_ind)
    for k, ind in back.items():
        im_stocks[k]["industry"] = ind
    log("BaoStock 补抓成功: %d 只" % len(back))

    if not args.dry_run:
        im["stocks"] = im_stocks
        im["total_stocks"] = len(im_stocks)
        im["total_associations"] = len(im_stocks)
        save_json(INDUSTRY_MAP, im)
        log("已写回 industry_map.json")

    # 4. 清理并 enrich 股池
    cand = load_json(CANDIDATE, {"stocks": {}})
    gold = load_json(GOLD, {"stocks": {}})
    cstocks = cand.get("stocks", {})
    gstocks = gold.get("stocks", {})

    purge_cand = [k for k in cstocks if k not in universe_keys and str(k).split("_", 1)[-1] not in universe_bare]
    purge_gold = [k for k in gstocks if k not in universe_keys and str(k).split("_", 1)[-1] not in universe_bare]
    for k in purge_cand:
        cstocks.pop(k, None)
    for k in purge_gold:
        gstocks.pop(k, None)
    log("candidate_pool 将删退市: %d，gold_pool 将删退市: %d" % (len(purge_cand), len(purge_gold)))

    ec = enrich_pool(cstocks, im_stocks, universe_keys)
    eg = enrich_pool(gstocks, im_stocks, universe_keys)
    log("enrich candidate_pool: %d 只，gold_pool: %d 只" % (ec, eg))

    if not args.dry_run:
        cand["stocks"] = cstocks
        cand["total"] = len(cstocks)
        gold["stocks"] = gstocks
        save_json(CANDIDATE, cand)
        save_json(GOLD, gold)
        log("已写回 candidate_pool.json / gold_pool.json")

    # 5. 汇总
    no_ind = sum(1 for v in im_stocks.values() if not v.get("industry"))
    no_con = sum(1 for v in im_stocks.values() if not v.get("concepts"))
    log("=== 维护后 industry_map: %d 只 | 缺行业 %d | 缺概念 %d ===" % (len(im_stocks), no_ind, no_con))
    log("DONE")


if __name__ == "__main__":
    main()
