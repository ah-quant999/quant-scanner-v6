#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿狸咪 v8 兜底部署器（选股四模块：三重共识 / 驾驶舱 / 全站精选 / 逆势龙头）

职责（双机分时铁律）：
  主责机 小九 每个交易日 15:30 已完成 v8 盘后生成+部署（推到 quant-scanner-v8 独立仓库 main）。
  阿狸咪 在晚间 18:30 / 20:00 兜底：检查 v8 今日是否已被小九部署；
    - 已部署 -> 直接退出，绝不重复部署（避免双机争抢同一 gh-pages）。
    - 未部署 -> 尽力重跑生成器链（单步失败保留现有 json，不中断整体）+ update_v8 + deploy_v8。

数据安全铁律：
  - calc_crds 需联网(mootdx)；若失败，保留现有 data/crds_result.json，不报错中断。
  - 各生成器失败仅告警并保留现有产物，整体部署仍照常进行（至少保证站点在线、显示上次真实数据）。
  - 与 update_data_v2 的 reset --hard 不同：此处只读 data/ 生成产物，不触碰仓库重置。

用法（自动化 prompt 只需一行）：
  python v8/alimi_backup_deploy.py
工作目录：E:/workspace/stock-scanner/repo-temp
"""
import subprocess, os, sys, shutil, tempfile, datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V8 = os.path.join(REPO, "v8")
GH_PAGES_URL = "git@github.com:ah-quant999/quant-scanner-v8.git"
HEARTBEAT = os.path.join(REPO, "_heartbeat.log")

# 生成器链（相对 REPO 的路径, 中文描述）；顺序即执行顺序
GEN_STEPS = [
    ("calc_crds.py",                    "CRDS 逆势龙头(联网失败保留旧值)"),
    ("generate_top10.py",               "TOP10 评分"),
    ("gen_cockpit_tier_recommend.py",   "驾驶舱分层推荐"),
    ("gen_triple_consensus.py",         "三重共识"),
    ("gen_triple_track.py",             "三重跟踪"),
    ("update_triple_resonance_history.py", "三重共振历史"),
]

def run(cmd, cwd=None, allow_fail=True, timeout=300):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           cwd=cwd, timeout=timeout)
        if r.returncode != 0 and not allow_fail:
            print(f"  ⚠️ {cmd}\n{r.stderr.strip()[:600]}")
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def deployed_today():
    """克隆 v8 远程(main)，取最近一次提交日期，判断是否 == 今天。"""
    tmp = tempfile.mkdtemp(prefix="v8chk_")
    try:
        code, _, err = run(f"git clone --depth=1 {GH_PAGES_URL} .", cwd=tmp, timeout=120)
        if code != 0:
            print(f"  ⚠️ 无法访问 v8 远程（{err[:200]}）-> 视为未部署，启动兜底")
            return False
        code, out, _ = run("git log -1 --format=%cd --date=short", cwd=tmp)
        last = out.strip()
        today = datetime.date.today().isoformat()
        print(f"  v8 远程最后部署日期: {last}  |  今日: {today}")
        return last == today
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def gen(step):
    path, desc = step
    full = os.path.join(REPO, path)
    if not os.path.exists(full):
        print(f"  ⏭️ 缺失 {path}，跳过")
        return
    print(f"  🔄 {desc} ...")
    code, out, err = run(f'python "{full}"', cwd=REPO)
    if code != 0:
        print(f"  ⚠️ {desc} 失败（保留现有数据继续）: {err[:240]}")
    else:
        print(f"  ✅ {desc} 完成")

def stamp(msg):
    line = f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n"
    try:
        with open(HEARTBEAT, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
    print(line.rstrip())

def main():
    print("=== 阿狸咪 v8 兜底部署器 ===")
    if deployed_today():
        stamp("v8 今日已由小九部署，阿狸咪兜底跳过")
        return
    print("⏰ 今日 v8 未部署，启动兜底生成 + 部署 ...")
    for s in GEN_STEPS:
        gen(s)
    print("  🔨 update_v8.py ...")
    run(f'python "{os.path.join(V8, "update_v8.py")}"', cwd=REPO, allow_fail=False)
    print("  🚀 deploy_v8.py ...")
    run(f'python "{os.path.join(V8, "deploy_v8.py")}"', cwd=REPO, allow_fail=False)
    stamp("v8 阿狸咪兜底部署完成")

if __name__ == "__main__":
    main()
