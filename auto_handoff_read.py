#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_handoff_read.py — 阿狸咪(家用机)读取单位机小九的交接文件并汇报。

工作机制：
  1. 先 git pull --rebase，确保拿到小九最新 push 的交接文件（交接文件走 git 同步）。
  2. 扫描以下文件（按时间排序）：
       - 紧急指令: URGENT_小九_*.md / URGENT_*.md
       - 普通交接: HANDOVER_小九_*.md / HANDOVER_2026-*.md
         （自动跳过含"阿狸咪"的文件，那是阿狸咪→小九方向，不回读）
  3. 用 .handoff_read_state.json 记录已读文件，只汇报"新增"的，幂等可重复跑。
  4. 首次运行(无历史状态)自动把当前已有文件标记已读，避免历史文件刷屏。

铁律：只读不写，不改代码、不部署、不删文件。
"""
import os
import json
import glob
import datetime
import subprocess

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(WORKSPACE, ".handoff_read_state.json")


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"processed": [], "urgent_processed": [], "last_run": None}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def git_pull():
    """尽力拉取远端最新交接文件（best-effort，失败不影响本地读取）"""
    try:
        subprocess.run(
            ["git", "pull", "--rebase"],
            cwd=WORKSPACE,
            capture_output=True,
            timeout=60,
        )
    except Exception:
        pass


def collect():
    urgent, regular = [], []
    for pat in ("URGENT_小九_*.md", "URGENT_*.md"):
        urgent += glob.glob(os.path.join(WORKSPACE, pat))
    for pat in ("HANDOVER_小九_*.md", "HANDOVER_2026-*.md"):
        for f in glob.glob(os.path.join(WORKSPACE, pat)):
            base = os.path.basename(f)
            if "阿狸咪" in base:  # 阿狸咪→小九方向，不回读
                continue
            regular.append(f)
    return sorted(set(urgent)), sorted(set(regular))


def read_content(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return "(读取失败: %s)" % e


def main():
    state = load_state()
    processed = set(state.get("processed", []))
    urgent_processed = set(state.get("urgent_processed", []))

    git_pull()
    urgent, regular = collect()

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # 首次运行：把已有文件全部标记已读，避免历史文件刷屏
    if not state.get("last_run"):
        for f in urgent:
            urgent_processed.add(os.path.basename(f))
        for f in regular:
            processed.add(os.path.basename(f))
        state["processed"] = list(processed)
        state["urgent_processed"] = list(urgent_processed)
        state["last_run"] = now
        save_state(state)
        print("✅ 已初始化交接读取状态（历史文件已标记已读），后续新增文件将自动汇报。")
        return

    new_urgent = [f for f in urgent if os.path.basename(f) not in urgent_processed]
    new_regular = [f for f in regular if os.path.basename(f) not in processed]

    if not new_urgent and not new_regular:
        print("✅ 无新交接文件")
        state["last_run"] = now
        save_state(state)
        return

    if new_urgent:
        print("🔴🔴🔴 紧急指令监听 (%s) — 发现 %d 条小九紧急指令：\n" % (now, len(new_urgent)))
        for f in new_urgent:
            print("=" * 60)
            print("🔴", os.path.basename(f))
            print("=" * 60)
            print(read_content(f))
            print()
            urgent_processed.add(os.path.basename(f))

    if new_regular:
        print("📬 交接速报 (%s) — 发现 %d 个新交接文件：\n" % (now, len(new_regular)))
        for f in new_regular:
            print("=" * 60)
            print("📋", os.path.basename(f))
            print("=" * 60)
            print(read_content(f))
            print()
            processed.add(os.path.basename(f))

    state["processed"] = list(processed)
    state["urgent_processed"] = list(urgent_processed)
    state["last_run"] = now
    save_state(state)
    print("--- 已标记 %d 个文件为已读 ---" % (len(new_urgent) + len(new_regular)))


if __name__ == "__main__":
    main()
