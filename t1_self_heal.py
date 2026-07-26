#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
周六 T+1 数据自愈器（阿狸咪本地，对称盘中看门狗）
================================================
周六 09:30 主检查 + 周一 07:00 盘前兜底，由自动化调用。检查 check_data_freshness 监控的
15 个关键数据文件，若任一文件的 update_time 早于「最近一个周六 00:00」（即 T+1 应在周六补全），
判定 T+1 失败 → 触发云端 cloud_weekly.yml task=t1 补跑 + 发送告警邮件。
  - 周六 09:30：发现周六 T+1 失败 → 当天补跑
  - 周一 07:00：若周六全天云端抽风都失败，开盘前再度发现并触发补跑部署（避免拖到周一20:00）
节流：当天最多触发 1 次（.t1_heal_state.json，按日期隔离，周六/周一互不干扰）。

对称盘中看门狗 intraday_fresh_check.py：发现旧数据立即触发云端补跑部署。
本脚本复用同一套机制（get_pat + curl dispatch），但不改动 trigger_cloud_dispatch.py
（那是双机发令枪，逻辑耦合，避免影响其盘中链路）。

用法：
  python t1_self_heal.py            # 检测 + 自愈（无邮件）
  python t1_self_heal.py --email    # 检测 + 自愈 + 邮件告警
  python t1_self_heal.py --dry-run  # 只打印判定与 dispatch 构造，不真发/不真触发
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
STATE_FILE = os.path.join(BASE, ".t1_heal_state.json")
# 截止基准：最近一个周六 00:00（T+1 数据应在周六补全；周一盘前比对上周六）。
# 注：原逻辑用"今天08:00"，周一运行会误判周六成功文件为过期 → 改为锚定最近周六。


def trigger_t1_redispatch(pat, dry_run):
    """触发云端 cloud_weekly.yml task=t1 补跑（抓取+构建+部署一体）。"""
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/cloud_weekly.yml/dispatches"
    body = {"ref": "main", "inputs": {"task": "t1"}}
    if dry_run:
        print("  🧪 [DRY-RUN] 将 dispatch cloud_weekly.yml task='t1'")
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
        print(f"  {'✅' if ok else '❌'} dispatch cloud_weekly.yml task='t1' -> {out}")
        return ok
    except Exception as e:
        print(f"  ❌ dispatch 异常: {e}")
        return False


def last_saturday_midnight():
    """返回最近一个周六 00:00（含今天若为周六）。T+1 数据应在周六补全。"""
    now = datetime.datetime.now()
    days_since_sat = (now.weekday() - 5) % 7
    return (now - datetime.timedelta(days=days_since_sat)).replace(
        hour=0, minute=0, second=0, microsecond=0)


def t1_failed_files():
    """返回 update_time 早于「最近周六 00:00」的关键文件 [(label, ts_str), ...]。
    周六运行 → 比对本周六 00:00（T+1 应在周六补全）。
    周一盘前运行 → 比对上周六 00:00（若 T+1 失败，文件仍停周五 → 判失败 → 触发补跑）。
    """
    deadline = last_saturday_midnight()
    failed = []
    for fn, (label, icon) in cf.DATA_SOURCES.items():
        ts, _ = cf.load_update_time(fn)
        if not ts:
            failed.append((label, "无时间戳/文件缺失"))
            continue
        try:
            dt = datetime.datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S")
        except Exception:
            try:
                dt = datetime.datetime.strptime(ts[:16], "%Y-%m-%d %H:%M")
            except Exception:
                continue
        if dt < deadline:
            failed.append((label, dt.strftime("%Y-%m-%d %H:%M")))
    return failed


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

    # 防御性：仅周六（T+1 主检查）与周一盘前（T+1 兜底，开盘前发现并部署）运行
    if now.weekday() not in (5, 0):
        print("📅 非周六/周一，跳过 T+1 自愈检查")
        return

    print(f"🔍 T+1 自愈检查 — {now.strftime('%Y-%m-%d %H:%M')}")
    failed = t1_failed_files()
    if not failed:
        print("  ✅ 所有关键数据文件均已刷新（T+1 成功），无需自愈")
        return

    print(f"  🔴 发现 {len(failed)} 个文件未刷新（T+1 疑似失败）:")
    for label, detail in failed:
        print(f"     - {label}: {detail}")

    # 节流：当天最多触发 1 次，避免与云端 cron / safety-net 重复刷爆 Actions
    state = load_state()
    today = now.strftime("%Y-%m-%d")
    if state.get("last_t1_dispatch", "").startswith(today):
        print("  🔕 今日已触发过 T+1 补跑，跳过重复触发（邮件照发）")
    else:
        pat = tcd.get_pat()
        if pat:
            ok = trigger_t1_redispatch(pat, dry_run)
            if ok and not dry_run:
                state["last_t1_dispatch"] = now.strftime("%Y-%m-%d %H:%M")
                save_state(state)
        else:
            print("  ⚠️ 未找到 PAT（GH_PAT/.gh_pat/git credential），无法触发云端补跑（仅邮件告警）")

    if send_mail:
        detail = [("T+1数据补全", "🔴", f"{label}: {detail}") for label, detail in failed]
        cf.send_email(detail, [])


if __name__ == "__main__":
    main()
