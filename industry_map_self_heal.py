#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行业地图(industry_map.json) 周日自愈器 + 周一盘前兜底
=================================================
周日 06:30 由 cloud_weekly.yml 重建 industry_map.json。
本脚本在 07:00 检查是否成功，若失败则触发云端补跑 + 邮件告警。
周一 06:45 盘前兜底，与周日自愈对称。

设计：
  - 只检查 data/industry_map.json 的 update_time 是否 ≥「最近周日 06:00」
    · 周日运行 → 比对本周日 06:00（重建应在 06:30 完成，07:00 检查）
    · 周一运行 → 比对上周日 06:00（若周日全天失败则触发补跑，开盘前恢复）
  - 节流：当天最多触发 1 次（.industry_map_heal_state.json），周日/周一互不干扰。
  - 复用 check_data_freshness.load_update_time + trigger_cloud_dispatch.get_pat。

用法：
  python industry_map_self_heal.py            # 检测 + 自愈（无邮件）
  python industry_map_self_heal.py --email    # 检测 + 自愈 + 邮件告警
  python industry_map_self_heal.py --dry-run  # 只打印判定与 dispatch 构造，不真发
"""
import os
import sys
import json
import datetime
import subprocess

import check_data_freshness as cf
import trigger_cloud_dispatch as tcd

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = "ah-quant999/quant-scanner-v6"
STATE_FILE = os.path.join(BASE, ".industry_map_heal_state.json")
TARGET_FILE = "industry_map.json"
TARGET_LABEL = "行业地图 industry_map.json"
# 截止基准：最近一个周日 06:00（重建应在 06:30 完成）
DEADLINE_HOUR = 6
DEADLINE_MINUTE = 0


def last_sunday_deadline():
    """返回最近一个周日 06:00（含今天若为周日）。industry_map 应在周日重建。"""
    now = datetime.datetime.now()
    days_since_sun = (now.weekday() - 6) % 7  # weekday: Mon=0,...,Sun=6
    return (now - datetime.timedelta(days=days_since_sun)).replace(
        hour=DEADLINE_HOUR, minute=DEADLINE_MINUTE, second=0, microsecond=0)


def trigger_industry_map_redispatch(pat, dry_run):
    """触发云端 cloud_weekly.yml task=industry_map 补跑（重建+推送 main+部署）。"""
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/cloud_weekly.yml/dispatches"
    body = {"ref": "main", "inputs": {"task": "industry_map"}}
    if dry_run:
        print("  🧪 [DRY-RUN] 将 dispatch cloud_weekly.yml task='industry_map'")
        return True
    cmd = [
        "curl", "-sS", "-X", "POST", url,
        "-H", "Accept: application/vnd.github+json",
        "-H", f"Authorization: Bearer {pat}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(body),
        "-w", "\\nHTTP:%{http_code}",
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        out = r.stdout.strip()
        ok = "HTTP:204" in out
        print(f"  {'✅' if ok else '❌'} dispatch cloud_weekly.yml task='industry_map' -> {out}")
        return ok
    except Exception as e:
        print(f"  ❌ dispatch 异常: {e}")
        return False


def industry_map_stale():
    """返回 (is_stale, detail) — industry_map.json 是否早于截止时间。"""
    ts, _ = cf.load_update_time(TARGET_FILE)
    if not ts:
        return True, f"无时间戳/文件缺失"
    try:
        dt = datetime.datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:
        try:
            dt = datetime.datetime.strptime(ts[:16], "%Y-%m-%d %H:%M")
        except Exception:
            return True, f"时间戳格式异常: {ts[:30]}"
    deadline = last_sunday_deadline()
    if dt < deadline:
        return True, dt.strftime("%Y-%m-%d %H:%M")
    return False, dt.strftime("%Y-%m-%d %H:%M")


def load_state():
    try:
        if os.path.exists(STATE_FILE):
            return json.load(open(STATE_FILE, encoding="utf-8"))
    except Exception:
        pass
    return {}


def save_state(state):
    try:
        json.dump(state, open(STATE_FILE, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
    except Exception:
        pass


def main():
    dry_run = "--dry-run" in sys.argv
    send_mail = "--email" in sys.argv
    now = datetime.datetime.now()

    # 防御性：仅周日（主检查）与周一盘前（兜底）运行
    if now.weekday() not in (6, 0):
        print("📅 非周日/周一，跳过 industry_map 自愈检查")
        return

    print(f"🔍 industry_map 自愈检查 — {now.strftime('%Y-%m-%d %H:%M')} 周{['一','二','三','四','五','六','日'][now.weekday()]}")
    is_stale, detail = industry_map_stale()
    if not is_stale:
        print(f"  ✅ industry_map 已于 {detail} 刷新，无需自愈")
        return

    print(f"  🔴 industry_map 未刷新（文件时间: {detail}），疑似重建失败")

    # 节流：当天最多触发 1 次
    state = load_state()
    today = now.strftime("%Y-%m-%d")
    if state.get("last_dispatch", "").startswith(today):
        print("  🔕 今日已触发过 industry_map 补跑，跳过重复触发（邮件照发）")
    else:
        pat = tcd.get_pat()
        if pat:
            ok = trigger_industry_map_redispatch(pat, dry_run)
            if ok and not dry_run:
                state["last_dispatch"] = now.strftime("%Y-%m-%d %H:%M")
                save_state(state)
        else:
            print("  ⚠️ 未找到 PAT（GH_PAT/.gh_pat/git credential），无法触发云端补跑（仅邮件告警）")

    if send_mail:
        detail_list = [(TARGET_LABEL, "🔴", f"文件时间: {detail}")]
        cf.send_email(detail_list, [])


if __name__ == "__main__":
    main()
