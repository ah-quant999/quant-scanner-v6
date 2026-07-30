#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v8_push.py — 阿狸咪专用：安全推送 v8 代码改动（防覆盖小九白天新版）

双机时间窗铁律（2026-07-30 拍板）：
- 小九 = 白天独家部署者（07:00~18:00），代码窗口外不推送。
- 阿狸咪 = 夜间/周末代码编辑者（工作日 18:00~次日 07:00，周末全天）。
- 关键保护：推送前必须 git pull --rebase origin/main，
  继承小九当日（<18:00）的改动，绝不用旧版覆盖新版。

用法：
    python v8/v8_push.py "本次改动说明"
或在 repo-temp 根目录：
    python v8/v8_push.py "说明"

行为：
1. 时间窗校验：工作日仅允许 18:00~07:00；周末(Sat/Sun)全天允许。
2. git fetch + git rebase origin/main（继承对方改动，解决分叉）。
3. git add -A + commit + push origin main（绝不 force）。
4. rebase 冲突 → 中止并提示手动解决，绝不静默覆盖。
"""
import subprocess, sys, os, datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(cmd, fatal=True):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=REPO, timeout=180)
    if r.returncode != 0 and fatal:
        print(f"❌ 命令失败: {cmd}\n{r.stderr or r.stdout}")
        sys.exit(1)
    return r.stdout.strip()

def in_push_window(now):
    """工作日 18:00~23:59 / 00:00~07:00 允许；周末(Sat=5,Sun=6)全天允许。"""
    wd = now.weekday()          # Mon=0 ... Sun=6
    h = now.hour
    if wd >= 5:                 # 周末：阿狸咪全天可改
        return True, "周末全天（阿狸咪窗口）"
    if h >= 18 or h < 7:        # 工作日夜间
        return True, f"工作日夜间 {h:02d}:xx（阿狸咪窗口）"
    return False, f"工作日白天 {h:02d}:xx（小九窗口，禁止推送代码）"

def main():
    now = datetime.datetime.now()
    allowed, reason = in_push_window(now)
    print(f"🕐 当前 {now.strftime('%Y-%m-%d %H:%M')} · {reason}")
    if not allowed:
        print("⛔ 不在阿狸咪代码推送窗口。小九白天独家部署，"
              "此时推送会覆盖其当日新版。请等到 18:00 后，或紧急时先与小九确认。")
        sys.exit(2)

    msg = sys.argv[1] if len(sys.argv) > 1 else "v8 代码更新（阿狸咪）"

    # 1) 关键：先 rebase 继承小九当日改动，绝不旧覆盖新
    print("📥 git fetch origin && git rebase origin/main ...")
    run("git fetch origin")
    try:
        run("git rebase origin/main")
    except SystemExit:
        print("⚠️ rebase 冲突！请手动解决冲突后 `git rebase --continue`，"
              "再重新运行本脚本。绝不 force push。")
        sys.exit(1)
    print("   ✅ 已继承小九当日最新代码")

    # 2) 提交并推送
    run("git add -A")
    st = run("git status --porcelain", fatal=False)
    if not st:
        print("✅ 无本地改动，无需推送")
        return
    run(f'git -c user.email="2814546@qq.com" -c user.name="ah-quant999" '
        f'commit -m "{msg}"')
    run("git push origin main")
    print("🚀 已安全推送（已继承小九当日改动，未覆盖其新版）")

if __name__ == "__main__":
    main()
