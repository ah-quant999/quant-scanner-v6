#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""前端部署到位检查器 + 自动补部署 (verify_frontend_deploy.py)

为什么需要它：
   deploy_now.py 在「双机部署锁被另一台机器持有且未过期」时会静默 SKIP 并 return 0，
   上层 batch_update.py 据此记 success=true —— 典型的「以为部署了其实没部署」陷阱。
   本脚本作为独立真相检查器，直接比对「本机已构建的 dist/ 前端」与「线上 origin/gh-pages」，
   发现差异就自动补部署，确保前端确实上线。

检查范围：
   dist/ 下全部 .html/.js/.css（前端 UI）。dist/data/ 走坚果云/CDN，不在此核对。

流程：
   1. git fetch origin gh-pages
   2. 本机 dist/ 前端文件 -> git hash-object (blob sha1)
   3. origin/gh-pages 树 -> git ls-tree -r (blob sha1)
   4. 逐文件比对；无差异 -> FRONTEND_DEPLOYED_OK
   5. 有差异 -> 调 deploy_now.py --force 补部署（--force 会先重建 dist 再推送，绝不推陈旧版）
      + 锁竞争检测：若被 SKIP 则等待锁超时后重试，最多 2 次
   6. 重新校验，输出哨兵行，并追加一条记录到 HANDOVER_LOG.jsonl
"""
import os
import sys
import time
import json
import datetime
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
HANDOVER = os.path.join(PROJECT_ROOT, "HANDOVER_LOG.jsonl")
FRONTEND_EXT = (".html", ".js", ".css")
LOCK_WAIT = 190  # > deploy_now.LOCK_TIMEOUT(180)，确保锁已过期可抢占


def run(cmd, cwd=PROJECT_ROOT, timeout=600):
    return subprocess.run(cmd, shell=True, cwd=cwd,
                          capture_output=True, text=True, timeout=timeout)


def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def local_frontend_hashes():
    """返回 {relpath: blob_sha1} 本机 dist/ 全部前端文件（排除 dist/data）"""
    res = {}
    for root, _dirs, files in os.walk(DIST_DIR):
        for f in files:
            if not f.endswith(FRONTEND_EXT):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, DIST_DIR).replace(os.sep, "/")
            if rel.startswith("data/"):   # 数据走坚果云/CDN，不核对
                continue
            h = run(f'git hash-object "{full}"').stdout.strip()
            if h:
                res[rel] = h
    return res


def remote_tree_hashes():
    """返回 {path: blob_sha1} origin/gh-pages 整棵树"""
    r = run("git fetch origin gh-pages --depth=1")
    if r.returncode != 0:
        log(f"  WARN fetch gh-pages 失败: {r.stderr[:200]}")
    out = run("git ls-tree -r origin/gh-pages").stdout
    res = {}
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        meta = parts[0].split()
        if len(meta) >= 3 and meta[1] == "blob":
            res[parts[1]] = meta[2]
    return res


def compare(local, remote):
    return [rel for rel, h in local.items() if remote.get(rel) != h]


def deploy_force():
    """调用 deploy_now.py --force 补部署，返回 'skip' | 'done' | 'fail'"""
    log("   调用 deploy_now.py --force 补部署...")
    try:
        r = run(f'{sys.executable} deploy_now.py --force', timeout=600)
    except subprocess.TimeoutExpired:
        log("   deploy_now.py 超时(>600s)")
        return "fail"
    out = r.stdout + r.stderr
    log(f"   deploy exit={r.returncode}")
    if "SKIP" in out and "deploying" in out:
        log("   ⚠️ 检测到锁竞争 SKIP，将等待锁超时后重试")
        return "skip"
    return "done" if r.returncode == 0 else "fail"


def write_handover(mode, success, redeployed, gap_count, status):
    rec = {
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "mode": mode,
        "host": os.environ.get("COMPUTERNAME", "?"),
        "success": success,
        "redeployed": redeployed,
        "gap_files": gap_count,
        "status": status,
    }
    try:
        with open(HANDOVER, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:
        log(f"  WARN 写 HANDOVER_LOG 失败: {e}")


def main():
    log("=== 前端部署到位检查 (verify_frontend_deploy) ===")
    local = local_frontend_hashes()
    log(f"   本机前端文件数: {len(local)}")
    remote = remote_tree_hashes()
    mismatches = compare(local, remote)

    if not mismatches:
        log("✅ FRONTEND_DEPLOYED_OK — 本地 dist 与 origin/gh-pages 完全一致")
        write_handover("close_deploy_verify", True, False, 0, "FRONTEND_DEPLOYED_OK")
        return 0

    log(f"⚠️ 发现 {len(mismatches)} 个前端文件未部署到位:")
    for m in mismatches[:30]:
        log(f"   - {m}")

    for attempt in range(2):
        result = deploy_force()
        if result == "skip":
            log(f"   等待锁超时 {LOCK_WAIT}s 后重试 ({attempt+1}/2)...")
            time.sleep(LOCK_WAIT)
            continue
        # 重新校验（deploy 会先重建 dist，必须重算本地哈希）
        remote2 = remote_tree_hashes()
        mismatches2 = compare(local_frontend_hashes(), remote2)
        if not mismatches2:
            log("✅ FRONTEND_REDEPLOYED_OK — 补部署成功，前端已到位")
            write_handover("close_deploy_verify", True, True,
                           len(mismatches), "FRONTEND_REDEPLOYED_OK")
            return 0
        log(f"⚠️ 补部署后仍有 {len(mismatches2)} 个差异，重试 ({attempt+1}/2)...")

    log("❌ FRONTEND_VERIFY_FAILED — 补部署后仍不到位，需人工介入")
    write_handover("close_deploy_verify", False, True,
                   len(mismatches), "FRONTEND_VERIFY_FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
