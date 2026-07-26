#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
intraday_local_failover.py — 本地盘中自动补跑
==============================================
当云端 cloud_intraday 在某档（10:31/11:46/13:31/14:31）失败时，
阿狸咪本地自动运行对应的 batch_update.py 模式补跑，确保盘中数据不空窗。

用法：
    python intraday_local_failover.py --slot 10:31 --mode morning_plus
    python intraday_local_failover.py --slot 11:46 --mode morning_report
    python intraday_local_failover.py --slot 13:31 --mode afternoon
    python intraday_local_failover.py --slot 14:31 --mode afternoon
"""
import os
import sys
import json
import subprocess
import datetime
import time
import argparse

BASE = os.path.dirname(os.path.abspath(__file__))
SCAN_RESULT = os.path.join(BASE, "data", "scan_result.json")
HANDOVER_LOG = os.path.join(BASE, "HANDOVER_LOG.jsonl")
LOCK_FILE = os.path.join(BASE, ".intraday_failover.lock")
STATE_FILE = os.path.join(BASE, ".intraday_failover_state.json")

SLOT_TO_MODE = {
    "10:31": "morning_plus",
    "11:46": "morning_report",
    "13:31": "afternoon",
    "14:31": "afternoon",
}

FAILOVER_DELAY_MIN = 45  # 档后多少分钟才判定云端失败并补跑
LOCK_TTL_MIN = 60        # 锁文件超过该时间视为死锁，可强制清除


def _run(cmd, timeout=60, env=None):
    e = os.environ.copy()
    if env:
        e.update(env)
    # 所有 git 命令都带 SSH 超时 + HTTP/1.1
    if cmd.strip().startswith("git "):
        e["GIT_SSH_COMMAND"] = "ssh -o ConnectTimeout=15"
    return subprocess.run(
        cmd, shell=True, cwd=BASE, capture_output=True, text=True,
        env=e, timeout=timeout,
    )


def _load_state():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
    except Exception:
        pass


def _is_trading_day():
    try:
        from is_trading_day import is_trading_day as itd
        return itd(datetime.date.today())
    except Exception:
        return datetime.date.today().weekday() < 5


def _lock_stale():
    try:
        mtime = os.path.getmtime(LOCK_FILE)
        return (time.time() - mtime) > LOCK_TTL_MIN * 60
    except Exception:
        return True


def _acquire_lock():
    if os.path.exists(LOCK_FILE):
        if not _lock_stale():
            print("  ⚠️ 已有补跑任务在运行（锁未过期），跳过")
            return False
        try:
            os.remove(LOCK_FILE)
        except Exception:
            pass
    try:
        with open(LOCK_FILE, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
        return True
    except Exception:
        return False


def _release_lock():
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except Exception:
        pass


def _write_handover(slot, mode, success, detail):
    try:
        entry = {
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": f"intraday_failover_{slot}",
            "host": "ALIMI",
            "success": success,
            "detail": detail,
        }
        with open(HANDOVER_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot", required=True, help="档位，如 10:31")
    parser.add_argument("--mode", required=True, help="batch_update.py 模式名")
    args = parser.parse_args()

    slot = args.slot
    mode = args.mode
    today = datetime.date.today().isoformat()

    # 1. 基础校验
    if slot not in SLOT_TO_MODE:
        print(f"  ⚠️ 未知 slot: {slot}")
        return 1
    if SLOT_TO_MODE[slot] != mode:
        print(f"  ⚠️ slot {slot} 对应模式应为 {SLOT_TO_MODE[slot]}，而非 {mode}")
        return 1

    # 2. 仅交易日
    if not _is_trading_day():
        print(f"  ⏭️ 非交易日，跳过 {slot} 补跑")
        return 0

    # 3. 检查是否已补跑过
    state = _load_state()
    if state.get(slot) == today:
        print(f"  ⏭️  {slot} 今日已补跑，跳过")
        return 0

    # 4. 时间窗口校验：当前时间应在 slot + FAILOVER_DELAY_MIN 之后
    now = datetime.datetime.now()
    h, m = map(int, slot.split(":"))
    slot_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if (now - slot_dt).total_seconds() < FAILOVER_DELAY_MIN * 60:
        print(f"  ⏭️  距 {slot} 不足 {FAILOVER_DELAY_MIN} 分钟，等云端跑完再判定")
        return 0

    # 5. 获取锁
    if not _acquire_lock():
        return 1

    try:
        # 6. 先拉取最新 main（避免本地 scan_result 未同步导致误补跑）
        print(f"  🔄 [{slot}] 先拉取 main 同步最新状态...")
        r = _run("git -c http.version=HTTP/1.1 pull --ff-only origin main", timeout=60)
        if r.returncode != 0:
            print(f"  ⚠️  pull main 失败: {r.stderr[:200]}，继续用本地状态判断")

        # 7. 检查 scan_result.json 时间戳
        need_failover = False
        if not os.path.exists(SCAN_RESULT):
            print(f"  ⚠️  scan_result.json 不存在，判定云端失败，启动补跑")
            need_failover = True
        else:
            ts = None
            try:
                with open(SCAN_RESULT, "r", encoding="utf-8") as f:
                    d = json.load(f)
                ts = d.get("scan_time") or d.get("update_time") or ""
            except Exception as e:
                print(f"  ⚠️  读取 scan_result.json 失败: {e}")
                ts = None

            if not ts:
                print(f"  ⚠️  scan_result.json 无时间戳，判定云端失败，启动补跑")
                need_failover = True
            else:
                try:
                    st = datetime.datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S")
                except Exception:
                    st = datetime.datetime.strptime(ts[:16], "%Y-%m-%d %H:%M")
                if st >= slot_dt:
                    print(f"  ✅ 云端 {slot} 已刷新（scan_result {ts[:16]} >= {slot}），无需补跑")
                    state[slot] = today
                    _save_state(state)
                    return 0
                else:
                    print(f"  🔴 云端 {slot} 未刷新（scan_result {ts[:16]} < {slot}），启动补跑")
                    need_failover = True

        # 8. 判定云端失败，启动本地补跑
        if not need_failover:
            # 理论上不会走到这里，防御性返回
            return 0

        print(f"  🔴 云端 {slot} 失败，启动本地补跑: batch_update.py {mode}")
        _write_handover(slot, mode, False, f"云端 {slot} 未刷新，启动本地补跑")

        r = _run(f"python batch_update.py {mode}", timeout=2400)
        success = r.returncode == 0
        detail = "OK" if success else (r.stderr.strip()[-200:] if r.stderr else f"exit={r.returncode}")
        _write_handover(slot, mode, success, detail)

        if success:
            print(f"  ✅ 本地补跑 {slot} 成功")
            state[slot] = today
            _save_state(state)
            return 0
        else:
            print(f"  ❌ 本地补跑 {slot} 失败: {detail}")
            return 1

    finally:
        _release_lock()


if __name__ == "__main__":
    sys.exit(main())
