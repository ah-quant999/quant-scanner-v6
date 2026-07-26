#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
九宝量化 v6 部署链一键审计脚本
用途：在任意机器上快速核验新旧算法残留、三重共识 A 档 wiring、前端一致性。
运行：python audit_v6_deploy_chain.py
输出：控制台结构化报告 + audit_report.json（可选）
"""

import json
import os
import re
import sqlite3
import sys
import glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DIST_DIR = ROOT / "dist"
STANDALONE_DIR = ROOT / "standalone"


def log(section, item, status, detail=""):
    icon = "✅" if status == "OK" else "⚠️" if status == "WARN" else "❌"
    print(f"{icon} [{section}] {item}")
    if detail:
        for line in detail.split("\n"):
            print(f"      {line}")


def read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"__error__": str(e)}


def audit_gen_script():
    path = ROOT / "gen_triple_consensus.py"
    if not path.exists():
        log("GEN", "gen_triple_consensus.py 存在", "FAIL")
        return
    text = path.read_text(encoding="utf-8")
    if 'if grade == "A":' in text:
        log("GEN", "生成器使用 grade == 'A'", "OK")
    else:
        log("GEN", "生成器未使用 grade == 'A'", "FAIL",
            "请检查 origin/main 上的 gen_triple_consensus.py 是否已更新")

    if "基本面A档" in text and "基本面≥B" not in text:
        log("GEN", "criteria/tag 文案已统一为 基本面A档", "OK")
    else:
        log("GEN", "criteria/tag 文案仍含 基本面≥B", "FAIL")


def audit_data_criteria():
    for label, path in [("data", DATA_DIR / "triple_consensus.json"),
                        ("dist/data", DIST_DIR / "data" / "triple_consensus.json")]:
        d = read_json(path)
        if "__error__" in d:
            log("DATA", f"{label}/triple_consensus.json 可读", "FAIL", d["__error__"])
            continue
        criteria = d.get("criteria", "")
        if "基本面A档" in criteria and "基本面≥B" not in criteria:
            log("DATA", f"{label}/triple_consensus.json criteria = 基本面A档", "OK", criteria)
        else:
            log("DATA", f"{label}/triple_consensus.json criteria 异常", "FAIL", criteria)


def audit_frontend_consistency():
    files = list(STANDALONE_DIR.glob("*.html"))
    if (DIST_DIR / "standalone").exists():
        files += list((DIST_DIR / "standalone").glob("*.html"))
    if (DIST_DIR / "index.html").exists():
        files.append(DIST_DIR / "index.html")

    total_a = 0
    total_b = 0
    b_files = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        a = text.count("基本面A档")
        b = text.count("基本面≥B")
        total_a += a
        total_b += b
        if b:
            b_files.append(f"{f.name}: {b} 处")

    log("FE", f"前端 基本面A档 出现 {total_a} 次", "OK" if total_a else "WARN")
    if total_b == 0:
        log("FE", "前端无 基本面≥B 残留", "OK")
    else:
        log("FE", f"前端仍有 基本面≥B 共 {total_b} 处", "FAIL", "\n".join(b_files))


def audit_dead_links():
    targets = [ROOT / "index.html", DIST_DIR / "index.html"]
    dead = ["multi_resonance.html", "triple_resonance.html"]
    for t in targets:
        if not t.exists():
            continue
        text = t.read_text(encoding="utf-8")
        hits = [d for d in dead if d in text]
        if hits:
            log("LINK", f"{t.name} 存在死链", "FAIL", "、".join(hits))
        else:
            log("LINK", f"{t.name} 无旧页面死链", "OK")


def audit_suspension_dead_code():
    root_html = ROOT / "index_master.html"
    if root_html.exists():
        text = root_html.read_text(encoding="utf-8")
        c = text.count("suspensionCard") + text.count("金股池异动停牌")
        if c == 0:
            log("DEAD", "index_master.html 无金股池异动停牌死代码", "OK")
        else:
            log("DEAD", f"index_master.html 仍含 {c} 处 suspension 残留", "WARN")


def audit_deploy_refresh():
    path = ROOT / "deploy_now.py"
    if not path.exists():
        log("DEPLOY", "deploy_now.py 存在", "FAIL")
        return
    text = path.read_text(encoding="utf-8")
    checks = [
        ("safe_pull 已导入", 'from git_safe_sync import safe_pull' in text),
        ("强制刷新 gen_triple_consensus.py", 'show origin/main:gen_triple_consensus.py' in text),
        ("重生 triple_consensus.json", "gen_triple_consensus.py" in text and "triple_consensus.json" in text),
        ("gh-pages copy 防御校验", "index.html" in text and "triple_consensus.json" in text and "文件缺失" in text),
    ]
    for name, ok in checks:
        log("DEPLOY", name, "OK" if ok else "FAIL")


def audit_automation_db():
    """只读读取本地 WorkBuddy 自动化 DB，列出关键自动化。"""
    cands = glob.glob(os.path.expanduser("~/.workbuddy/workbuddy.db"))
    if not cands:
        log("AUTO", "未找到 workbuddy.db", "WARN")
        return
    db = cands[0]
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = con.cursor()
        cur.execute("SELECT id, name, status, cwds, prompt FROM automations WHERE deleted_at IS NULL OR deleted_at=0")
        rows = cur.fetchall()
        total = len(rows)
        bad_cwd = []
        deploy_autos = []
        for aid, name, status, cwds, prompt in rows:
            low = (cwds or "").lower()
            if "e:\\e\\" in low or (low.startswith("e:\\") and "e:\\e\\workspace" in low):
                bad_cwd.append(f"{aid}: {name} -> {cwds}")
            p = (prompt or "").lower()
            if "deploy_now" in p or "gen_triple" in p or "scanner.py" in p:
                deploy_autos.append(f"{aid}: {name}")
        log("AUTO", f"本地活自动化共 {total} 条", "OK")
        if bad_cwd:
            log("AUTO", "发现可疑 cwd", "FAIL", "\n".join(bad_cwd))
        else:
            log("AUTO", "cwd 全部正确", "OK")
        log("AUTO", f"涉及部署/生成器的自动化 {len(deploy_autos)} 条", "OK", "\n".join(deploy_autos) or "无")
        con.close()
    except Exception as e:
        log("AUTO", "读取自动化 DB 失败", "FAIL", str(e))


def main():
    print("=" * 60)
    print("九宝量化 v6 部署链审计报告")
    print(f"ROOT: {ROOT}")
    print("=" * 60)

    audit_gen_script()
    audit_data_criteria()
    audit_frontend_consistency()
    audit_dead_links()
    audit_suspension_dead_code()
    audit_deploy_refresh()
    audit_automation_db()

    print("=" * 60)
    print("审计完成。如有 ❌/⚠️ 项，请按 HANDOVER 文档处理。")


if __name__ == "__main__":
    main()
