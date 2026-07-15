#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_multi_resonance_daily.py — 每日多维共振TOP10快照追加到历史数据库

数据源: TOP10_DAILY.json（每日扫描结果）
输出:   data/multi_resonance_history.json（按日期累积）
用途:   multi_resonance.html 的"冠军统计/时间轴/排名趋势"页面

调用时机:
  - batch_update.py 盘后任务自动调用
  - 也可单独运行: python update_multi_resonance_daily.py
"""
import json, os, sys
from datetime import datetime, date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORY_FILE = os.path.join(DATA_DIR, "multi_resonance_history.json")
SOURCE_FILE = os.path.join(DATA_DIR, "TOP10_DAILY.json")

# 只记录 score >= 70 的高质量信号（和前端筛选一致)
MIN_SCORE = 70


def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_today_str():
    """返回今天的日期字符串(YYYY-MM-DD)，如果是非交易时间则用最新数据日期"""
    source = load_json(SOURCE_FILE)
    if not source or not source.get("update_time"):
        return date.today().strftime("%Y-%m-%d")

    update_time = source.get("update_time", "")
    try:
        dt = datetime.strptime(update_time[:10], "%Y-%m-%d").date()
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return date.today().strftime("%Y-%m-%d")


def run():
    print("=" * 50)
    print("多维共振每日快照更新")
    print("=" * 50)

    # 1. 读取今日TOP10
    source = load_json(SOURCE_FILE)
    if not source or not source.get("top10"):
        print(f"  ⚠️ {SOURCE_FILE} 无数据，跳过")
        return False

    today = get_today_str()
    top10 = source.get("top10", [])
    update_time = source.get("update_time", "")

    # 过滤 >= MIN_SCORE 的股票
    picks = [s for s in top10 if s.get("total_score", 0) >= MIN_SCORE]
    
    if not picks:
        print(f"  ⚠️ 今日无score>={MIN_SCORE}的股票，跳过")
        return False

    print(f"  日期: {today}")
    print(f"  数据时间: {update_time}")
    print(f"  总扫描数: {source.get('total_scored', len(top10))}")
    print(f"  score>={MIN_SCORE}: {len(picks)}只")

    # 2. 加载历史
    history = load_json(HISTORY_FILE, {})

    # 3. 检查是否已存在（防止重复写入）
    if today in history:
        print(f"  ℹ️  {today} 已存在({len(history[today].get('top10',[]))}只)，覆盖更新")
    else:
        print(f"  ✅ 新增 {today}")

    # 4. 写入今日快照
    history[today] = {
        "update_time": update_time,
        "total_scored": source.get("total_scored", len(top10)),
        "top10": picks,
        "_source": "TOP10_DAILY"
    }

    # 清理超期数据（保留最近90天，减少文件大小）
    dates = sorted(history.keys())
    if len(dates) > 90:
        cutoff = dates[-90:]
        cleaned = {k: history[k] for k in cutoff if k.startswith("20")}
        removed = len(dates) - len(cutoff)
        if removed > 0:
            history = cleaned
            print(f"  🗑️  清理{removed}天旧数据（保留90天）")

    # 5. 保存
    save_json(HISTORY_FILE, history)

    total_days = len([k for k in history.keys() if k.startswith("20")])
    print(f"  ✓ 历史共 {total_days} 天数据 → {HISTORY_FILE}")

    # 6. 统计信息
    champ_map = {}
    for d, entry in history.items():
        if d.startswith("_") or not isinstance(entry, dict):
            continue
        t10 = entry.get("top10", [])
        if t10:
            name = t10[0].get("name", "?")
            champ_map[name] = champ_map.get(name, 0) + 1

    if champ_map:
        top_champ = sorted(champ_map.items(), key=lambda x: -x[1])[0]
        print(f"  🏆 当前历史冠军王: {top_champ[0]} ({top_champ[1]}次)")
        
        # 最新一天的冠军
        latest_day = max(d for d in history.keys() if d.startswith("20"))
        latest_top = history[latest_day].get("top10", [])
        if latest_top:
            print(f"  👑 今日/最新冠军王: {latest_top[0].get('name','?')} ({latest_day})")

    return True


if __name__ == "__main__":
    ok = run()
    # 无数据(无top10/无>=70股票)是正常跳过，不算失败，避免污染并行组。
    # 只有 run() 内部抛出未捕获异常才会 exit(1)，那才是真失败。
    sys.exit(0)
