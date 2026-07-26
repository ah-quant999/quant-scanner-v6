#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
push_experiment_files.py — 自动把实验目录数据文件提交到 main

因为 data/experiment/ 已进 Git（.gitignore 白名单 !data/experiment/），
本脚本在本地双机跑完三重选股等实验后调用，确保云端构建时能读到最新实验数据。

用法:
  python push_experiment_files.py
"""
import os
import sys
import subprocess
import glob
from datetime import datetime

WORKSPACE = os.path.dirname(os.path.abspath(__file__))

def run(cmd, cwd=WORKSPACE):
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)


def main():
    # 只提交 experiment 目录下的 triple_select 文件
    patterns = [
        "data/experiment/triple_select_*.json",
        "data/experiment/triple_select_history.json",
    ]
    files = []
    for pat in patterns:
        files.extend(glob.glob(os.path.join(WORKSPACE, pat)))
    files = [f for f in files if os.path.exists(f)]
    if not files:
        print("[push_experiment] 无实验文件，跳过")
        return 0

    # 先检查文件是否已经在 Git 跟踪中；未跟踪则加 -f
    added = 0
    for f in files:
        rel = os.path.relpath(f, WORKSPACE)
        r = run(f"git ls-files --error-unmatch {rel}")
        if r.returncode != 0:
            run(f"git add -f {rel}")
            added += 1
        else:
            run(f"git add {rel}")
            added += 1

    # 检查是否有可提交内容
    r = run("git diff --cached --stat")
    if not r.stdout.strip():
        print("[push_experiment] 无新增/修改内容，跳过")
        return 0

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"auto: sync experiment data {now}"
    r = run(f'git commit -m "{msg}"')
    if r.returncode != 0:
        # 可能是 nothing to commit
        if "nothing to commit" in (r.stdout + r.stderr):
            print("[push_experiment] nothing to commit，跳过")
            return 0
        print(f"[push_experiment] commit 失败: {r.stderr[:200]}")
        return 1

    # push 带 SSH 超时保护 + HTTP/1.1
    env = os.environ.copy()
    env["GIT_SSH_COMMAND"] = "ssh -o ConnectTimeout=15"
    r = run("git -c http.version=HTTP/1.1 push origin main", env=env)
    if r.returncode != 0:
        print(f"[push_experiment] push 失败: {r.stderr[:200]}")
        return 1

    print(f"[push_experiment] 已提交并推送 {len(files)} 个实验文件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
