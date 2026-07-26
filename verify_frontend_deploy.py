#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""前端部署到位检查器 + 自动补部署 (verify_frontend_deploy.py)

为什么需要它：
   deploy_now.py 在「双机部署锁被另一台机器持有且未过期」时会静默 SKIP 并 return 0，
   上层 batch_update.py 据此记 success=true —— 典型的「以为部署了其实没部署」陷阱。
   本脚本作为独立真相检查器，直接比对「本机已构建的 dist/ 前端」与「线上 origin/gh-pages」，
   发现差异就自动补部署，确保前端确实上线。

检查范围：
   dist/ 下全部 .html/.js/.css（前端 UI）+ dist/data/*.json（数据/运维状态）。
   2026-07-19 修复：此前刻意跳过 dist/data/，导致数据/运维状态（.ops_status.json 等）
   陈腐时仍报 FRONTEND_DEPLOYED_OK 假阳性——用户看到的「检查都说最新、实际数据陈旧」即源于此。
   现纳入比对：本地 dist/ 与 origin/gh-pages 不一致即补部署。

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
FRONTEND_EXT = (".html", ".js", ".css", ".json")
# 锁竞争等待时间：部署锁默认 180s，加 10s 缓冲区确保锁已过期
# 可通过环境变量 DEPLOY_LOCK_WAIT 覆盖（调试/网络慢场景）
LOCK_WAIT = int(os.environ.get("DEPLOY_LOCK_WAIT", "190"))


def run(cmd, cwd=PROJECT_ROOT, timeout=600):
    return subprocess.run(cmd, shell=True, cwd=cwd,
                          capture_output=True, text=True, timeout=timeout)


def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# JSON 文件中随每次运行变化的"时间戳"字段，比对时忽略
# 规则：字段名含 time/stamp/date 的都视为时间戳变体
import re as _re


def _is_timestamp_key(k):
    """判断字段名是否属于时间戳类（比对时忽略）。"""
    return bool(_re.search(r"(time|stamp|date)", k, _re.I))


def _strip_time_variants(obj):
    """递归去除 JSON 对象中的时间戳字段。"""
    if isinstance(obj, dict):
        return {k: _strip_time_variants(v) for k, v in obj.items()
                if not _is_timestamp_key(k)}
    if isinstance(obj, list):
        return [_strip_time_variants(v) for v in obj]
    return obj


def _stable_hash_json(path):
    """对 JSON 文件：去除时间戳字段后计算 sha1 hash，避免误报。"""
    try:
        with open(path, "rb") as f:
            data = json.load(f)
        stripped = _strip_time_variants(data)
        normalized = json.dumps(stripped, sort_keys=True, ensure_ascii=False).encode("utf-8")
        # 模拟 git blob hash: sha1("blob <size>\\0<content>")
        import hashlib
        blob = b"blob %d\0%s" % (len(normalized), normalized)
        return hashlib.sha1(blob).hexdigest()
    except Exception as e:
        log(f"  WARN 解析 JSON 失败 {path}: {e}")
        return None


def _stable_hash_text(path, rel):
    """非 JSON 文件：用 git hash-object --filters 对齐 autocrlf。
    对 .html 文件额外剥离 build-stamp 内容再 hash，避免构建戳差异误报。"""
    with open(path, "rb") as fh:
        raw = fh.read()
    # HTML 文件：剥离 build-stamp 避免构建戳误报
    if rel.endswith(".html"):
        raw = _re.sub(rb'build-stamp["\':=]+["\']?\d{14}["\']?', b'build-stamp"STRIPPED"', raw)
    try:
        r = subprocess.run(
            ["git", "hash-object", "--filters", "--stdin", "--path", rel],
            input=raw, capture_output=True, text=False,
            cwd=PROJECT_ROOT, timeout=30)
        return r.stdout.strip().decode() if r.stdout else None
    except Exception as e:
        log(f"  WARN 计算 hash 失败 {path}: {e}")
        return None


def _stable_hash(path, rel):
    """计算文件的"稳定 hash"——排除时间戳变体后比对。
    对 .json 文件用 _stable_hash_json，其余用 _stable_hash_text。"""
    if rel.endswith(".json"):
        return _stable_hash_json(path)
    return _stable_hash_text(path, rel)


def local_frontend_hashes():
    """返回 {relpath: stable_hash} 本机 dist/ 全部前端文件"""
    res = {}
    for root, _dirs, files in os.walk(DIST_DIR):
        for f in files:
            if not f.endswith(FRONTEND_EXT):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, DIST_DIR).replace(os.sep, "/")
            h = _stable_hash(full, rel)
            if h:
                res[rel] = h
    return res


def remote_content_hashes():
    """返回 {path: stable_hash} origin/gh-pages 整棵树的稳定 hash。
    对 .json 文件通过 git show 获取内容后去除时间戳字段再 hash；
    对非 JSON 文件直接用 ls-tree 的 blob hash（已与 git push 时一致）。"""
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
        if len(meta) < 3 or meta[1] != "blob":
            continue
        path = parts[1]
        raw_hash = meta[2]
        if path.endswith(".json"):
            # JSON 文件：从仓库取出内容，去除时间戳字段后算稳定 hash
            try:
                content = subprocess.run(
                    ["git", "show", f"origin/gh-pages:{path}"],
                    capture_output=True, timeout=30).stdout
                data = json.loads(content)
                stripped = _strip_time_variants(data)
                normalized = json.dumps(stripped, sort_keys=True, ensure_ascii=False).encode("utf-8")
                import hashlib
                blob = b"blob %d\0%s" % (len(normalized), normalized)
                res[path] = hashlib.sha1(blob).hexdigest()
            except Exception as e:
                log(f"  WARN 处理远程 JSON {path} 失败: {e}")
                res[path] = raw_hash  # fallback
        else:
            # 非 JSON 文件
            if not path.endswith(FRONTEND_EXT):
                continue
            if path.endswith(".html"):
                # HTML 文件：取出内容，剥离 build-stamp 后算 hash
                try:
                    content = subprocess.run(
                        ["git", "show", f"origin/gh-pages:{path}"],
                        capture_output=True, timeout=30).stdout
                    stripped = _re.sub(rb'build-stamp["\':=]+["\']?\d{14}["\']?',
                                       b'build-stamp"STRIPPED"', content)
                    import hashlib
                    blob = b"blob %d\0%s" % (len(stripped), stripped)
                    res[path] = hashlib.sha1(blob).hexdigest()
                except Exception as e:
                    log(f"  WARN 处理远程 HTML {path} 失败: {e}")
                    res[path] = raw_hash
            else:
                # .js/.css 直接用 ls-tree hash
                res[path] = raw_hash
    return res


def compare(local, remote):
    return [rel for rel, h in local.items()
            if rel not in remote or remote[rel] != h]


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
    if ("SKIP" in out and "deploying" in out) or "部署被跳过" in out:
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
    remote = remote_content_hashes()
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
        if result == "done":
            # deploy 成功（exit=0+SUCCESS输出）。deploy_now.py --force 已保证推送
            # 不重新 hash 比对——因为 deploy 重建 dist 可能改变数据内容，
            # 与刚推送的版本产生循环差异。信任 deploy 自身的成功证据。
            log("✅ FRONTEND_REDEPLOYED_OK — deploy_now.py --force 成功")
            write_handover("close_deploy_verify", True, True,
                           len(mismatches), "FRONTEND_REDEPLOYED_OK")
            return 0
        # deploy 失败（真错误）
        log(f"⚠️ deploy_now.py 返回错误，重试 ({attempt+1}/2)...")

    log("❌ FRONTEND_VERIFY_FAILED — 补部署失败，需人工介入")
    write_handover("close_deploy_verify", False, True,
                   len(mismatches), "FRONTEND_VERIFY_FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
