#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
peer_health_monitor.py — 阿狸咪主机上的小九心跳监控 + 自动接管
============================================================

背景：小九是主力机，若其停电/断网/系统崩溃，阿狸咪需要感知并补跑救火任务。
本脚本监控 hb_xiaojiu.json（由 report_heartbeat 写入并推 main 的心跳文件），
当小九沉默 >90 分钟时，调用 audit_automations.py 激活阿狸咪本机的救火任务。

用法：
  阿狸咪主机 WorkBuddy 自动化：每 30 分钟运行一次（交易日 09:00-21:30）
    python peer_health_monitor.py

退出码：
  0 = 小九正常 / 非交易日 / 已接管
  1 = 检测到小九掉线并已激活接管
  2 = 读取失败
"""

import json
import os
import sys
import subprocess
import smtplib
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.header import Header

BASE = os.path.dirname(os.path.abspath(__file__))
HB_FILE = os.path.join(BASE, "data", "hb_xiaojiu.json")
PEER_FAILOVER_THRESHOLD_MIN = 90
LOG_FILE = os.path.join(BASE, "data", "_peer_monitor.log")
ALERT_STATE_FILE = os.path.join(BASE, "data", "_peer_alert_state.json")
ALERT_COOLDOWN_HOURS = 6  # 同一次失联事件内，邮件告警最多每 6 小时发一次，防刷屏

# ===== 失联邮件告警通道（复用备份 check_data_freshness.py 的 QQ SMTP 配置）=====
SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 465
SMTP_USER = "2814546@qq.com"          # 发件人 = 收件人（主人QQ邮箱）
SMTP_TO = "2814546@qq.com"
SMTP_AUTH_CODE = "sceornygysatcaig"   # QQ邮箱授权码；优先读环境变量 QQ_SMTP_PASS
SMTP_PASS = os.environ.get("QQ_SMTP_PASS", SMTP_AUTH_CODE)


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _git(cmd):
    """Git 操作：先拉取最新 main，确保拿到最新心跳"""
    full = f"git -c http.version=HTTP/1.1 {cmd}"
    return subprocess.run(full, shell=True, cwd=BASE,
                          capture_output=True, text=True, timeout=30)


def check_peer_alive():
    """
    检查小九心跳：
    1. git pull origin main（获取最新 hb_xiaojiu.json）
    2. 读取 hb_xiaojiu.json last_time
    3. 计算沉默分钟数
    返回 (alive: bool, silent_min: float, last_time: str)
    """
    # 1. 先拉取最新数据
    r = _git("pull --ff-only origin main")
    if r.returncode != 0:
        log(f"  ⚠️ git pull 失败: {r.stderr[:200]}")

    # 2. 读心跳文件
    if not os.path.exists(HB_FILE):
        log(f"  ⚠️ hb_xiaojiu.json 不存在，可能 repo 未同步或小九从未写过心跳")
        return True, 0, ""  # 无法确认掉线，默认活着

    try:
        with open(HB_FILE, encoding="utf-8") as f:
            hb = json.load(f)
        last_ts = hb.get("last_time", "")
        if not last_ts:
            log(f"  ⚠️ hb_xiaojiu.json 无 last_time 字段")
            return True, 0, ""
        peer_time = datetime.strptime(last_ts, "%Y-%m-%d %H:%M:%S")
        elapsed = (datetime.now() - peer_time).total_seconds() / 60.0
        return elapsed < PEER_FAILOVER_THRESHOLD_MIN, elapsed, last_ts
    except Exception as e:
        log(f"  ❌ 读 hb_xiaojiu.json 失败: {e}")
        return True, 0, ""  # 解析失败，防御性认为活着


def send_alert_email(silent_min, hb_last_time):
    """小九失联时发邮件告警到主人QQ邮箱。带冷却，避免每30分钟刷屏。返回是否实际发送。"""
    now = datetime.now()

    # 冷却检查：同一次失联事件内，最多每 ALERT_COOLDOWN_HOURS 小时发一次
    try:
        if os.path.exists(ALERT_STATE_FILE):
            st = json.load(open(ALERT_STATE_FILE, encoding="utf-8"))
            last = st.get("last_alert_ts")
            if last:
                last_dt = datetime.strptime(last, "%Y-%m-%d %H:%M:%S")
                if (now - last_dt).total_seconds() < ALERT_COOLDOWN_HOURS * 3600:
                    log(f"  ⏳ 邮件告警冷却中（上次 {last}），本次跳过发送")
                    return False
    except Exception:
        pass

    subject = f"🚨 九宝量化-小九失联告警 ({now.strftime('%m-%d %H:%M')})"
    body = (
        "【九宝量化 v6.0 双机监控告警】\n\n"
        f"阿狸咪（家里机）检测到小九（单位机）心跳失联！\n\n"
        f"· 小九最后心跳：{hb_last_time}\n"
        f"· 已沉默：{silent_min:.0f} 分钟（阈值 {PEER_FAILOVER_THRESHOLD_MIN} 分钟）\n"
        f"· 检测时间：{now.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"· 当前模式：只读哨兵（--alert-only），阿狸咪未自动接管\n\n"
        "可能的故障：小九停电 / 断网 / 系统崩溃 / 进程卡死。\n"
        "请确认小九状态；如需阿狸咪接管，请明确下令。\n\n"
        "---\n阿狸咪自动监控 | peer_health_monitor.py 发送"
    )
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = SMTP_USER
        msg["To"] = SMTP_TO
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15)
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, [SMTP_TO], msg.as_string())
        server.quit()
        log(f"  ✅ 失联告警邮件已发送至 {SMTP_TO}")
        with open(ALERT_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_alert_ts": now.strftime("%Y-%m-%d %H:%M:%S")}, f)
        return True
    except Exception as e:
        log(f"  ❌ 告警邮件发送失败: {e}")
        return False


def reset_alert_state():
    """小九恢复正常时清除告警冷却，下次失联立即发信。"""
    try:
        if os.path.exists(ALERT_STATE_FILE):
            os.remove(ALERT_STATE_FILE)
    except Exception:
        pass


def main():
    # 1. 交易日判断（只有交易日才需要盘中监控）
    try:
        sys.path.insert(0, BASE)
        from is_trading_day import is_trading_day as itd
        if not itd(datetime.now().date()):
            log("⏭️ 非交易日，跳过监控")
            return 0
    except ImportError:
        # 模块缺失，fallback 到 weekday 判断
        if datetime.now().weekday() >= 5:
            log("⏭️ 周末且无法判断调休，跳过监控")
            return 0

    # 2. 时间窗口：仅工作日 08:00-21:30 才监控（收盘部署已结束）
    now = datetime.now()
    window_start = now.replace(hour=8, minute=0, second=0)
    window_end = now.replace(hour=21, minute=30, second=0)
    if now < window_start or now > window_end:
        log(f"⏭️ 非监控窗口（08:00-21:30），跳过")
        return 0

    # 3. 检查小九状态
    alive, silent_min, hb_last = check_peer_alive()

    if alive:
        log(f"✅ 小九正常（最近心跳 {silent_min:.0f} 分钟前）")
        reset_alert_state()  # 恢复即清冷却，下次失联立即发信
        return 0

    # 4. 小九沉默超时 → 触发
    log(f"🔴 小九心跳已 {silent_min:.0f} 分钟（> {PEER_FAILOVER_THRESHOLD_MIN}min），判为掉线！")
    # 立即发邮件告警（无论是否自动接管，都先通知主人）
    send_alert_email(silent_min, hb_last)

    if "--alert-only" in sys.argv:
        # 只读哨兵模式（2026-07-27 主人指令：阿狸咪冷备，发现失联只报警，
        # 恢复 ACTIVE 必须等主人明确下令，严禁自动激活救援任务）
        log("🚨 ALERT-ONLY 模式：仅报警，不激活任何救援任务。请人工确认小九状态！")
        return 1

    log(f"🚀 调用 audit_automations.py 激活阿狸咪救火任务...")

    r = subprocess.run(
        [sys.executable, "audit_automations.py"],
        cwd=BASE, capture_output=True, text=True, timeout=120
    )

    if r.returncode == 0:
        # 从输出中提取 peer_failover 激活条目
        output = r.stdout + r.stderr
        activated_count = output.count("peer_failover_activated")
        log(f"✅ 阿狸咪救火任务已激活（{activated_count} 个），查看 audit log")
        return 1

    log(f"❌ audit_automations.py 失败 (exit={r.returncode}): {r.stderr[:300]}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
