#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
概念涨跌幅排名 Top40（涨幅前20 + 跌幅前20）v2
=== 改用 同花顺(THS) 数据源，绕开被墙的 东财(EM) ===
用法：python fetch_concept_ranking_v2.py
输出：data/concept_ranking.json, data/concept_history.json
"""

import akshare as ak
import json
import datetime
import os
import time
import concurrent.futures

OUT = "data/concept_ranking.json"
HISTORY = "data/concept_history.json"
MAX_WORKERS = 12  # 并发线程数


def log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")


def get_concept_pct(name):
    """获取单概念板块涨幅(%)"""
    try:
        df = ak.stock_board_concept_info_ths(symbol=name)
        row = df[df['项目'] == '板块涨幅']
        if row.empty:
            return (name, None)
        pct_str = row['值'].values[0]
        pct_val = float(pct_str.replace('%', ''))
        return (name, pct_val)
    except Exception as e:
        log(f"  ⚠ {name}: {e}")
        return (name, None)


def fetch_concept_ranking():
    """获取概念板块涨跌幅排名（同花顺数据源）"""
    log("获取概念板块列表（同花顺）...")
    try:
        names_df = ak.stock_board_concept_name_ths()
        names = names_df['name'].tolist()
    except Exception as e:
        log(f"✗ 获取概念列表失败: {e}")
        return []
    log(f"✓ 共 {len(names)} 个概念板块")

    # 并发获取所有概念的涨跌幅
    log(f"并发获取{len(names)}个概念的涨跌幅（{MAX_WORKERS}线程）...")
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(get_concept_pct, names))
    elapsed = time.time() - t0

    valid = [(n, p) for n, p in results if p is not None]
    failed = len(names) - len(valid)
    log(f"✓ {len(valid)}/{len(names)} 个成功{f'（{failed}个跳过）' if failed else ''}，耗时 {elapsed:.0f}s")

    if len(valid) == 0:
        log("⚠ 全部失败，返回空")
        return []

    # 排序：涨幅从高到低
    valid.sort(key=lambda x: -x[1])

    # 涨幅前TOP_N + 跌幅前TOP_N
    TOP_N = 20
    top_gainers = valid[:TOP_N]
    top_losers = valid[-TOP_N:][::-1]

    ranking = []
    for name, pct in top_gainers:
        ranking.append({'name': name, 'pct': round(pct, 2)})
    for name, pct in top_losers:
        ranking.append({'name': name, 'pct': round(pct, 2)})

    return ranking


def main():
    log("概念涨跌幅排名 v2（同花顺数据源）")
    print("=" * 50)

    ranking = fetch_concept_ranking()
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not ranking:
        log("⚠ 获取失败，检查是否需要保留旧数据")
        old_data = None
        if os.path.exists(OUT):
            try:
                with open(OUT, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
            except:
                pass
        if old_data and old_data.get('ranking') and len(old_data['ranking']) > 0:
            log(f"✓ 保留上一份有效数据({len(old_data['ranking'])}条)，不覆盖")
            return
        else:
            output = {'update_time': now_str, 'data_available': False, 'ranking': []}
            os.makedirs(os.path.dirname(OUT), exist_ok=True)
            with open(OUT, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            log(f"✓ 已写入空结构: {OUT}")
            return

    output = {
        'update_time': now_str,
        'ranking': ranking,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 概念历史（用于前端"连X天"统计）
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    concept_day = {}
    for item in ranking:
        concept_day[item['name']] = item['pct']
    history = {}
    if os.path.exists(HISTORY):
        with open(HISTORY, 'r', encoding='utf-8') as f:
            history = json.load(f)
    history[today_str] = concept_day
    keys = sorted(history.keys())
    if len(keys) > 10:
        for old in keys[:-10]:
            del history[old]
    with open(HISTORY, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    log(f"✓ 完成！共 {len(ranking)} 个概念")
    for i, x in enumerate(ranking, 1):
        arrow = '▲' if x['pct'] > 0 else '▼'
        print(f"  {i}. {x['name']} {arrow}{abs(x['pct']):.2f}%")


if __name__ == "__main__":
    from fetch_logger import record_success, record_failure
    try:
        main()
        record_success(__file__)
    except Exception as e:
        record_failure(__file__, str(e))
        raise
