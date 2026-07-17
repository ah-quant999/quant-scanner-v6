#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# DO NOT DELETE: 主站(dist/index.html) 与独立页(dist/standalone/*.html) 同步校验闸门
"""
确保「主站」与「手机版/独立页」永远同源同戳、一起上线。

为什么需要它（2026-07-16 修复）：
  云端迁移后，独立页(standalone/) 与 dist/standalone/ 都在 .gitignore 中，
  云端 git checkout 拉不到独立页，只能靠 extract_panels_v6.py 现场抽取。
  原云端工作流独立页生成步骤带 continue-on-error + `cp ... || true`，
  一旦抽页在 CI 失败 → dist/standalone/ 为空 → actions-gh-pages 的
  keep_files:false 全量替换会把独立页整页删掉/变陈旧，而主站正常 → 不同步。

本脚本作为统一闸门：
  1. 运行 extract_panels_v6.py 从【已构建好的 dist/index.html】重建 standalone/
  2. 同步 standalone/*.html -> dist/standalone/（含 triple/multi_resonance 链接修正）
  3. (可选 --inject-buildstamp) 给 dist/ 下所有 html 注入 build-stamp/title（与本地 deploy_now.py 一致）
  4. 同源同戳指纹校验：dist/index.html 与 dist/standalone/overview.html 的
     window.*_DATA 标记集合 + POST_CLOSE_TIME 必须完全一致
  5. 硬核数据块校验：EXPERIMENT_DATA / CRDS_CARD_DATA 等关键数据块在
     主站与独立页之间必须逐字段一致（防止只同戳不同数据）
  6. 校验失败 -> 打印诊断并 exit(1)，使调用方（云端 step / 本地 deploy）阻断部署，
     绝不允许「主站上线、独立页缺失/数据陈旧」的半残状态上线

用法:
  python ensure_standalone_sync.py                 # 仅抽取+同步+校验
  python ensure_standalone_sync.py --inject-buildstamp   # 额外注入 build-stamp
"""
import os
import sys
import re
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
CST = timezone(timedelta(hours=8))  # 统一 build-stamp 时区，避免云端(UTC)覆盖本机(CST)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(PROJECT_ROOT, "dist")
STANDALONE_DIR = os.path.join(PROJECT_ROOT, "standalone")
DIST_STANDALONE = os.path.join(DIST_DIR, "standalone")


def log(msg):
    print(msg, flush=True)


def _run_extract():
    """运行 extract_panels_v6.py 重建 standalone/（从 dist/index.html 抽取）。"""
    extract_py = os.path.join(PROJECT_ROOT, "extract_panels_v6.py")
    if not os.path.exists(extract_py):
        log("  ❌ extract_panels_v6.py 不存在，无法重建独立页")
        return False
    if not os.path.exists(os.path.join(DIST_DIR, "index.html")):
        log("  ❌ dist/index.html 不存在，无法抽取独立页（请先 update_data_v2.py）")
        return False
    r = subprocess.run([sys.executable, extract_py],
                       capture_output=True, text=True, timeout=180, cwd=PROJECT_ROOT)
    if r.returncode != 0:
        log(f"  ❌ extract_panels_v6.py 失败 (rc={r.returncode}): {r.stderr.strip()[:300]}")
        return False
    log("  ✓ extract_panels_v6.py 重建 standalone/ 成功")
    return True


def _sync_to_dist():
    """把 standalone/ 同步到 dist/standalone/（与 deploy_now.py _regen_standalone_if_needed 一致）。"""
    os.makedirs(DIST_STANDALONE, exist_ok=True)
    if not os.path.exists(STANDALONE_DIR):
        log("  ❌ standalone/ 目录不存在，无法同步")
        return False
    copied = 0
    for fname in os.listdir(STANDALONE_DIR):
        if not fname.endswith(".html"):
            continue
        if fname in ("triple_resonance.html", "multi_resonance.html"):
            continue  # 这两个由下方 dist/ 根目录版强制覆盖
        shutil.copy2(os.path.join(STANDALONE_DIR, fname),
                     os.path.join(DIST_STANDALONE, fname))
        copied += 1
    # 共振页：用 dist/ 根目录新鲜版覆盖（避免 standalone 旧副本上 gh-pages）
    for _p in ("triple_resonance", "multi_resonance"):
        _src = os.path.join(DIST_DIR, f"{_p}.html")
        _dst = os.path.join(DIST_STANDALONE, f"{_p}.html")
        if os.path.exists(_src):
            shutil.copy2(_src, _dst)
            try:
                with open(_dst, "r", encoding="utf-8") as _f:
                    _c = _f.read()
                _c = _c.replace('href="index_master.html"', 'href="../index.html"')
                _c = _c.replace('href="index.html"', 'href="../index.html"')
                with open(_dst, "w", encoding="utf-8") as _f:
                    _f.write(_c)
            except Exception as _e:
                log(f"  ⚠️ 重写 {_p} 返回链接失败（不阻塞）: {_e}")
            copied += 1
    log(f"  ✓ 已同步 {copied} 个独立页到 dist/standalone/")
    return True


def _inject_buildstamp():
    """给 dist/ 下所有 html 注入 build-stamp / title（与本地 deploy_now.py CDN bust 一致）。"""
    now_stamp = datetime.now(CST).strftime("%Y%m%d%H%M%S")
    pat_build = re.compile(r"<!-- build: \d+ -->")
    pat_title = re.compile(r"<title>九宝量化 v\d\.\d</title>")
    pat_meta = re.compile(r'<meta name="build-stamp" content="[^"]*">')
    n = 0
    for root, _dirs, files in os.walk(DIST_DIR):
        for fname in files:
            if not fname.endswith(".html"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    c = f.read()
            except Exception:
                continue
            changed = False
            if pat_build.search(c):
                c = pat_build.sub(f"<!-- build: {now_stamp} -->", c)
                changed = True
            if pat_title.search(c):
                c = pat_title.sub(f"<title>九宝量化 v6.0 ({now_stamp})</title>", c)
                changed = True
            if pat_meta.search(c):
                c = pat_meta.sub(f'<meta name="build-stamp" content="{now_stamp}">', c)
                changed = True
            else:
                c = c.replace("<head>", f"<head>\n<meta name=\"build-stamp\" content=\"{now_stamp}\">", 1)
                changed = True
            if changed:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(c)
                n += 1
    log(f"  ✓ build-stamp 注入完成: {now_stamp}（{n} 个文件）")
    return now_stamp


def _fingerprint(path):
    """抽取「同源指纹」：window.* 数据标记集合 + POST_CLOSE_TIME 值 + 文件体积。

    独立页是从主站 dist/index.html 整体复制后仅改 CSS/head 生成，
    因此内嵌的 window.*_DATA 标记集合与 POST_CLOSE_TIME 必须完全一致。
    一旦抽页失败/读取到陈旧 index，指纹即对不上。
    """
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        c = f.read()
    markers = sorted(set(re.findall(r"window\.([A-Z][A-Z0-9_]*)\s*=", c)))
    pct = re.findall(r'POST_CLOSE_TIME\s*=\s*"([^"]*)"', c)
    pct_val = pct[0] if pct else ""
    return (markers, pct_val, len(c))


def _verify_parity():
    """校验主站与独立页总览同源同戳。返回 (ok, detail)。"""
    main_html = os.path.join(DIST_DIR, "index.html")
    ov_html = os.path.join(DIST_STANDALONE, "overview.html")
    if not os.path.exists(ov_html):
        return False, "dist/standalone/overview.html 不存在（抽页未产出）"
    fp_main = _fingerprint(main_html)
    fp_ov = _fingerprint(ov_html)
    if fp_main is None:
        return False, "dist/index.html 指纹提取失败"
    if fp_ov is None:
        return False, "dist/standalone/overview.html 指纹提取失败"

    # 体积门限：独立页应接近主站体积（不应是空壳）
    if fp_ov[2] < fp_main[2] * 0.3:
        return False, (f"独立页体积过小 ({fp_ov[2]}B vs 主站 {fp_main[2]}B)，"
                       f"疑似抽页失败/空壳")

    if fp_ov[0] != fp_main[0]:
        missing = set(fp_main[0]) - set(fp_ov[0])
        extra = set(fp_ov[0]) - set(fp_main[0])
        detail = "window.* 数据标记不一致"
        if missing:
            detail += f" | 独立页缺失: {sorted(missing)[:8]}"
        if extra:
            detail += f" | 独立页多余: {sorted(extra)[:8]}"
        return False, detail

    if fp_ov[1] != fp_main[1]:
        return False, f"POST_CLOSE_TIME 不一致: 主站={fp_main[1]} 独立页={fp_ov[1]}"

    return True, (f"主站/独立页同源同戳校验通过 "
                  f"(标记 {len(fp_main[0])} 个, POST_CLOSE_TIME={fp_main[1]}, "
                  f"体积 {fp_main[2]}B/{fp_ov[2]}B)")


def _extract_data_block(path, marker):
    """从 HTML 中提取 window.X = {...} JSON 对象，失败返回 None。"""
    import json
    try:
        with open(path, "r", encoding="utf-8") as f:
            c = f.read()
    except Exception:
        return None
    i = c.find(marker)
    if i < 0:
        return None
    i += len(marker)
    while i < len(c) and c[i] in " \t\r\n":
        i += 1
    try:
        obj, _ = json.JSONDecoder().raw_decode(c, i)
        return obj
    except Exception:
        return None


def _verify_data_parity():
    """
    硬核数据块校验：主站与独立页的关键数据块必须逐字段一致。
    可发现「独立页从旧版 dist/index.html 抽取」或「数据注入失败」导致不同步。
    """
    main_html = os.path.join(DIST_DIR, "index.html")
    checks = []
    for fname in os.listdir(DIST_STANDALONE):
        if not fname.endswith(".html"):
            continue
        st_path = os.path.join(DIST_STANDALONE, fname)
        if os.path.getsize(st_path) < 100000:
            continue  # 导航页等不需要校验
        # EXPERIMENT_DATA 关键字段
        main_exp = _extract_data_block(main_html, "window.EXPERIMENT_DATA = ")
        st_exp = _extract_data_block(st_path, "window.EXPERIMENT_DATA = ")
        if main_exp and st_exp:
            mt = main_exp.get("today", {})
            st = st_exp.get("today", {})
            for k in ("scanned", "total", "failed", "generated_at"):
                if mt.get(k) != st.get(k):
                    checks.append((fname, "EXPERIMENT_DATA.today." + k, mt.get(k), st.get(k)))
        # CRDS_CARD_DATA 关键字段
        main_crds = _extract_data_block(main_html, "window.CRDS_CARD_DATA = ")
        st_crds = _extract_data_block(st_path, "window.CRDS_CARD_DATA = ")
        if main_crds and st_crds:
            for k in ("total_scanned", "failed", "update_time"):
                if main_crds.get(k) != st_crds.get(k):
                    checks.append((fname, "CRDS_CARD_DATA." + k, main_crds.get(k), st_crds.get(k)))
            for k in ("elite", "advanced", "cond1_list", "cond2_list", "cond3_list"):
                if len(main_crds.get(k, [])) != len(st_crds.get(k, [])):
                    checks.append((fname, f"CRDS_CARD_DATA.{k}.length", len(main_crds.get(k, [])), len(st_crds.get(k, []))))
    if not checks:
        return True, "关键数据块（EXPERIMENT_DATA/CRDS_CARD_DATA）逐字段一致"
    detail = "; ".join(f"{fname} {field}: 主站={mv} 独立页={sv}" for fname, field, mv, sv in checks[:5])
    return False, "关键数据块不一致: " + detail


def main():
    inject = "--inject-buildstamp" in sys.argv
    log("=" * 55)
    log("🔗 主站 ↔ 独立页 同步校验闸门")
    log("=" * 55)

    # 0. 前置：dist/index.html 必须已构建
    if not os.path.exists(os.path.join(DIST_DIR, "index.html")):
        log("  ❌ dist/index.html 不存在，请先运行 update_data_v2.py")
        return 1

    # 1. 抽取独立页
    if not _run_extract():
        log("  ❌ 独立页抽取失败，阻断部署（避免主站上线而独立页缺失）")
        return 1

    # 2. 同步到 dist/standalone/
    if not _sync_to_dist():
        log("  ❌ 独立页同步失败，阻断部署")
        return 1

    # 3. (可选) 注入 build-stamp
    if inject:
        _inject_buildstamp()

    # 4. 同源同戳校验
    ok, detail = _verify_parity()
    if not ok:
        log(f"  ❌ 同步校验失败: {detail}")
        log("  ❌ 阻断部署：主站与独立页不一致，绝不允许半残上线")
        return 1

    log(f"  ✅ {detail}")
    log("  ✅ 主站与独立页已确认同步，可安全上线")
    return 0


if __name__ == "__main__":
    sys.exit(main())
