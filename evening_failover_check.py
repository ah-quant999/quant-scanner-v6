#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
17:30 后收盘阶段主备状态检查
运行在小九机器上，判断阿狸咪主流程是否成功，从而决定小九是否需要兜底。

输出：
- "阿狸咪主流程成功，小九无需兜底" → 跳过
- "需要兜底：XXX" → 执行对应补跑
"""
import json
import os
import sys
import glob
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

DATA_DIR = Path(r"E:/workspace/stock-scanner/data")
LOG_PATH = Path(r"E:/workspace/stock-scanner/HANDOVER_LOG.jsonl")
REPO = "ah-quant999/quant-scanner-v6"
DEPLOY_CUTOFF_HOUR = 19
DEPLOY_CUTOFF_MINUTE = 30


def now():
    return datetime.now().astimezone()


def today_cutoff():
    n = now()
    return n.replace(hour=DEPLOY_CUTOFF_HOUR, minute=DEPLOY_CUTOFF_MINUTE, second=0, microsecond=0)


def file_mtime(path: Path):
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=now().tzinfo)


def github_gh_pages_latest(repo: str):
    """查 gh-pages 分支最新提交时间（UTC）"""
    try:
        import urllib.request
        url = f"https://api.github.com/repos/{repo}/commits/gh-pages"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        dt = datetime.fromisoformat(data["commit"]["committer"]["date"].replace("Z", "+00:00"))
        return dt
    except Exception:
        return None


def close_deploy_success_today(today: str):
    """HANDOVER_LOG 中今日是否有 close_deploy success=true"""
    if not LOG_PATH.exists():
        return False
    with LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("time", "").startswith(today) and d.get("mode") == "close_deploy" and d.get("success") is True:
                return True
    return False


def main():
    today = now().strftime("%Y-%m-%d")
    cutoff = today_cutoff()
    checks = []
    failed = []

    # 1. gold_pool.json
    gold = file_mtime(DATA_DIR / "gold_pool.json")
    if gold and gold > cutoff:
        checks.append(f"✅ gold_pool.json 已更新：{gold.strftime('%H:%M:%S')}")
    else:
        failed.append("gold_pool.json 未在 19:30 后更新")
        checks.append(f"❌ gold_pool.json {'未找到' if gold is None else '更新于 '+gold.strftime('%H:%M:%S')}")

    # 2. scan_result.json
    scan = file_mtime(DATA_DIR / "scan_result.json")
    if scan and scan > cutoff:
        checks.append(f"✅ scan_result.json 已更新：{scan.strftime('%H:%M:%S')}")
    else:
        failed.append("scan_result.json 未在 19:30 后更新")
        checks.append(f"❌ scan_result.json {'未找到' if scan is None else '更新于 '+scan.strftime('%H:%M:%S')}")

    # 3. HANDOVER_LOG close_deploy success
    if close_deploy_success_today(today):
        checks.append("✅ HANDOVER_LOG 今日 close_deploy 成功")
    else:
        failed.append("HANDOVER_LOG 无今日 close_deploy 成功记录")
        checks.append("❌ HANDOVER_LOG 无今日 close_deploy 成功记录")

    # 4. gh-pages 最新提交
    gh = github_gh_pages_latest(REPO)
    if gh:
        gh_local = gh.astimezone()
        if gh_local.date() == now().date() and gh_local.hour >= DEPLOY_CUTOFF_HOUR and (gh_local.hour > DEPLOY_CUTOFF_HOUR or gh_local.minute >= DEPLOY_CUTOFF_MINUTE):
            checks.append(f"✅ gh-pages 今日 {gh_local.strftime('%H:%M:%S')} 已部署")
        else:
            failed.append(f"gh-pages 最新提交不在今日 {DEPLOY_CUTOFF_HOUR}:{DEPLOY_CUTOFF_MINUTE:02d} 之后")
            checks.append(f"❌ gh-pages 最新提交：{gh_local.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        failed.append("gh-pages 查询失败")
        checks.append("❌ gh-pages 查询失败")

    print(f"📊 17:30 后主备检查 ({now().strftime('%Y-%m-%d %H:%M:%S')})")
    for c in checks:
        print(c)

    if not failed:
        print("\n✅ 阿狸咪主流程成功，小九无需兜底")
        return 0
    else:
        print(f"\n🔴 需要兜底：{', '.join(failed)}")
        print("建议：小九运行对应 batch_update.py 补跑环节")
        return 1


if __name__ == "__main__":
    sys.exit(main())
