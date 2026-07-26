#!/usr/bin/env python3
"""
新鲜度闸门：对比本地数据 vs gh-pages 当前数据
防止「云端用旧数据构建 → 覆盖 gh-pages 上的新鲜数据」

用法（GitHub Actions）：
  python check_freshness_vs_ghpages.py
  退出码 0 = 放行 | 1 = 阻断

返回 SKIP_DEPLOY 环境变量到 $GITHUB_ENV（调用方 workflow 负责 echo）
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone


def load_update_time(file_path: str, keys: list) -> str | None:
    """从 JSON 文件提取第一个存在的 key 的值"""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in keys:
            val = data.get(k)
            if val:
                return str(val)
        return None
    except (json.JSONDecodeError, OSError):
        return None


def fetch_gh_pages_file(file_path: str) -> str | None:
    """从 gh-pages 分支提取文件内容"""
    try:
        result = subprocess.run(
            ["git", "show", f"origin/gh-pages:{file_path}"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except (subprocess.TimeoutExpired, OSError):
        return None


def parse_time(value: str) -> datetime | None:
    """解析时间字符串为 datetime（兼容 ISO 8601 和 %Y-%m-%d %H:%M:%S）"""
    for fmt in [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
    ]:
        try:
            dt = datetime.strptime(value.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def main():
    print("🛡️ 新鲜度闸门：对比本地 vs gh-pages 数据时间")

    # === 1. 读取本地数据 ===
    local_times: dict[str, datetime | None] = {}
    for name, path, keys in [
        ("gold_pool", "data/gold_pool.json", ["update_time", "last_update"]),
        ("macro_data", "data/macro_data.json", ["update_time"]),
    ]:
        raw = load_update_time(path, keys)
        if raw:
            dt = parse_time(raw)
            local_times[name] = dt
            print(f"  本地 {name}: {raw}  → parsed={dt}")
        else:
            local_times[name] = None
            print(f"  本地 {name}: 无法读取")

    if not any(local_times.values()):
        print("::warning::无法读取任何本地数据文件时间戳，放行部署")
        return 0

    # === 2. 获取 gh-pages 数据 ===
    print("  正在获取 gh-pages 分支数据...")
    fetch_ok = subprocess.run(
        ["git", "fetch", "origin", "gh-pages", "--depth=1"],
        capture_output=True, timeout=30,
    ).returncode == 0

    if not fetch_ok:
        print("::warning::无法获取 gh-pages 分支，放行部署")
        return 0

    gh_times: dict[str, datetime | None] = {}
    for name, path, keys in [
        ("gold_pool", "data/gold_pool.json", ["update_time", "last_update"]),
        ("macro_data", "data/macro_data.json", ["update_time"]),
    ]:
        content = fetch_gh_pages_file(path)
        if content:
            try:
                data = json.loads(content)
                for k in keys:
                    val = data.get(k)
                    if val:
                        dt = parse_time(str(val))
                        gh_times[name] = dt
                        print(f"  gh-pages {name}: {val}  → parsed={dt}")
                        break
                else:
                    gh_times[name] = None
                    print(f"  gh-pages {name}: 无匹配字段")
            except json.JSONDecodeError:
                gh_times[name] = None
                print(f"  gh-pages {name}: JSON 解析失败")
        else:
            gh_times[name] = None
            print(f"  gh-pages {name}: 无法读取")

    # === 3. 对比时间 ===
    threshold = 3600  # 1 小时（秒）
    block_reasons: list[str] = []

    for name in ["gold_pool", "macro_data"]:
        local_dt = local_times.get(name)
        gh_dt = gh_times.get(name)
        if local_dt and gh_dt:
            diff = (gh_dt - local_dt).total_seconds()
            if diff > threshold:
                msg = (
                    f"{name}: 本地({local_dt}) 比 gh-pages({gh_dt}) "
                    f"旧了 {diff / 60:.0f} 分钟！"
                )
                print(f"::error::{msg}")
                block_reasons.append(msg)
            elif diff > 0:
                print(
                    f"  ⚠️ {name}: 本地比 gh-pages 旧 {diff / 60:.0f} 分钟，"
                    "可接受范围内"
                )
            else:
                print(f"  ✅ {name}: 本地({local_dt}) ≥ gh-pages({gh_dt})")
        else:
            print(
                f"  ⚠️ {name}: 无法对比"
                f"（本地={'有' if local_dt else '无'}, "
                f"gh-pages={'有' if gh_dt else '无'}），放行"
            )

    # === 4. 结果 ===
    if block_reasons:
        print("::error::🚫 新鲜度闸门阻断：本地数据显著旧于 gh-pages，跳过此次部署")
        # 如果 GITHUB_ENV 存在（在 GitHub Actions 中运行），写环境变量
        gh_env = os.environ.get("GITHUB_ENV")
        if gh_env:
            with open(gh_env, "a") as f:
                f.write("SKIP_DEPLOY=true\n")
        print("设置为 SKIP_DEPLOY=true，部署步骤将跳过")
        return 1

    print("🟢 新鲜度闸门通过，放行部署")
    return 0


if __name__ == "__main__":
    sys.exit(main())
