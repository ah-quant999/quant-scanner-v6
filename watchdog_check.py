#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
watchdog_check.py — 阿狸咪白天任务看门狗 (A+D 双机主备方案)
============================================================
用途：
    阿狸咪白天 10 个镜像任务，原本和小九(白天主)跑一样的全量 pipeline，
    双重浪费。本脚本让阿狸咪只做"看门狗"：判定小九是否已产出本时段数据。
      - 数据新鲜(小九已产出)  -> 退出码 0 -> 调用方跳过本任务(不跑 pipeline)
      - 数据缺失/过期(小九宕机或太慢) -> 退出码 1 -> 调用方接管全量

为什么用轮询：
    小九比阿狸咪早 1 分钟(-1 铁律)触发，所以阿狸咪任务点火时，小九本时段
    通常已跑完并 push。脚本每 POLL_SEC 秒 pull 一次 origin/main 并重判，命中
    本时段数据(更新时间落在 [slot-GRACE, now] 窗口)即判新鲜并跳过；超过 MAX_WAIT
    仍无新鲜数据则判接管。轮询同时作为小九偶发延迟/宕机的兜底，不会误接管。

数据新鲜判定：
    读 --data 指定数据文件内嵌的时间字段(update_time / scan_time 等)，
    【必须用文件内嵌时间，不能用 mtime】——因为 git pull 后 mtime=拉取时刻，
    会永远"新鲜"导致永不接管。

用法(贴入阿狸咪白天任务 prompt)：
    cd repo-temp && python -c "import git_safe_sync; git_safe_sync.safe_pull()"
    cd repo-temp && python watchdog_check.py --slot 11:45 --data data/scan_result.json
    # 退出码 0 -> 打印"小九数据新鲜，跳过"并 EXIT(不要跑 pipeline)
    # 退出码 1 -> 执行原全量流程(scanner/fetch -> update_data_v2 --fast -> deploy_now --force)

各任务对应 --data：
    08:30 IPO打新研判       -> data/ipo_score.json
    09:15 全盘(pre_market)  -> data/scan_result.json
    09:46/10:30/11:45/13:30/14:30/15:30/16:30 盘中 -> data/scan_result.json

注意：任务超时须 > MAX_WAIT(默认 1200s=20min)，否则用 --no-poll 并自行把
      任务时间后移 5~10 分钟。
"""
import argparse 
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 安全同步：彻底消除 stash-pop 冲突（data/ 双机重写根因）
try:
    from git_safe_sync import safe_pull
except ImportError:
    sys.path.insert(0, SCRIPT_DIR)
    from git_safe_sync import safe_pull
GRACE_MIN = 15          # 容忍小九在本时段前/后若干分钟内产出
POLL_SEC = 60           # 轮询间隔
MAX_WAIT = 1200         # 最长轮询等待(秒)，须 < 任务超时
UPDATE_KEYS = ("update_time", "scan_time", "updateTime", "updated_at",
               "time", "timestamp", "date")


def parse_slot(s):
    h, m = s.split(":")
    return int(h), int(m)


def parse_any_time(v):
    if isinstance(v, (int, float)):
        if v > 1e12:
            v = v / 1000
        try:
            return datetime.fromtimestamp(v)
        except Exception:
            return None
    s = str(v).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M",
                "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass
    return None


def load_update_time(path):
    """返回数据文件内嵌时间(datetime)，失败返回 None。优先读内嵌字段，绝不用 mtime。"""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict):
            for k in UPDATE_KEYS:
                if k in d and d[k]:
                    ts = parse_any_time(d[k])
                    if ts:
                        return ts
            for v in d.values():
                if isinstance(v, dict):
                    for k in UPDATE_KEYS:
                        if k in v and v[k]:
                            ts = parse_any_time(v[k])
                            if ts:
                                return ts
    except Exception:
        pass
    return None


def check_fresh(path, slot_dt, grace, now):
    ut = load_update_time(path)
    if ut is None:
        return False, None
    lo = slot_dt - timedelta(minutes=grace)
    hi = now + timedelta(minutes=1)
    return (lo <= ut <= hi), ut


def _silent_pull():
    try:
        safe_pull()
    except Exception:
        pass


def _report(fresh, ut, slot_dt, grace):
    ts = ut.strftime("%Y-%m-%d %H:%M:%S") if ut else "缺失"
    if fresh:
        print(f"[watchdog] 小九数据新鲜(update={ts}, 时段≈{slot_dt:%H:%M}) -> 跳过本任务")
    else:
        lo = (slot_dt - timedelta(minutes=grace)).strftime("%H:%M")
        print(f"[watchdog] 小九数据缺失/过期(update={ts}, 期望∈[{lo},现在]) -> 接管全量")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot", required=True, help="本任务在阿狸咪侧的计划时间 HH:MM")
    ap.add_argument("--data", required=True, help="本任务产出的主数据文件(相对 repo-temp 或绝对路径)")
    ap.add_argument("--grace", type=int, default=GRACE_MIN)
    ap.add_argument("--max-wait", type=int, default=MAX_WAIT)
    ap.add_argument("--poll", type=int, default=POLL_SEC)
    ap.add_argument("--no-poll", action="store_true",
                    help="只检查一次(需自行把任务时间后移，使小九已跑完)")
    args = ap.parse_args()

    now = datetime.now()
    h, m = parse_slot(args.slot)
    slot_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
    data_path = args.data if os.path.isabs(args.data) else os.path.join(SCRIPT_DIR, args.data)

    if args.no_poll:
        fresh, ut = check_fresh(data_path, slot_dt, args.grace, datetime.now())
        _report(fresh, ut, slot_dt, args.grace)
        sys.exit(0 if fresh else 1)

    deadline = time.time() + args.max_wait
    while True:
        _silent_pull()
        fresh, ut = check_fresh(data_path, slot_dt, args.grace, datetime.now())
        if fresh:
            _report(True, ut, slot_dt, args.grace)
            sys.exit(0)
        if time.time() > deadline:
            _report(False, ut, slot_dt, args.grace)
            sys.exit(1)
        time.sleep(args.poll)


if __name__ == "__main__":
    main()
