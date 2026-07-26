#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
clean_deploy_lock.py — 清理 origin/main 上的陈旧 .deploy_lock

用途：
    部署中断后（git push 失败、进程被杀等），.deploy_lock 会残留在 origin/main 上。
    下次 deploy_now.py _acquire_deploy_lock() 虽能检测到并强制抢占，
    但残锁会干扰首次尝试（stale self-lock 警告）。
    
    本脚本：
    1) 检查 origin/main 上的 .deploy_lock 是否存在
    2) 若存在且超过 LOCK_TIMEOUT（180s），视为残锁 → 删除 + push
    3) 若 lock 的 host 是本机且存在 → 也视为残锁（前一次已结束）
    
用法：
    python clean_deploy_lock.py           # 有残锁才清理
    python clean_deploy_lock.py --force   # 强制清理
    
铁律：
    - 只清理远程锁，不涉及 gh-pages 或 dist/
    - 不会影响正在进行的部署（`_acquire_deploy_lock()` 自身会重试）

输出：
    0 = 无操作（锁不存在或仍有效）
    1 = 已清理残锁
    2 = 错误
"""
import os, sys, json, subprocess
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LOCK_TIMEOUT = 180  # 与 deploy_now.py 保持一致

REPO = "ah-quant999/quant-scanner-v6"
GIT = "git -c http.version=HTTP/1.1"


def _git(cmd, cwd=None):
    full = f"{GIT} {cmd}"
    r = subprocess.run(full, shell=True, capture_output=True, text=True, cwd=cwd or PROJECT_ROOT)
    return r


def clean():
    force = "--force" in sys.argv

    # 1. 检查远程锁
    r = _git("show origin/main:.deploy_lock")
    if r.returncode != 0:
        print("[lock] no remote .deploy_lock found — nothing to clean")
        return 0

    try:
        lock = json.loads(r.stdout.strip())
    except json.JSONDecodeError:
        print("[lock] corrupt remote lock file — will clean")
        lock = {"host": "?", "time": "2000-01-01T00:00:00"}

    host = lock.get("host", "?")
    time_str = lock.get("time", "2000-01-01T00:00:00")
    try:
        lock_time = datetime.fromisoformat(time_str)
        age = (datetime.now() - lock_time).total_seconds()
    except:
        age = LOCK_TIMEOUT + 1  # 解析失败视为过期

    my_host = os.environ.get("COMPUTERNAME", "unknown").upper()

    is_self = host == my_host or host == "CAT" or host == "ALIMI"

    if age < LOCK_TIMEOUT and not is_self and not force:
        print(f"[lock] remote lock is active ({host}, {age:.0f}s old < {LOCK_TIMEOUT}s) — not cleaning")
        return 0

    print(f"[lock] stale lock detected: host={host}, age={age:.0f}s")
    print(f"[lock] cleaning...")

    # 2. 删除并推送
    lock_path = os.path.join(PROJECT_ROOT, ".deploy_lock")
    if os.path.exists(lock_path):
        os.remove(lock_path)

    r1 = _git("rm -f --ignore-unmatch .deploy_lock")
    r2 = _git('commit --allow-empty -m "[lock] cleanup stale lock from CAT"')
    r3 = _git("push origin main")

    if r3.returncode == 0:
        print(f"[lock] ✅ stale lock cleaned (commit: {r2.stdout[:40] if r2.stdout else '?'})")
        return 1
    else:
        print(f"[lock] ❌ push failed: {r3.stderr[:200]}")
        return 2


if __name__ == "__main__":
    sys.exit(clean())
