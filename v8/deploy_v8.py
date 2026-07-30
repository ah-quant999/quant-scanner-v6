#!/usr/bin/env python3
"""v8 部署脚本 — 推 index.html 到 quant-scanner-v8 的 main 分支（独立仓库，不依赖 v6）

注意：quant-scanner-v8 只有 main 分支，GitHub Pages 直接从 main 出，
因此部署目标就是 main（不是 gh-pages）。
"""

import subprocess, sys, os, shutil, tempfile, datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V8_SRC = os.path.join(REPO, "v8", "dist", "index.html")
GH_PAGES_URL = "git@github.com:ah-quant999/quant-scanner-v8.git"

def log(msg):
    print(f"  {msg}")

def run(cmd, cwd=None, fatal=False):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, timeout=180)
    if r.returncode != 0:
        err = (r.stderr or r.stdout).strip()
        log(f"⚠️  {cmd} 失败: {err}")
        if fatal:
            raise RuntimeError(f"命令失败 (exit={r.returncode}): {cmd}\n{err}")
    return r.stdout.strip()

def deploy():
    # Iron rule: always rebase latest template before building+deploying
    # 关键双机保护：小九部署前先 git pull --rebase，继承阿狸咪夜间推送的新版代码，
    # 绝不用本地旧版覆盖她 18:00~07:00 的改动（满足「明早7点前阿狸咪新版不被小九旧版覆盖」）。
    log("📥 Pulling latest from origin/main (阿狸咪's code changes, --rebase)...")
    try:
        run("git fetch origin", cwd=REPO)
        rb = run("git rebase origin/main", cwd=REPO)
        if rb:
            log(f"   Rebased: {rb[:80]}")
        else:
            log("   Already up to date (no new code changes)")
    except RuntimeError as e:
        log(f"   ⚠️ rebase 失败（可能本地有未提交改动），使用本地版本继续: {e}")

    tmp = tempfile.mkdtemp(prefix="v8deploy_")
    try:
        # 全量克隆：浅克隆(--depth=1)曾导致远端 commit_refs 推送被拒
        log("📥 克隆 main 分支（全量）...")
        run(f"git clone {GH_PAGES_URL} .", cwd=tmp, fatal=True)

        # 拉取远端最新并变基，避免双机并发部署造成 non-fast-forward 冲突
        try:
            run("git fetch origin", cwd=tmp, fatal=True)
            run("git rebase origin/main", cwd=tmp, fatal=True)
        except RuntimeError as e:
            log(f"   ⚠️ 变基失败，继续（后续推送若冲突会报错）: {e}")

        log(f"📄 复制 index.html...")
        shutil.copy2(V8_SRC, os.path.join(tmp, "index.html"))

        run("git add -A", cwd=tmp, fatal=True)
        st = run("git status --porcelain", cwd=tmp)
        if not st:
            log("✅ 无变化，跳过部署")
            return 0

        run('git config user.email "2814546@qq.com"', cwd=tmp, fatal=True)
        run('git config user.name "ah-quant999"', cwd=tmp, fatal=True)
        run(f'git commit -m "deploy {datetime.datetime.now():%Y-%m-%d_%H:%M}"', cwd=tmp, fatal=True)
        log("🚀 推送到 main...")
        run(f"git push origin main", cwd=tmp, fatal=True)
        log("✅ v8 部署成功！")
        log(f"   🌐 https://ah-quant999.github.io/quant-scanner-v8/")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == '__main__':
    try:
        deploy()
    except RuntimeError as e:
        log(f"❌ 部署失败: {e}")
        sys.exit(1)
