#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
close_deploy_guarded.py — 阿狸咪 19:30 收盘最终部署「守卫」
====================================================
【根因】2026-07-16 事故：云端 18:31 已部署新鲜数据，但阿狸咪 19:30 用
陈旧本地数据重新 deploy，把云端的好数据冲掉了，导致主站/独立页看不到最新。

【本脚本逻辑】比较「本地待部署数据」与「线上 gh-pages 已部署数据」的新鲜度：
  - 线上(云端) >= 本地  → 云端已到位，【跳过兜底部署】（绝不覆盖新鲜云端）
  - 线上缺失 / 线上 < 本地 → 调用 deploy_now.py 兜底部署（云端没跑或数据更旧）

这样阿狸咪 19:30 从「必部署」降级为「云端没到位才兜底」，与云端自主定时(cron)
形成完美闭环：云端为主、阿狸咪为最终兜底、互不伤害。

用法（由 batch_update.py close_deploy 调用，替换原 deploy_now.py 步）：
  python close_deploy_guarded.py
退出码：0=跳过(云端已新) / deploy_now 的退出码(已兜底部署) / 1=异常
"""
import os
import re
import sys
import json
import subprocess
import urllib.request
from datetime import datetime, timezone, timedelta

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
SITE_URL = "https://ah-quant999.github.io/quant-scanner-v6/"
TZ = timezone(timedelta(hours=8))


def log(msg):
    ts = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def extract_scan_time(text):
    """从 HTML 文本里取 SCAN_DATA.scan_time 或 build-stamp。"""
    m = re.search(r'"scan_time"\s*:\s*"([^"]+)"', text)
    if m:
        return m.group(1)
    b = re.search(r'name="build-stamp"\s+content="(\d+)"', text)
    if b:
        return b.group(1)
    return None


def parse_ts(s):
    """把 scan_time / build-stamp 解析成带时区的 datetime；失败返回 None。"""
    if not s:
        return None
    s = s.strip()
    try:
        # 形如 "2026-07-16 18:31:00" 或 ISO "2026-07-16T18:31:00"
        s2 = s.replace("T", " ").replace("Z", "").strip()
        if len(s2) >= 19:
            return datetime.strptime(s2[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=TZ)
        # build-stamp 形如 20260716183000
        if len(s2) == 14 and s2.isdigit():
            return datetime.strptime(s2, "%Y%m%d%H%M%S").replace(tzinfo=TZ)
    except Exception:
        pass
    return None


def remote_scan_time():
    try:
        req = urllib.request.Request(SITE_URL, headers={"User-Agent": "guard/1.0"})
        html = urllib.request.urlopen(req, timeout=12).read().decode("utf-8", "ignore")
        return extract_scan_time(html)
    except Exception as e:
        log(f"⚠️ 读取线上站点失败: {e}")
    return None


def local_scan_time():
    p = os.path.join(WORKSPACE, "dist", "index.html")
    if not os.path.exists(p):
        log("⚠️ 本地 dist/index.html 不存在（update_data_v2 可能未生成）")
        return None
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            return extract_scan_time(f.read())
    except Exception as e:
        log(f"⚠️ 读取本地 dist 失败: {e}")
    return None


def deploy():
    """调用真实部署脚本。"""
    log("🚀 调用 deploy_now.py 兜底部署…")
    r = subprocess.run([sys.executable, "deploy_now.py"], cwd=WORKSPACE)
    return r.returncode


def main():
    local_raw = local_scan_time()
    remote_raw = remote_scan_time()
    local = parse_ts(local_raw)
    remote = parse_ts(remote_raw)

    if local is None:
        log("❌ 本地无有效 scan_time，无法判定新鲜度，保守兜底部署")
        sys.exit(deploy())
    if remote is None:
        log("⚠️ 线上无有效 scan_time（可能首次/异常），兜底部署")
        sys.exit(deploy())

    if remote >= local:
        log(f"✅ 线上数据更新或相等（线上 {remote:%Y-%m-%d %H:%M} ≥ 本地 {local:%Y-%m-%d %H:%M}），"
             f"云端已到位 → 跳过兜底部署（避免覆盖新鲜云端）")
        sys.exit(0)

    # remote < local：本地确实更新 → 兜底部署
    log(f"🔄 本地数据更新（本地 {local:%Y-%m-%d %H:%M} > 线上 {remote:%Y-%m-%d %H:%M}），执行兜底部署")
    sys.exit(deploy())


if __name__ == "__main__":
    main()
