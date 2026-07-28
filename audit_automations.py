#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
audit_automations.py — WorkBuddy 自动化全量审计 + 防御性修复

用途：
    每日/每小时自动审计本机所有 WorkBuddy 自动化任务的健康状态：
    1) model_id 检查：必须是 API 接受的有效模型（防止 ds-V4-FLASH 之类的拼写错误死灰复燃）
    2) 静默失败检查：扫描 automation_runtime_state.last_error 找持续失败的 task
    3) 心跳缺失检查：对比 _heartbeat.log 和预期任务表，找出应跑未跑的任务
    4) cwds 路径检查：确保任务的 working directory 实际存在
    5) rrule 合法性检查：所有 rrule 必须是合法 RFC5545
    6) neodata token 时效（防止运维状态卡显示令牌过期红 ❌）
    7) ops_status 一致性（数据源时间 vs 实际令牌时间）
    8) hy3 额度守卫：hy3 免费算力耗尽时自动切全部任务到 deepseek-v4-flash

    防御性修复：
    - 发现 model_id 不在 VALID_MODELS 中 → 自动改回 VALID_MODELS[0]（默认 deepseek-v4-flash）
    - hy3 额度耗尽（检测 429/频率限制错误）→ 自动把当前 hy3/auto 任务切到 deepseek-v4-flash
    - 其他问题只告警，不自动改（避免误操作）

    输出：
    - data/ops_status.json 增 "audit" 段
    - _heartbeat.log 写 "audit_YYYYMMDD_HHMMSS" 行
    - 严重问题通过 send_alert.py 推送给小九

依赖：Python 3.x 标准库
触发：每日 09:00（工作日），由 automation-1785000000001（小九-每日自动化审计）调用
"""

import os
import sys
import json
import time
import sqlite3
import datetime
import subprocess
import re
import glob
from collections import defaultdict

REPO = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.expanduser("~/.workbuddy/workbuddy.db")
HB_PATH = os.path.join(REPO, "_heartbeat.log")
OPS_PATH = os.path.join(REPO, "data", ".ops_status.json")

# 铁律：API 接受的有效模型（来自 API 错误回包"Currently supported models"）
# 任何不在此列表的 model_id 都会触发 HTTP 400 静默拒绝
VALID_MODELS = {
    "deepseek-v4-flash",  # 默认/主力（2026-07-21 起小九所有新任务统一用这个）
    "deepseek-v4-pro",    # 重型/盘后长流程
    "auto",               # 调度器自动选型
    "hy3",                # 旧的稳定模型（兼容）
    "hy3-preview-agent",  # 旧预览模型（兼容）
    "glm-5.2",            # 备用
    "glm-5.1",            # 备用
    "glm-5v-turbo",       # 视觉备用
    "kimi-k3-2",          # 备用
    "kimi-k2.7",          # 备用
    "kimi-k2.6",          # 备用
    "minimax-m3-pay",     # 备用
}

# 用户口语化简称 → 正确 API 名（防御性映射）
# 历史教训：2026-07-21 用户说"ds-V4-FLASH"被误写入 22 个任务，5 小时盘中数据无更新
MODEL_ALIASES = {
    "ds-V4-FLASH":      "deepseek-v4-flash",
    "ds-v4-flash":      "deepseek-v4-flash",
    "ds-V4Flash":       "deepseek-v4-flash",
    "DS-V4-FLASH":      "deepseek-v4-flash",
    "deepseek-flash":   "deepseek-v4-flash",
    "v4-flash":         "deepseek-v4-flash",
    "v4_flash":         "deepseek-v4-flash",
    "V4-FLASH":         "deepseek-v4-flash",
    "deepseek_v4_flash":"deepseek-v4-flash",
    "ds_flash":         "deepseek-v4-flash",
}

DEFAULT_MODEL = "deepseek-v4-flash"  # 修复时使用的兜底模型

# neodata token 早过期阈值（小时）：token 有效期 ~24h，提前 N 小时告警
NEODATA_TOKEN_WARN_HOURS = 4
NEODATA_TOKEN = os.path.join(REPO, ".neodata_token")

# ─── hy3 额度守卫 ───
# 用户首选 hy3（免费额度有限），后备 deepseek-v4-flash（便宜无额度限制）
# 策略：当检测到 hy3 任务出现 429/频率限额错误时，自动把所有 hy3 任务切到 deepseek-v4-flash
#       当后续 hy3 任务连续成功 X 次不再 429 时，切回 hy3
# 状态跟踪文件
MODEL_STATE = os.path.join(REPO, ".model_state.json")
# 触发切换的连续 429 错误次数阈值
HY3_429_THRESHOLD = 2
# 切换后，连续成功次数达到此值则恢复 hy3
HY3_RECOVER_SUCCESS = 3
# 最近成功/失败记录保留窗口（条数）
HY3_TRACK_WINDOW = 20

# 关键预期任务表（与小九盘前/盘后/盘中等核心任务对应）
# 注：与 check_all_deploys.py 的 TASKS 保持同步
EXPECTED_WORKDAY_TASKS = [
    ("08:00", "08_交接检查"),
    ("08:30", "candidate_pool_watchdog"),  # 整点任务也覆盖
    ("08:15", "pre_market_deploy"),
    ("09:00", "candidate_pool_watchdog"),
    ("09:25", "IPO打新"),
    ("09:30", "candidate_pool_watchdog"),
    ("09:30", "intraday_09_30"),
    ("10:00", "candidate_pool_watchdog"),
    ("10:05", "pre_market_deploy_self_heal"),
    ("10:30", "candidate_pool_watchdog"),
    ("10:31", "intraday_10_31"),
    ("11:00", "candidate_pool_watchdog"),
    ("11:30", "candidate_pool_watchdog"),
    ("11:46", "intraday_11_46"),
    ("12:00", "candidate_pool_watchdog"),
    ("13:00", "candidate_pool_watchdog"),
    ("13:30", "candidate_pool_watchdog"),
    ("13:31", "intraday_13_31"),
    ("14:00", "candidate_pool_watchdog"),
    ("14:30", "candidate_pool_watchdog"),
    ("14:31", "intraday_14_31"),
    ("15:00", "candidate_pool_watchdog"),
    ("15:30", "candidate_pool_watchdog"),
    ("16:00", "candidate_pool_watchdog"),
    ("16:30", "candidate_pool_watchdog"),
    ("16:31", "post_close_16_31"),
    ("17:25", "neodata_token_17_25"),
    ("17:31", "neodata_17_31"),
    ("19:30", "close_19_30_deploy"),
]


def now():
    return datetime.datetime.now()


def log(msg):
    print(f"[audit] {msg}")


def check_model_ids(cur):
    """
    检查所有 ACTIVE 任务的 model_id 合法性。
    - 错配（不在 VALID_MODELS 也不在 MODEL_ALIASES）→ 告警
    - 别名（ds-V4-FLASH 等）→ 自动修复为 DEFAULT_MODEL
    - 空（未设置）→ 告警（不应使用空，会导致默认行为不确定）
    返回：(issues_list, fixed_count)
    """
    cur.execute("SELECT id, name, model_id FROM automations WHERE deleted_at IS NULL")
    rows = cur.fetchall()
    issues = []
    fixed = 0
    for aid, name, mid in rows:
        if not mid:
            issues.append({"level": "WARN", "type": "empty_model", "id": aid, "name": name,
                           "msg": f"task '{name}' has empty model_id (will use system default)"})
            continue
        # 检查别名 → 自动修复
        if mid in MODEL_ALIASES:
            target = MODEL_ALIASES[mid]
            cur.execute("UPDATE automations SET model_id=? WHERE id=?", (target, aid))
            issues.append({"level": "FIXED", "type": "model_alias", "id": aid, "name": name,
                           "msg": f"auto-fixed '{mid}' → '{target}'"})
            fixed += 1
            continue
        # 检查合法
        if mid not in VALID_MODELS:
            issues.append({"level": "ERROR", "type": "invalid_model", "id": aid, "name": name,
                           "msg": f"task '{name}' has INVALID model_id '{mid}' — API will HTTP 400 reject"})
    return issues, fixed


def check_silent_failures(cur):
    """扫描 automation_runtime_state 找持续失败的任务（last_error 含关键字）

    2026-07-23 修复：原查询直接读 automation_runtime_state，未 JOIN automations，
    导致已软删除（deleted_at 非 NULL）/已重建换 id 的残留 last_error 被当成
    "静默失败"误报。现 JOIN automations 并只统计「未删除 + 活跃」的任务，
    与 check_cwds_paths / check_rrule_validity 的过滤口径一致。
    """
    cur.execute("""
        SELECT ar.automation_id, ar.last_error, ar.last_run_at
        FROM automation_runtime_state ar
        JOIN automations a ON a.id = ar.automation_id
        WHERE ar.last_error IS NOT NULL AND ar.last_error != ''
          AND a.deleted_at IS NULL AND a.status = 'ACTIVE'
        ORDER BY ar.last_run_at DESC
        LIMIT 20
    """)
    issues = []
    for aid, err, last_run in cur.fetchall():
        if not err:
            continue
        # 静默失败的特征关键词
        keywords = ["400", "model", "refus", "service info not found", "internal", "stopped before"]
        if any(k.lower() in err.lower() for k in keywords):
            issues.append({"level": "ERROR", "type": "silent_failure", "id": aid,
                           "msg": f"task last error: {err[:120]}", "last_run": last_run})
    return issues


def check_heartbeat_coverage():
    """
    读 _heartbeat.log，对比 EXPECTED_WORKDAY_TASKS，找出今天本工作日应跑但没跑的任务。
    只在工作时间(08:00~18:00)且为工作日才检查。
    """
    if not os.path.exists(HB_PATH):
        return [{"level": "WARN", "type": "no_heartbeat", "msg": "_heartbeat.log not found"}]

    n = now()
    if n.weekday() >= 5:  # 周末
        return []
    if n.hour < 8 or n.hour >= 18:
        return []  # 非工作时间不查

    today = n.strftime("%Y-%m-%d")
    done_tasks = set()
    with open(HB_PATH, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line.startswith(today):
                continue
            # 解析 "TIMESTAMP | HOST | TASK | STATUS | EXTRA"
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 4:
                continue
            task = parts[2]
            status = parts[3]
            if status.upper() == "DONE":
                done_tasks.add(task)

    # 找出"应跑过但没跑"的任务
    issues = []
    for time_str, task in EXPECTED_WORKDAY_TASKS:
        th, tm = map(int, time_str.split(":"))
        # 若当前时间已过此任务触发时间+15分钟，且未在 done 集合
        if n.hour > th or (n.hour == th and n.minute >= tm + 15):
            if not any(t.lower() in (k.lower() for k in done_tasks) for t in [task]):
                # 模糊匹配（任务名可能在 DONE 中有后缀如 intraday_09_30）
                matched = False
                for done_task in done_tasks:
                    if task.lower() in done_task.lower() or done_task.lower() in task.lower():
                        matched = True
                        break
                if not matched:
                    issues.append({"level": "WARN", "type": "missing_heartbeat", "time": time_str,
                                   "task": task, "msg": f"{time_str} {task} 应跑但 _heartbeat.log 无 DONE"})
    return issues


def check_cwds_paths(cur):
    """检查所有 ACTIVE 任务的 cwds 路径是否存在"""
    cur.execute("SELECT id, name, cwds FROM automations WHERE deleted_at IS NULL AND status='ACTIVE'")
    issues = []
    for aid, name, cwds in cur.fetchall():
        if not cwds:
            continue
        # cwds 可能是单路径字符串或 JSON 数组
        paths = []
        try:
            if cwds.strip().startswith("["):
                paths = json.loads(cwds)
            else:
                paths = [cwds]
        except Exception:
            paths = [cwds]
        for p in paths:
            if not os.path.exists(p):
                issues.append({"level": "ERROR", "type": "bad_cwds", "id": aid, "name": name,
                               "msg": f"task '{name}' cwds path missing: {p}"})
    return issues


def check_rrule_validity(cur):
    """检查所有 ACTIVE 任务的 rrule 合法性（粗校验：FREQ / BYDAY / BYHOUR / BYMINUTE 至少有其一）"""
    cur.execute("SELECT id, name, rrule FROM automations WHERE deleted_at IS NULL AND status='ACTIVE'")
    issues = []
    for aid, name, rrule in cur.fetchall():
        if not rrule:
            issues.append({"level": "WARN", "type": "empty_rrule", "id": aid, "name": name,
                           "msg": f"task '{name}' has empty rrule"})
            continue
        # 基础 RFC5545 检查：必须含 FREQ
        if "FREQ=" not in rrule.upper():
            issues.append({"level": "ERROR", "type": "invalid_rrule", "id": aid, "name": name,
                           "msg": f"task '{name}' rrule missing FREQ: {rrule[:80]}"})
    return issues


def check_neodata_token():
    """检查 .neodata_token 时效（防止 运维状态 卡片显示"令牌:已过期"红 ❌）
    阈值：token saved_at + 24h - NEODATA_TOKEN_WARN_HOURS → 提前 4h 告警
    """
    if not os.path.exists(NEODATA_TOKEN):
        return [{"level": "ERROR", "type": "no_neodata_token",
                 "msg": f".neodata_token 文件不存在（路径={NEODATA_TOKEN}）；neodata 抓取将全部跳过"}]
    try:
        with open(NEODATA_TOKEN, encoding="utf-8") as f:
            tok = json.load(f)
        token = tok.get("token", "")
        saved_at = int(tok.get("saved_at", 0))
        if not token or not token.startswith("tk_"):
            return [{"level": "ERROR", "type": "bad_neodata_token",
                     "msg": ".neodata_token 内容异常（token 不以 tk_ 开头）；运营卡片将显示令牌:已过期 红"}]
        if saved_at <= 0:
            return [{"level": "WARN", "type": "no_saved_at",
                     "msg": ".neodata_token 缺少 saved_at 字段，无法判断时效"}]
        # 阈值：saved_at + 24h - 4h（早 4 小时告警）
        now_ts = int(time.time())
        expires_ts = saved_at + 24 * 3600
        warn_ts = expires_ts - NEODATA_TOKEN_WARN_HOURS * 3600
        if now_ts >= expires_ts:
            return [{"level": "ERROR", "type": "expired_neodata_token",
                     "msg": f"neodata token 已过期 {(now_ts - expires_ts) // 60} 分钟；立即手动刷新或等 17:25 自动化"}]
        if now_ts >= warn_ts:
            remain_h = (expires_ts - now_ts) / 3600
            return [{"level": "WARN", "type": "neodata_token_expiring",
                     "msg": f"neodata token 还有 {remain_h:.1f} 小时过期（< {NEODATA_TOKEN_WARN_HOURS}h 阈值）"}]
        return []
    except Exception as e:
        return [{"level": "ERROR", "type": "neodata_token_read_fail",
                 "msg": f"读 .neodata_token 失败: {e}"}]


def check_ops_status_consistency():
    """检查 ops_status.json 与 data/*.json 实际状态的一致性
    - neodata_valid_until vs .neodata_token 的 saved_at + 24h
    - three_party.xiaojiu.last_time vs 实际最近 deploy 时间
    """
    ops_path = os.path.join(REPO, "data", ".ops_status.json")
    if not os.path.exists(ops_path):
        return [{"level": "WARN", "type": "no_ops_status", "msg": "data/.ops_status.json 不存在"}]
    try:
        with open(ops_path, encoding="utf-8") as f:
            ops = json.load(f)
    except Exception as e:
        return [{"level": "ERROR", "type": "ops_status_read_fail", "msg": f"读 .ops_status.json 失败: {e}"}]
    issues = []
    # 1) neodata_valid_until 与 .neodata_token 一致性
    if os.path.exists(NEODATA_TOKEN):
        try:
            with open(NEODATA_TOKEN, encoding="utf-8") as f:
                tok = json.load(f)
            saved = int(tok.get("saved_at", 0))
            expected_valid = saved + 24 * 3600
            stored_valid = ops.get("neodata_valid_until")
            if stored_valid:
                # 解析 stored_valid 格式
                try:
                    stored_ts = int(datetime.datetime.strptime(stored_valid, "%Y-%m-%d %H:%M:%S").timestamp())
                    if abs(stored_ts - expected_valid) > 300:  # 差 5 分钟以上视为不一致
                        issues.append({"level": "WARN", "type": "ops_neodata_mismatch",
                                       "msg": f"ops_status.json neodata_valid_until={stored_valid} 与 .neodata_token 实际 saved_at+24h 不一致"})
                except Exception:
                    pass
        except Exception:
            pass
    # 2) three_party xiaojiu 时间不超过 1 小时（说明最近没部署）
    tp = ops.get("three_party", {})
    xj = tp.get("xiaojiu", {})
    if xj.get("last_time"):
        try:
            last_ts = int(datetime.datetime.strptime(xj["last_time"], "%Y-%m-%d %H:%M:%S").timestamp())
            age_h = (int(time.time()) - last_ts) / 3600
            if age_h > 1 and 9 <= datetime.datetime.now().hour <= 18:  # 盘中1小时无部署
                issues.append({"level": "WARN", "type": "xiaojiu_stale",
                               "msg": f"小九最近部署 {age_h:.1f} 小时前（{xj['last_time']}），盘中应 < 1h"})
        except Exception:
            pass
    return issues


def _read_model_state():
    """读 .model_state.json，缺字段就用默认"""
    default = {
        "hy3_available": True,            # hy3 当前是否可用
        "hy3_429_count": 0,                # 连续 429 次数
        "hy3_success_count": 0,            # 切换后连续成功次数
        "last_switch_time": None,         # 最近一次切换时间（切到 deepseek-v4-flash）
        "last_429_time": None,            # 最近一次 429 时间
        "last_success_time": None,         # 最近一次 hy3 成功时间
        "preferred_model": "hy3",
        "fallback_model": "deepseek-v4-flash",
        "model_history": [],               # 最近 HY3_TRACK_WINDOW 条记录 [(ts, model_used, success), ...]
    }
    if not os.path.exists(MODEL_STATE):
        return default
    try:
        with open(MODEL_STATE, encoding="utf-8") as f:
            d = json.load(f)
        for k in default:
            d.setdefault(k, default[k])
        return d
    except Exception:
        return default


def _save_model_state(state):
    os.makedirs(os.path.dirname(MODEL_STATE), exist_ok=True)
    with open(MODEL_STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def quota_guard():
    """
    hy3 额度守卫：
    - 扫描最近 HY3_TRACK_WINDOW 条 runtime_state（所有任务·所有模型），看当前是否出现 429/频率限额错误
    - 重点关注当前使用 hy3/auto 模型的任务
    - 当检测到连续 HY3_429_THRESHOLD 次 429 → 把所有 hy3 任务切到 deepseek-v4-flash
    - 当切换到 fallback 后，连续 HY3_RECOVER_SUCCESS 次无 429 → 切回 hy3
    """
    db_path = os.path.expanduser("~/.workbuddy/workbuddy.db")
    if not os.path.exists(db_path):
        return [], 0  # (issues, switched_count)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    issues = []
    switched = 0
    state = _read_model_state()

    # 1. 扫描最近 runtime_state 中带有 429/频率限额/超额 的记录
    q = ("SELECT automation_id, last_error, last_run_at FROM automation_runtime_state "
         "WHERE last_error IS NOT NULL AND last_error != '' "
         "ORDER BY last_run_at DESC LIMIT ?")
    cur.execute(q, (HY3_TRACK_WINDOW,))
    recent_429 = 0
    recent_ok = 0
    latest_429_time = state.get("last_429_time")
    latest_ok_time = state.get("last_success_time")
    for aid, err, run_at in cur.fetchall():
        is_429 = False
        if err:
            lower = err.lower()
            # 429 特征：频率限制/超出使用量/quota/额度/too many requests/rate limit
            if any(k in lower for k in ["429", "频率限制", "使用量已超出", "quota", "额度",
                                         "too many requests", "rate limit", "130009"]):
                is_429 = True
            # 检查 model_id 是 hy3 还是其他
            cur2 = conn.cursor()
            cur2.execute("SELECT model_id FROM automations WHERE id=?", (aid,))
            mrow = cur2.fetchone()
            cur2.close()
            if mrow:
                mid = mrow[0]
                if mid in ("hy3", "auto") and is_429:
                    recent_429 += 1
                    if run_at and (latest_429_time is None or run_at > latest_429_time):
                        latest_429_time = run_at
                elif mid in ("hy3", "auto") and not is_429:
                    # 非 429 错误不算成功（成功不应有 error）
                    pass

    # 2. 检查当前所有 hy3 任务的最近一次运行是否有 429
    cur.execute("SELECT id, name FROM automations WHERE model_id='hy3' AND deleted_at IS NULL")
    hy3_tasks = cur.fetchall()
    cur.execute("SELECT id, name FROM automations WHERE model_id='auto' AND deleted_at IS NULL")
    auto_tasks = cur.fetchall()

    full_429_count = recent_429
    state["hy3_429_count"] = full_429_count

    # 3. 判断：连续 HY3_429_THRESHOLD 次 429 → 切
    if full_429_count >= HY3_429_THRESHOLD and state.get("hy3_available", True):
        # hy3 当前在(或auto在), 且最近多数是 429 → 切到 deepseek-v4-flash
        switch_targets = hy3_tasks + auto_tasks
        switched_ids = []
        for aid, name in switch_targets:
            cur.execute("UPDATE automations SET model_id=? WHERE id=?", ("deepseek-v4-flash", aid))
            switched += 1
            switched_ids.append(aid)
            log(f"[quota_guard] 🔄 {name}({aid}): hy3→deepseek-v4-flash (连续{full_429_count}次429)")
        conn.commit()
        state["hy3_available"] = False
        state["last_switch_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state["hy3_success_count"] = 0
        state["switched_tasks"] = switched_ids  # 记录被切的任务ID，恢复时只还原这些
        issues.append({"level": "FIXED", "type": "quota_switch",
                       "msg": f"hy3 额度耗尽（连续 {full_429_count} 次 429 错误），已将 {switched} 个任务切到 deepseek-v4-flash"})

    elif full_429_count == 0 and not state.get("hy3_available", True):
        # 已切到 fallback，现在 429 清了 → 恢复 hy3
        state["hy3_success_count"] += 1
        if state["hy3_success_count"] >= HY3_RECOVER_SUCCESS:
            # 恢复：只恢复之前被切的任务（hy3 盘中任务），不动原本就是 deepseek-v4-flash 的盘后任务
            restore_count = 0
            switched_ids = state.get("switched_tasks", [])
            placeholders = ",".join("?" * len(switched_ids)) if switched_ids else ""
            if placeholders:
                cur.execute(f"SELECT id, name FROM automations WHERE id IN ({placeholders}) AND deleted_at IS NULL", switched_ids)
                for aid, name in cur.fetchall():
                    cur.execute("UPDATE automations SET model_id=? WHERE id=?", ("hy3", aid))
                    restore_count += 1
                    log(f"[quota_guard] 🔄 {name}({aid}): deepseek-v4-flash→hy3 (额度恢复)")
            if restore_count > 0:
                conn.commit()
                state["hy3_available"] = True
                state["hy3_429_count"] = 0
                state["last_switch_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                issues.append({"level": "FIXED", "type": "quota_restore",
                               "msg": f"hy3 额度恢复（连续 {state['hy3_success_count']} 次无 429），已将 {switched} 个任务恢复为 hy3"})
            else:
                state["hy3_available"] = True
    elif not state.get("hy3_available", True):
        # 已切但仍有 429（不是 hy3 的，可能是全局限制）
        other_429_msg = f"hy3 已切 fallback，但仍有 {full_429_count} 次 429（可能全局限流）"
        issues.append({"level": "WARN", "type": "quota_persist", "msg": other_429_msg})

    # 更新记录
    if latest_429_time:
        state["last_429_time"] = latest_429_time
    if latest_ok_time:
        state["last_success_time"] = latest_ok_time

    # 模型历史（滚动）
    history = state.get("model_history", [])
    now_ts = datetime.datetime.now().timestamp()
    history.append([now_ts, "hy3" if state["hy3_available"] else "deepseek-v4-flash",
                    full_429_count == 0])
    if len(history) > HY3_TRACK_WINDOW:
        history = history[-HY3_TRACK_WINDOW:]
    state["model_history"] = history
    _save_model_state(state)
    conn.close()
    return issues, switched


# ─── 云端沉默兜底（silent_failover）───
# 用户架构要求 (2026-07-21): "云主力+本兜底"。本机盘中 5 + 盘后 1 默认 PAUSED，
# 防止和云端同时段双跑竞态。但当云端某个时间点沉默>30min（GitHub Actions 挂/网络断/cron miss），
# 本机自动激活对应任务做兜底跑。云端恢复后自动 PAUSED 回去。
SILENT_FAILOVER_THRESHOLD_MIN = 30   # 沉默超过 N 分钟触发兜底
# 本机盘中 + 盘后任务（云端主力，本机兜底）
FAILOVER_BACKUP_TASKS = {
    "automation-1784516582539": "intraday_09_30",
    "automation-1784516582857": "intraday_10_31",
    "automation-1784516582189": "intraday_11_46",
    "automation-1784516583499": "intraday_13_31",
    "automation-1784516583205": "intraday_14_31",
    "automation-1784516583790": "post_close_16_31",
}
# 云端期望部署时间窗口（cron 时间点 ± 5 分钟）
CLOUD_EXPECTED_SLOTS = {
    "intraday_09_30": (9, 30),
    "intraday_10_31": (10, 31),
    "intraday_11_46": (11, 46),
    "intraday_13_31": (13, 31),
    "intraday_14_31": (14, 31),
    "post_close_16_31": (16, 31),
}

# ─── 小九沉默兜底（peer_failover）───
# 2026-07-23 新增：小九是主力机（阿狸咪仅为救援船），当小九 heartbeat>60min 沉默，
# 表示小九停电/断网/系统崩溃，阿狸咪应自动激活救火任务补跑。
PEER_FAILOVER_THRESHOLD_MIN = 60    # 小九沉默超过 N 分钟→判为掉线
# 阿狸咪主机上 PAUSED 的小九救火任务（仅在阿狸咪本机 DB，小九 DB 无这些 ID）
PEER_FAILOVER_TASKS = {
    "automation-1783525364826": "close_p1_deputy",    # 17:45 收盘一段兜底
    "automation-1783525370164": "close_p2_deputy",    # 19:05 收盘二段兜底
    "automation-1781294395804": "close_deploy_final", # 19:31 收盘最终部署
    "automation-1784128040505": "backup_deputy",      # 21:10 备份兜底
    "automation-1783522751504": "pre_market_deputy",  # 08:30 IPO 研判（小九代管后失联→自扛）
}
# 小九各档位的期望心跳时间窗口（按计划的最后可能上线时间）
PEER_EXPECTED_SLOTS = {
    "close_p1_deputy":    (17, 50),  # close_p1 17:30 启动，17:50 应该有心跳
    "close_p2_deputy":    (19, 15),  # close_p2 19:05 启动，19:15 应该有心跳
    "close_deploy_final": (19, 45),  # close_deploy 19:31 启动，19:45 应该有心跳
    "backup_deputy":      (21, 20),  # backup 21:10 启动，21:20 应该有心跳
    "pre_market_deputy":  (9,  0),   # 08:30 IPO 研判后，09:00 前应有心跳
}


def silent_failover():
    """
    云端沉默兜底：
    - 读取 hb_cloud.json 的 last_time 与当前时间差
    - 超过 SILENT_FAILOVER_THRESHOLD_MIN 分钟 → 沉默
    - 对每个本机兜底任务：
      - 如果对应云端时间点已过 + 沉默 → ACTIVE 激活（让 WorkBuddy 调度器立即跑）
      - 如果云端已恢复（沉默结束） → PAUSED 回去
    """
    hb_path = os.path.join(REPO, "data", "hb_cloud.json")
    if not os.path.exists(hb_path):
        return [], []  # (issues, activated_list)
    try:
        with open(hb_path, encoding="utf-8") as f:
            cloud_hb = json.load(f)
        cloud_last_ts = cloud_hb.get("last_time", "")
        if not cloud_last_ts:
            return [], []
        # 解析 "2026-07-21 12:36:16" → unix ts
        from datetime import datetime as _dt
        cloud_ts = _dt.strptime(cloud_last_ts, "%Y-%m-%d %H:%M:%S").timestamp()
    except Exception as e:
        return [{"level": "WARN", "type": "silent_failover_read_fail",
                 "msg": f"读 hb_cloud.json 失败: {e}"}], []

    now_ts = int(time.time())
    silent_min = (now_ts - cloud_ts) / 60.0
    issues = []
    activated = []
    db_path = os.path.expanduser("~/.workbuddy/workbuddy.db")
    if not os.path.exists(db_path):
        return issues, activated
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    now_h, now_m = datetime.datetime.now().hour, datetime.datetime.now().minute
    for task_id, slot_name in FAILOVER_BACKUP_TASKS.items():
        # 这个时间点云端应该部署过了吗？
        exp_h, exp_m = CLOUD_EXPECTED_SLOTS[slot_name]
        slot_passed = (now_h > exp_h) or (now_h == exp_h and now_m >= exp_m + 5)
        if not slot_passed:
            continue  # 时辰未到，不算沉默
        # 查当前 status
        cur.execute("SELECT status, name FROM automations WHERE id=? AND deleted_at IS NULL", (task_id,))
        row = cur.fetchone()
        if not row:
            continue
        current_status = row[0]
        if silent_min > SILENT_FAILOVER_THRESHOLD_MIN:
            # 云端沉默超时 → 激活兜底
            if current_status != "ACTIVE":
                cur.execute("UPDATE automations SET status='ACTIVE' WHERE id=?", (task_id,))
                activated.append((task_id, row[1], slot_name, silent_min))
                issues.append({"level": "FIXED", "type": "silent_failover_activated",
                               "msg": f"云端沉默 {silent_min:.0f}min，{row[1]}（{slot_name}）已激活兜底"})
        else:
            # 云端正常 → 兜底任务保持 PAUSED
            if current_status != "PAUSED":
                cur.execute("UPDATE automations SET status='PAUSED' WHERE id=?", (task_id,))
                activated.append((task_id, row[1], slot_name, silent_min))
                issues.append({"level": "FIXED", "type": "silent_failover_restored",
                               "msg": f"云端已恢复（{silent_min:.0f}min），{row[1]}（{slot_name}）已 PAUSED 回去"})
    conn.commit()
    conn.close()
    return issues, activated


def peer_failover():
    """
    小九沉默兜底（仅阿狸咪主机有意义）：
    - 读取 hb_xiaojiu.json 的 last_time 与当前时间差
    - 超过 PEER_FAILOVER_THRESHOLD_MIN 分钟 → 判小九掉线
    - 对本机 PEER_FAILOVER_TASKS：
      - 对应时间窗口已过 + 小九沉默 → ACTIVE 激活（让阿狸咪补跑）
      - 小九恢复 → PAUSED 回去
    """
    hb_path = os.path.join(REPO, "data", "hb_xiaojiu.json")
    if not os.path.exists(hb_path):
        return [], []  # 无心跳文件，不决策
    try:
        with open(hb_path, encoding="utf-8") as f:
            peer_hb = json.load(f)
        peer_last_ts = peer_hb.get("last_time", "")
        if not peer_last_ts:
            return [], []
        peer_ts = datetime.datetime.strptime(peer_last_ts, "%Y-%m-%d %H:%M:%S").timestamp()
    except Exception as e:
        return [{"level": "WARN", "type": "peer_failover_read_fail",
                 "msg": f"读 hb_xiaojiu.json 失败: {e}"}], []

    now_ts = int(time.time())
    silent_min = (now_ts - peer_ts) / 60.0
    issues = []
    activated = []
    db_path = os.path.expanduser("~/.workbuddy/workbuddy.db")
    if not os.path.exists(db_path):
        return issues, activated
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    now_h, now_m = datetime.datetime.now().hour, datetime.datetime.now().minute

    for task_id, slot_name in PEER_FAILOVER_TASKS.items():
        exp_h, exp_m = PEER_EXPECTED_SLOTS[slot_name]
        slot_passed = (now_h > exp_h) or (now_h == exp_h and now_m >= exp_m + 5)
        if not slot_passed:
            continue
        cur.execute("SELECT status, name FROM automations WHERE id=? AND deleted_at IS NULL", (task_id,))
        row = cur.fetchone()
        if not row:
            continue
        current_status = row[0]

        if silent_min > PEER_FAILOVER_THRESHOLD_MIN:
            if current_status != "ACTIVE":
                cur.execute("UPDATE automations SET status='ACTIVE' WHERE id=?", (task_id,))
                activated.append((task_id, row[1], slot_name, silent_min))
                issues.append({"level": "FIXED", "type": "peer_failover_activated",
                               "msg": f"小九沉默 {silent_min:.0f}min，{row[1]}（{slot_name}）已激活——阿狸咪接管"})
        else:
            if current_status != "PAUSED":
                cur.execute("UPDATE automations SET status='PAUSED' WHERE id=?", (task_id,))
                activated.append((task_id, row[1], slot_name, silent_min))
                issues.append({"level": "FIXED", "type": "peer_failover_restored",
                               "msg": f"小九已恢复（{silent_min:.0f}min），{row[1]}（{slot_name}）已 PAUSED 回去"})
    conn.commit()
    conn.close()
    return issues, activated


def write_ops_status(audit_result):
    """把审计结果写入 data/.ops_status.json 的 audit 段（保留其他段）"""
    existing = {}
    if os.path.exists(OPS_PATH):
        try:
            with open(OPS_PATH, encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = {}
    existing["audit"] = audit_result
    existing["audit"]["updated_at"] = now().strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(os.path.dirname(OPS_PATH), exist_ok=True)
    with open(OPS_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)


def write_heartbeat(severity, summary):
    """把审计结果写一行到 _heartbeat.log（统一心跳格式）"""
    line = f"{now().strftime('%Y-%m-%d %H:%M:%S')} | xiaojiu | audit_automations | {severity} | {summary}"
    with open(HB_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    log("==== WorkBuddy 自动化审计开始 ====")
    if not os.path.exists(DB_PATH):
        log(f"FATAL: db not found at {DB_PATH}")
        sys.exit(2)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    all_issues = []
    fixed_count = 0

    # 1. model_id 检查（带修复）
    model_issues, fixed = check_model_ids(cur)
    all_issues.extend(model_issues)
    fixed_count += fixed
    conn.commit()
    log(f"[1] model_id 检查：{len(model_issues)} 项，修复 {fixed} 个")

    # 2. 静默失败
    silent = check_silent_failures(cur)
    all_issues.extend(silent)
    log(f"[2] 静默失败：{len(silent)} 项")

    # 3. 心跳缺失
    missing = check_heartbeat_coverage()
    all_issues.extend(missing)
    log(f"[3] 心跳缺失：{len(missing)} 项")

    # 4. cwds 路径
    bad_cwds = check_cwds_paths(cur)
    all_issues.extend(bad_cwds)
    log(f"[4] cwds 路径：{len(bad_cwds)} 项")

    # 5. rrule 合法
    bad_rrule = check_rrule_validity(cur)
    all_issues.extend(bad_rrule)
    log(f"[5] rrule 合法：{len(bad_rrule)} 项")

    # 6. neodata token 时效（防止 运维状态 显示"令牌:已过期"红 ❌）
    neodata_issues = check_neodata_token()
    all_issues.extend(neodata_issues)
    log(f"[6] neodata token：{len(neodata_issues)} 项")

    # 7. ops_status.json 一致性
    ops_issues = check_ops_status_consistency()
    all_issues.extend(ops_issues)
    log(f"[7] ops_status 一致性：{len(ops_issues)} 项")

    # 8. hy3 额度守卫（已禁用 2026-07-22 — 用户手动按时间段设死模型，不再自动切换）
    # quota_issues, quota_switched = quota_guard()
    # all_issues.extend(quota_issues)
    # log(f"[8] hy3 额度守卫：{len(quota_issues)} 项, 切换 {quota_switched} 个")
    # fixed_count += quota_switched

    # 9. 云端沉默兜底（silent_failover）：本机盘中 5 + 盘后 1 默认 PAUSED，
    #    当云端某个时间点沉默>30min，自动激活对应本机任务做兜底
    failover_issues, failover_activated = silent_failover()
    all_issues.extend(failover_issues)
    log(f"[9] 云端沉默兜底：{len(failover_issues)} 项, 切换 {len(failover_activated)} 个")
    fixed_count += len(failover_activated)

    # 10. 小九沉默兜底（peer_failover）：仅阿狸咪主机有意义
    #     当小九心跳 >90min 沉默 → 判掉线 → 激活阿狸咪救火任务
    peer_issues, peer_activated = peer_failover()
    all_issues.extend(peer_issues)
    fixed_count += len(peer_activated)
    if peer_activated:
        log(f"[10] ⚠️ 小九沉默兜底：{len(peer_issues)} 项, 切换 {len(peer_activated)} 个——已激活阿狸咪救火任务")
    else:
        log(f"[10] 小九沉默兜底：{len(peer_issues)} 项, 切换 0 个（小九正常）")

    conn.close()

    # 严重度评估
    error_count = sum(1 for i in all_issues if i.get("level") == "ERROR")
    warn_count = sum(1 for i in all_issues if i.get("level") == "WARN")
    severity = "ERROR" if error_count > 0 else ("WARN" if warn_count > 0 else "OK")

    # 输出
    audit_result = {
        "severity": severity,
        "error_count": error_count,
        "warn_count": warn_count,
        "fixed_count": fixed_count,
        "issues": all_issues[:50],  # 最多 50 条
        "checked_at": now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    write_ops_status(audit_result)

    # 心跳留痕
    summary = f"E:{error_count} W:{warn_count} F:{fixed_count}"
    write_heartbeat(severity, summary)

    log(f"==== 审计完成：severity={severity}, errors={error_count}, warns={warn_count}, fixed={fixed_count} ====")
    # 退出码：0=OK, 1=有 ERROR, 2=只有 WARN
    sys.exit(0 if severity == "OK" else (1 if severity == "ERROR" else 0))


if __name__ == "__main__":
    main()
