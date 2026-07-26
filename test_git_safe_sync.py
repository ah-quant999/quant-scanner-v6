#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_git_safe_sync.py — 验证 safe_pull() 永绝 git 合并冲突（绝不遗留 UU 未合并文件）。

安全隔离策略（绝不触碰主工作树，绝不丢失用户未提交改动）：
  - 全程在「临时 git worktree」中执行：git worktree add 出一个独立工作树
    gss_test_branch（基于 main HEAD）。所有 git 操作都 cwd=该 worktree。
  - 真实 main 工作树自始至终不被 read/write，因此用户的未提交改动绝不会被动到。
  - 用本地临时 bare 仓库作为 fake remote（无需联网）。
  - T3 冲突模拟使用「测试自建的 fixture 文件」，绝不碰任何生产源码，且每次全新创建，
    所以无论仓库当前状态如何，测试都可重复、幂等通过。

场景：
  T1 干净树拉取              -> 返回 True，无 UU 遗留
  T2 派生数据(data/)脏改动   -> 拉取后数据被还原为 HEAD 版，无 UU 遗留
  T3 源码同文件 stash-pop 冲突 -> 拉取后冲突被安全解决（取上游版），无 UU 遗留
"""
import os
import sys
import subprocess
import tempfile
import shutil

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORKSPACE)
import git_safe_sync as g

REMOTE_NAME = "gssremote"
TEST_BRANCH = "gss_test_branch"
FIXTURE = "gss_conflict_fixture.py"     # T3 自建 fixture（在 worktree 内创建）


def git(args, cwd, check=True):
    r = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr}")
    return r


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def find_line(lines, prefix):
    for i, l in enumerate(lines):
        if l.strip().startswith(prefix):
            return i
    return None


def main():
    tmp = tempfile.mkdtemp(prefix="gss_test_")
    wt = os.path.join(tmp, "wt")
    remote_dir = os.path.join(tmp, "remote.git")
    failures = []
    try:
        # 0) 清理可能残留的 worktree / 分支
        git(["worktree", "remove", wt, "--force"], cwd=WORKSPACE, check=False)
        git(["branch", "-D", TEST_BRANCH], cwd=WORKSPACE, check=False)

        # 1) 建隔离 worktree（真实 main 工作树完全不动）
        git(["worktree", "add", wt, "-b", TEST_BRANCH], cwd=WORKSPACE)

        # 2) 建 fake remote 并发布 main 作为上游
        git(["init", "--bare", remote_dir], cwd=tmp)
        git(["config", "receive.shallowUpdate", "true"], cwd=remote_dir)
        git(["remote", "add", REMOTE_NAME, remote_dir], cwd=wt)
        git(["push", REMOTE_NAME, "main"], cwd=wt)

        # ===== T1: 干净树拉取 =====
        ok = g.safe_pull(remote=REMOTE_NAME, branch="main", cwd=wt)
        uu = git(["diff", "--name-only", "--diff-filter=U"], cwd=wt).stdout.strip()
        if not ok:
            failures.append("T1: safe_pull 返回 False")
        if uu:
            failures.append(f"T1: 遗留未合并文件 {uu}")

        # ===== T2: 派生数据脏 -> 还原为 HEAD =====
        data_file = os.path.join(wt, "data", "gold_pool.json")
        before = read_file(data_file)
        with open(data_file, "a", encoding="utf-8") as f:
            f.write("\n// TEST DIRTY MARKER\n")
        ok = g.safe_pull(remote=REMOTE_NAME, branch="main", cwd=wt)
        after = read_file(data_file)
        uu = git(["diff", "--name-only", "--diff-filter=U"], cwd=wt).stdout.strip()
        if not (ok and after == before and not uu):
            failures.append(f"T2: 派生数据未还原或遗留 UU (ok={ok}, reverted={after == before}, uu={uu!r})")

        # ===== T3: 源码同文件 stash-pop 冲突 -> 安全解决 =====
        # 3.0 自建 fixture（干净初始内容），提交到 TEST_BRANCH 并推到 fake remote main
        fixture = os.path.join(wt, FIXTURE)
        write_file(fixture, "LINE_A = 1\nLINE_B = 2\nLINE_C = 3\n")
        git(["add", "-f", FIXTURE], cwd=wt)
        git(["commit", "-q", "-m", "t3: add fixture"], cwd=wt)
        git(["push", REMOTE_NAME, "main"], cwd=wt)

        # 3.1 在「独立分支」制造 REMOTE 改动并推到 fake remote main，
        #     让 TEST_BRANCH 停在 X、remote 前进到 X'（真正分叉 -> stash-pop 必冲突）
        tlines = read_file(fixture).splitlines()
        t = find_line(tlines, "LINE_B")
        if t is None:
            raise RuntimeError("fixture 中找不到 LINE_B")
        git(["checkout", "-q", "-b", "t3remote"], cwd=wt)
        tlines[t] = "LINE_B = 2  # REMOTE-CONFLICT-MARKER"
        write_file(fixture, "\n".join(tlines) + "\n")
        git(["add", "-f", FIXTURE], cwd=wt)
        git(["commit", "-q", "-m", "remote conflict edit"], cwd=wt)
        git(["push", REMOTE_NAME, "t3remote:main"], cwd=wt)
        git(["checkout", "-q", TEST_BRANCH], cwd=wt)
        git(["branch", "-D", "t3remote"], cwd=wt)
        git(["fetch", REMOTE_NAME], cwd=wt)   # 让 worktree 感知远程新提交

        # 3.2 本地也改同一行（未提交），制造 stash-pop 冲突
        slines = read_file(fixture).splitlines()
        slines[t] = "LINE_B = 2  # LOCAL-CONFLICT-MARKER"
        write_file(fixture, "\n".join(slines) + "\n")

        ok = g.safe_pull(remote=REMOTE_NAME, branch="main", cwd=wt)
        uu = git(["diff", "--name-only", "--diff-filter=U"], cwd=wt).stdout.strip()
        content = read_file(fixture)
        if uu:
            failures.append(f"T3: 遗留未合并文件 {uu}")
        if "REMOTE-CONFLICT-MARKER" not in content:
            failures.append("T3: 冲突未取上游版（缺 REMOTE 标记）")
        if "LOCAL-CONFLICT-MARKER" in content:
            failures.append("T3: 仍含本地冲突标记（未清理）")
        if not ok:
            failures.append("T3: safe_pull 返回 False（pull 应成功）")

    finally:
        # 清理 worktree（完全隔离，main 工作树不受影响）；顺手删 fake remote 与临时目录
        try:
            git(["worktree", "remove", wt, "--force"], cwd=WORKSPACE, check=False)
        except Exception:
            pass
        try:
            git(["branch", "-D", TEST_BRANCH], cwd=WORKSPACE, check=False)
        except Exception:
            pass
        try:
            git(["remote", "remove", REMOTE_NAME], cwd=WORKSPACE, check=False)
        except Exception:
            pass
        try:
            shutil.rmtree(tmp, ignore_errors=True)
        except Exception:
            pass

    if failures:
        print("❌ TEST FAILED:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("✅ ALL TESTS PASSED: safe_pull 永绝冲突（无 UU 遗留，main 工作树零触碰，未碰生产文件）")


if __name__ == "__main__":
    main()
