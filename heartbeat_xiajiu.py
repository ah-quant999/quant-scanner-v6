#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿狸咪 → 小九 对称心跳检查
机制：
1. 查 GitHub main 分支最新提交时间（对称于小九查 gh-pages 最新提交）
2. 查 HANDOVER_LOG.jsonl 白天（09:00-17:00）是否有今日记录
3. 查是否存在今日 HANDOVER_小九_*.md 文档
输出简洁中文报告，适合自动化任务汇报。
"""
import json
import os
import sys
import glob
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = "ah-quant999/quant-scanner-v6"
LOG_PATH = Path(r"E:/workspace/stock-scanner/HANDOVER_LOG.jsonl")
HANDOVER_DIR = Path(r"E:/workspace/stock-scanner")
WORKDAY_START = 9   # 09:00
WORKDAY_END = 17    # 17:00
OFFLINE_HOURS = 24  # GitHub 提交超过 N 小时认为不在线


def now():
    return datetime.now().astimezone()


def fmt(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def github_latest_commit(repo: str):
    """返回 (commit_time, author, sha) 或 None"""
    try:
        import urllib.request
        url = f"https://api.github.com/repos/{repo}/commits/main"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        dt = datetime.fromisoformat(data["commit"]["committer"]["date"].replace("Z", "+00:00"))
        author = data["commit"]["committer"].get("name", "unknown")
        sha = data.get("sha", "")[:7]
        return dt, author, sha
    except Exception as e:
        return None, str(e), ""


def daytime_log_entries(today: str):
    """返回今日 09:00-17:00 的 HANDOVER_LOG 条目列表"""
    if not LOG_PATH.exists():
        return [], "日志文件不存在"
    entries = []
    with LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = d.get("time", "")
            if not t.startswith(today):
                continue
            try:
                dt = datetime.strptime(t, "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.now().astimezone().tzinfo)
            except ValueError:
                continue
            if WORKDAY_START <= dt.hour < WORKDAY_END:
                entries.append(d)
    return entries, None


def latest_xiajiu_handover(today: str):
    """返回今日最新的 HANDOVER_小九_*.md 路径 或 None"""
    files = glob.glob(str(HANDOVER_DIR / "HANDOVER_小九_*.md"))
    today_files = [p for p in files if today in os.path.basename(p)]
    if not today_files:
        return None
    return max(today_files, key=os.path.getmtime)


def main():
    today = now().strftime("%Y-%m-%d")
    report = ["📡 小九心跳检查结果"]

    # 1. GitHub main
    gh_time, gh_author, gh_sha = github_latest_commit(REPO)
    if gh_time is None:
        report.append(f"⚠️ GitHub main 查询失败: {gh_author}")
        gh_alive = False
    else:
        gh_local = gh_time.astimezone()
        age_hours = (now() - gh_local).total_seconds() / 3600
        gh_alive = age_hours <= OFFLINE_HOURS
        status = "✅" if gh_alive else "❌"
        report.append(f"{status} GitHub main 最新提交: {fmt(gh_local)} ({age_hours:.1f}h 前) by {gh_author} ({gh_sha})")

    # 2. HANDOVER_LOG 白天条目
    entries, err = daytime_log_entries(today)
    if err:
        report.append(f"⚠️ {err}")
    else:
        log_alive = len(entries) > 0
        status = "✅" if log_alive else "❌"
        latest = entries[-1]["time"] if entries else "无"
        report.append(f"{status} 今日白天日志条目: {len(entries)} 条（最新 {latest}）")

    # 3. HANDOVER 文档
    handover = latest_xiajiu_handover(today)
    if handover:
        report.append(f"✅ 今日小九交接文档: {os.path.basename(handover)}")
    else:
        report.append("❌ 今日无小九交接文档")

    # 综合判断
    if gh_alive or (len(entries) > 0) or handover:
        report.append("\n结论：小九今天有活动，判定为在线。")
    else:
        report.append("\n结论：小九今天无可见活动，可能离线或任务未跑。")

    print("\n".join(report))
    return 0 if (gh_alive or len(entries) > 0 or handover) else 1


if __name__ == "__main__":
    sys.exit(main())
