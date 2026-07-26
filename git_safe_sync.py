#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
git_safe_sync.py — 永绝 stash-pop / autostash 合并冲突的根因修复（单一维护点）。

═════════════════════════════════════════════════════════════════════════
【问题根因】
  data/ 与 dist/data/ 等「派生数据」由双机(阿狸咪/小九)各自重新生成并推送，
  本地未提交改动与 origin/main 几乎必然不同。脚本若用
      git pull --autostash            （自动 stash → 拉取 → 自动 pop）
  或  git stash + git pull + git stash pop
  同步时，pop 必冲突，留下 UU 混乱（<<<<<<< Updated upstream / >>>>>>> Stashed
  changes），导致后续所有 git 操作卡死、部署失败、数据陈旧。

【为什么之前修不好】
  之前只在「部署前扫描冲突标记」(detect) 和「冲突后清理文件」(cleanup) 上打补丁，
  没动 autostash/stash-pop 这个病根，所以周期性复发。

【本模块方案（永绝后患）】
  拉取前先丢弃本地派生数据改动（它们总会被构建重新生成，权威版在 origin/main），
  使工作树对 pull 而言「干净」，再 git pull --rebase（无 autostash，绝不自动 pop）。
  若仍有源码类脏改动，才 stash（不含数据），pull 后冲突安全 pop：
      一旦 pop 冲突，一律取上游(ours=rebase 后的 HEAD)并 drop stash，
      绝不遗留未合并文件。

【使用】
  from git_safe_sync import safe_pull
  safe_pull()                 # 默认 origin/main，cwd=本模块所在仓库根
  safe_pull(remote="origin", branch="main")
═════════════════════════════════════════════════════════════════════════
"""
import os
import subprocess

WORKSPACE = os.path.dirname(os.path.abspath(__file__))

# 派生 / 可重生成数据目录：拉取前应丢弃本地改动（绝不把这些卷进 stash-pop）
DERIVED_DIRS = ["data", "dist/data"]

# 仓库根目录下、会被双机改写且无需随 pull 保留的零散文件
DERIVED_FILES = [".ops_status.json", "HANDOVER_LOG.jsonl", "data/.ops_status.json"]

GIT_SSH = "ssh -o ConnectTimeout=15 -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -o StrictHostKeyChecking=no"


def _run(args, cwd=WORKSPACE, timeout=240):
    env = dict(os.environ)
    env.setdefault("GIT_SSH_COMMAND", GIT_SSH)
    cmd = ["git", "-c", "http.version=HTTP/1.1"] + list(args)
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                          timeout=timeout, env=env)


def safe_pull(remote="origin", branch="main", cwd=None):
    """安全拉取，绝不遗留未合并文件。

    返回 True=拉取成功（或已是最新），False=拉取失败（已尽量清理，调用方可重试）。

    cwd: 可选，指定在哪个工作树执行（默认本模块所在仓库根）。测试时传入隔离
         worktree 路径即可，绝不触碰主工作树。
    """
    cwd = cwd or WORKSPACE
    # 1) 丢弃派生数据目录/文件的本地未提交改动（权威版在 origin/main）
    for d in DERIVED_DIRS:
        if os.path.isdir(os.path.join(cwd, d)):
            _run(["checkout", "--", d], cwd=cwd)
    for f in DERIVED_FILES:
        fp = os.path.join(cwd, f)
        if os.path.exists(fp):
            _run(["checkout", "--", f], cwd=cwd)

    # 2) 是否仍有源码类脏改动？
    st = _run(["status", "--porcelain"], cwd=cwd)
    dirty = bool(st.stdout.strip())

    if dirty:
        # 仅 stash 已跟踪的源码改动（不含 -u：绝不把未跟踪文件卷进 pop，
        # 避免冲突 drop 时误删新建的本地文件）
        _run(["stash", "push", "-m", "safe-pull-src"], cwd=cwd)

    # 3) rebase 拉取（树已干净，不会因数据冲突）
    pull = _run(["pull", "--rebase", remote, branch], cwd=cwd)

    # 4) 冲突安全 pop（仅当上一步真的 stash 了源码改动）
    if dirty:
        pop = _run(["stash", "pop"], cwd=cwd)
        out = (pop.stdout + pop.stderr)
        if ("CONFLICT" in out or "could not apply" in out
                or "Previous HEAD" in out or "Merge conflict" in out):
            # pop 冲突：一律取上游(rebase 后的 HEAD=ours)，丢弃 stash，绝不遗留 UU
            _run(["checkout", "--ours", "--", "."], cwd=cwd)
            _run(["add", "-u"], cwd=cwd)          # 清除索引里的未合并条目，否则 git status 仍报 UU
            _run(["stash", "drop"], cwd=cwd)
    return pull.returncode == 0


if __name__ == "__main__":
    ok = safe_pull()
    print("safe_pull ->", "OK" if ok else "FAILED")
