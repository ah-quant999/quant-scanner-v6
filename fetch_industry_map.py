#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_industry_map.py — 重建「行业板块 + 概念」映射 (data/industry_map.json)

设计原则（用户铁律）：
  1. 重要数据接口必须有备用源：行业/概念各有多源回退链，本源失败自动切下一个。
  2. 实在都没有了才汇报（打印告警），绝不过问、绝不阻塞。
  3. 别再丢数据：每次只填充「缺失/为空」的字段，旧值一律保留；
     源全挂时沿用上次成功结果，不覆盖成空。

【性能关键修复 2026-07-08】
  - 只查候选池+金股池并集（~384 只），不跑全宇宙 5200 只（用户铁律：
    股池=成交额前100×3板+港股前50+研报，行业概念只需覆盖这些）。
  - BaoStock 每只查询 ~2-4 秒，384 只串行 ≈ 20-25 分钟。支持 --shard/--of 分片并行加速。
  - 概念源（东财 datacenter）现处软封禁（HTTP 200 但 data=None）。启动探测一次，
    若不可用则整体跳过逐股概念请求（之前会逐股浪费请求），仅保留缓存并汇报。
  - 增量写盘：每 100 只写一次分片文件，崩溃可续跑（重跑只补缺失）。

数据源回退链：
  【行业 industry】
    S1  BaoStock query_stock_industry  (主源, 证监会分类)
    S2  akshare stock_individual_info_em (东财个股信息, 封禁时快速失败)
    S3  akshare stock_individual_info_ths (同花顺, 备选)
  【概念 concepts】
    C1  东财 datacenter-web RPT_THEME_CONCEPT (探测可用才逐股请求)

用法：
  python fetch_industry_map.py --shard 1 --of 6     # 跑第1分片(共6)
  python fetch_industry_map.py --merge              # 合并所有分片 -> industry_map.json
  python fetch_industry_map.py                       # 单进程全量(默认--shards 1, 最稳, ~20-25分钟)
  python fetch_industry_map.py --shards 1           # 显式单进程(推荐, 17:30任务使用)
"""
import os, sys, time, json, re, argparse, glob

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "data")
STOCK_NAMES = os.path.join(DATA_DIR, "stock_names.json")
OUT_FILE = os.path.join(DATA_DIR, "industry_map.json")
SHARD_TMPL = os.path.join(DATA_DIR, "industry_map_shard_{}.json")

_bs_logged = False
def _bs_login(max_retry=3):
    """登录 BaoStock，失败指数退避重试（默认 3 次: 1s/2s/4s）。

    返回 True/False。调用方应保证同一进程内登录串行（避免并发限流）。
    本环境 BaoStock 认证偶发失败，重试可显著拉高成功率。
    """
    global _bs_logged
    if _bs_logged:
        return True
    import baostock as bs
    last_msg = ""
    for attempt in range(1, max_retry + 1):
        try:
            lg = bs.login()
            ec = getattr(lg, "error_code", "1")
            if ec == "0":
                _bs_logged = True
                if attempt > 1:
                    print("  [OK] BaoStock 登录成功(第%d次重试)" % attempt)
                return True
            last_msg = getattr(lg, "error_msg", "") or ""
        except Exception as e:
            last_msg = str(e)
        print("  [WARN] BaoStock 登录失败(第%d/%d次): %s"
              % (attempt, max_retry, last_msg))
        if attempt < max_retry:
            time.sleep(2 ** (attempt - 1))  # 1s, 2s, 4s 退避
    # 全部失败：强制重置，下次再试时有机会成功
    _bs_logged = False
    return False

def _bs_logout():
    global _bs_logged
    try:
        import baostock as bs
        bs.logout()
    except Exception:
        pass
    _bs_logged = False

def _strip_industry_code(s):
    if not s:
        return ""
    m = re.match(r'^[A-Za-z]{1,2}\d+\s*(.*)$', s.strip())
    if m and m.group(1):
        return m.group(1).strip()
    return s.strip()

def _clean_code(code):
    """清洗候选池/gold_pool 的 code 格式: sh_600030 -> 600030, sz_300750 -> 300750"""
    if not code:
        return ""
    # 去掉 sh_/sz_/hk_ 等前缀
    m = re.match(r'^(?:sh|sz|hk|bj)?[_\-]?(\d{5,6})$', str(code).strip())
    if m:
        return m.group(1)
    # 兜底：纯数字直接返回
    if code.isdigit():
        return code
    return code

# ─────────────────────────── 行业源 ───────────────────────────
def industry_from_baostock(code, retry=2):
    """S1: BaoStock 证监会行业分类（含会话失效自愈 + 重试兜底）。

    - 登录失败由 _bs_login 内部退避重试兜底；
    - 若查询返回非 '0' 且含 "you don't login." 之类会话失效提示，
      强制 _bs_logout() 让下一轮重新登录，避免整片静默失败；
    - 仍失败则返回 None，由 fetch_industry 回退链切下一源。
    """
    code = _clean_code(code)
    for attempt in range(retry + 1):
        if not _bs_login():
            # 登录彻底不可达：放弃本股，保留旧值
            return None
        try:
            import baostock as bs
            prefix = "sh" if code.startswith("6") else "sz"
            rs = bs.query_stock_industry(code="%s.%s" % (prefix, code))
            if rs.error_code == '0' and rs.next():
                row = rs.get_row_data()
                if len(row) >= 4 and row[3]:
                    ind = _strip_industry_code(row[3])
                    if ind:
                        return ind
            # 会话失效检测（如 "you don't login."）：强制重置登录态
            if rs.error_code != '0':
                msg = getattr(rs, "error_msg", "") or ""
                if "login" in msg.lower() or "you don" in msg.lower():
                    _bs_logout()
            return None
        except Exception:
            _bs_logout()  # socket 异常 -> 重置登录后重试
    return None

def industry_from_eastmoney(code):
    try:
        import akshare as ak
        info = ak.stock_individual_info_em(symbol=code)
        if isinstance(info, dict):
            for k in ('行业', 'industry'):
                if k in info and info[k]:
                    return str(info[k]).strip()
    except Exception:
        pass
    return None

def industry_from_ths(code):
    try:
        import akshare as ak
        info = ak.stock_individual_info_ths(symbol=code)
        if isinstance(info, dict):
            for k in ('行业', 'industry', '所属行业'):
                if k in info and info[k]:
                    return str(info[k]).strip()
    except Exception:
        pass
    return None

def fetch_industry(code):
    for fn in (industry_from_baostock, industry_from_eastmoney, industry_from_ths):
        try:
            r = fn(code)
            if r:
                return r
        except Exception:
            continue
    return None

# ─────────────────────────── 概念源 ───────────────────────────
_eastmoney_concept_ok = None
def probe_eastmoney_concept():
    """启动探测一次，判断东财概念源是否可用（避免逐股浪费请求）"""
    global _eastmoney_concept_ok
    if _eastmoney_concept_ok is not None:
        return _eastmoney_concept_ok
    try:
        import requests
        url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
        params = {"reportName": "RPT_THEME_CONCEPT", "columns": "SECURITY_CODE,THEME_NAME",
                  "filter": "(SECURITY_CODE=='600000')", "pageNumber": 1, "pageSize": 5}
        r = requests.get(url, params=params, timeout=6)
        d = r.json()
        _eastmoney_concept_ok = bool((d.get("data") or {}).get("data"))
    except Exception:
        _eastmoney_concept_ok = False
    return _eastmoney_concept_ok

def concepts_from_eastmoney_datacenter(code):
    import requests
    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    params = {"reportName": "RPT_THEME_CONCEPT", "columns": "SECURITY_CODE,THEME_NAME",
              "filter": "(SECURITY_CODE=='%s')" % code, "pageNumber": 1, "pageSize": 100}
    r = requests.get(url, params=params, timeout=8)
    d = r.json()
    out = []
    if d.get("data") and d["data"].get("data"):
        for it in d["data"]["data"]:
            nm = it.get("THEME_NAME", "")
            if nm:
                out.append(nm)
    return out

def fetch_concepts(code):
    try:
        return concepts_from_eastmoney_datacenter(code)
    except Exception:
        return []

# ─────────────────────────── 分片运行 ───────────────────────────
_FULL_UNIVERSE = False  # 由 --full-universe 设置
def _build_universe():
    """构建待查股票列表：候选池+金股池并集（~384只），不跑全宇宙5200只。
    若 _FULL_UNIVERSE=True 则强制全量（读 stock_names.json）。"""
    _fu = globals().get("_FULL_UNIVERSE", False)
    pool_codes = set()
    if not _fu:
        for fname in ("candidate_pool.json", "gold_pool.json"):
            p = os.path.join(DATA_DIR, fname)
            if os.path.exists(p):
                try:
                    d = json.load(open(p, "r", encoding="utf-8"))
                    pool_codes.update(d.get("stocks", {}).keys())
                except Exception:
                    pass
    if not pool_codes:
        # 回退或全量模式：读 stock_names 全宇宙
        if not os.path.exists(STOCK_NAMES):
            print("[ERROR] 找不到 stock_names.json 且无 candidate_pool/gold_pool")
            sys.exit(1)
        with open(STOCK_NAMES, "r", encoding="utf-8") as f:
            names = json.load(f)
        pool_codes = {s.get("code", "") for s in names
                      if s.get("full_code", "").startswith(("sh", "sz")) and s.get("code")}
    # 过滤掉港股前缀(hk_)和空码 — BaoStock 只支持 A 股
    pool_codes = {c for c in pool_codes if c and not c.startswith("hk_")}
    return sorted(pool_codes)


def run_shard(idx, of):
    t0 = time.time()
    universe = _build_universe()
    my = universe[idx - 1::of]
    print("[分片 %d/%d] 待查 %d 只, 本片 %d 只" % (idx, of, len(universe), len(my)))

    # 预登录 BaoStock（含重试兜底），提前暴露登录问题
    if not _bs_login():
        print("  [ERROR] BaoStock 登录失败，本分片行业数据将沿用缓存/标记缺失")
    else:
        print("  [OK] BaoStock 已登录")

    # 概念源探测（一次）
    concept_ok = probe_eastmoney_concept()
    print("  东财概念源可用: %s" % concept_ok)

    # 分片缓存（续跑）
    shard_file = SHARD_TMPL.format(idx)
    cache = {}
    if os.path.exists(shard_file):
        try:
            cache = json.load(open(shard_file, "r", encoding="utf-8")).get("stocks", {})
            print("  分片缓存: %d 只" % len(cache))
        except Exception:
            cache = {}

    out = {}
    done = 0
    ind_got = 0
    con_got = 0
    for code in my:
        rec = dict(cache.get(code, {}))
        if not rec.get("industry"):
            ind = fetch_industry(code)
            if ind:
                rec["industry"] = ind
        if not rec.get("concepts") and concept_ok:
            cons = fetch_concepts(code)
            if cons:
                rec["concepts"] = cons
        if rec.get("industry") or rec.get("concepts"):
            out[code] = rec
            if rec.get("industry"):
                ind_got += 1
            if rec.get("concepts"):
                con_got += 1
        done += 1
        if done % 100 == 0:
            _write_shard(shard_file, out, idx, of)
            print("  [分片%d] 进度 %d/%d, 行业 %d, 概念 %d, 耗时 %.0fs"
                  % (idx, done, len(my), ind_got, con_got, time.time() - t0))
    _write_shard(shard_file, out, idx, of)
    _bs_logout()
    print("=== 分片 %d 完成 === 行业 %d, 概念 %d, 耗时 %.1fs -> %s"
          % (idx, ind_got, con_got, time.time() - t0, shard_file))

def _write_shard(shard_file, out, idx, of):
    tmp = {"shard": idx, "of": of, "update_time": time.strftime("%Y-%m-%d %H:%M"),
           "count": len(out), "stocks": out}
    with open(shard_file, "w", encoding="utf-8") as f:
        json.dump(tmp, f, ensure_ascii=False, indent=1)

# ─────────────────────────── 合并 ───────────────────────────
def merge():
    t0 = time.time()
    merged = {}
    # 已有最终文件作为底层缓存
    if os.path.exists(OUT_FILE):
        try:
            merged = json.load(open(OUT_FILE, "r", encoding="utf-8")).get("stocks", {})
        except Exception:
            merged = {}
    shards = sorted(glob.glob(SHARD_TMPL.format("*")))
    print("发现分片文件: %d 个" % len(shards))
    for sf in shards:
        try:
            d = json.load(open(sf, "r", encoding="utf-8"))
        except Exception:
            continue
        for code, rec in d.get("stocks", {}).items():
            old = merged.get(code, {})
            new = dict(old)
            if rec.get("industry"):
                new["industry"] = rec["industry"]
            if rec.get("concepts"):
                new["concepts"] = rec["concepts"]
            if new:
                merged[code] = new
    # 汇总
    total_ind = sum(1 for v in merged.values() if v.get("industry"))
    total_con = sum(1 for v in merged.values() if v.get("concepts"))
    sectors = set()
    assoc = 0
    for v in merged.values():
        if v.get("industry"):
            sectors.add(v["industry"]); assoc += 1
        for c in v.get("concepts", []):
            sectors.add(c); assoc += 1
    # ── 防覆盖：强制从 concept_map.json 回填 concepts ──
    # 东财 datacenter 概念源常软封禁，重建时 concept_ok=False 不会补概念，
    # 仅靠 base 保留易被稀释。concept_map.json 是独立持久化真源，每次重建后
    # 强制回填，确保概念"覆盖不掉"。
    _cm_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "data", "concept_map.json")
    if os.path.exists(_cm_path):
        try:
            _cm = json.load(open(_cm_path, "r", encoding="utf-8")).get("map", {})
            _bf = 0
            for _code, _rec in merged.items():
                _c = _cm.get(_code)
                if isinstance(_c, list) and _c:
                    if not _rec.get("concepts"):
                        _rec["concepts"] = _c
                        _bf += 1
                    else:
                        _ex = set(_rec["concepts"])
                        _add = [x for x in _c if x not in _ex]
                        if _add:
                            _rec["concepts"] = _rec["concepts"] + _add
                            _bf += 1
            if _bf:
                print("  [防覆盖] 从 concept_map.json 回填/补充概念 %d 只" % _bf)
        except Exception as _e:
            print("  [防覆盖] concept_map 回填失败: %s" % _e)
    else:
        print("  [防覆盖] ⚠️ 未找到 concept_map.json，跳过概念回填（概念可能丢失）")

    result = {"update_time": time.strftime("%Y-%m-%d %H:%M"),
              "total_stocks": len(merged), "total_sectors": len(sectors),
              "total_associations": assoc, "stocks": merged}
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print("=== 合并完成 ===")
    print("  耗时 %.1fs, 写入 %s" % (time.time() - t0, OUT_FILE))
    print("  总股票 %d, 含行业 %d (%.1f%%), 含概念 %d"
          % (len(merged), total_ind, 100.0*total_ind/max(1,len(merged)), total_con))
    print("  行业/概念去重 %d 类, 总关联 %d" % (len(sectors), assoc))
    if total_ind == 0:
        print("  [告警] ⚠️ 行业源全部不可用")
    if total_con == 0:
        print("  [告警] ⚠️ 概念源不可用（东财 datacenter 软封禁），已保留缓存；东财恢复后自动补齐")

def main():
    # 全量模式不跳过非交易日（云端随时可跑）
    # 非交易日跳过行业映射重建，避免休市日空跑抓行情
    try:
        from is_trading_day import is_trading_day as _itd
    except Exception:
        _itd = None
    _fu = globals().get("_FULL_UNIVERSE", False)
    if not _fu and _itd is not None and not _itd():
        import datetime as _dt
        _w = _dt.date.today().weekday()
        _why = "周末" if _w >= 5 else "法定假日"
        print("⏭️ 非交易日（%s），行业映射重建跳过" % _why)
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=0, help="分片序号(1-based)，0=自动全量分片")
    ap.add_argument("--of", type=int, default=0, help="总分片数，0=自动")
    ap.add_argument("--merge", action="store_true", help="仅合并已有分片")
    ap.add_argument("--shards", type=int, default=1,
                   help="自动分片并行进程数(默认1=串行最稳, 避免BaoStock并发登录限流)")
    ap.add_argument("--full-universe", action="store_true",
                   help="强制全量模式：覆盖所有 A 股（5199只），读 stock_names.json 而非候选池")
    args = ap.parse_args()
    if args.full_universe:
        globals()["_FULL_UNIVERSE"] = True
        print("[全量模式] 覆盖所有 A 股（含非候选池冷门股）")
    if args.merge:
        merge()
    elif args.shard and args.of:
        run_shard(args.shard, args.of)
    else:
        # 自动分片（默认 --shards 1 = 串行）：候选池+金股池并集 ~384 只，单进程约 20-25 分钟。
        # 串行可避免 BaoStock 并发登录限流（本环境登录偶发失败）；如需加速可 --shards N，
        # 但并发进程数建议 <=3 以免触发限流。17:30 任务显式传 --shards 1。
        import subprocess
        N = max(1, args.shards)
        py = sys.executable
        script = os.path.abspath(__file__)
        print("[自动分片] 启动 %d 个并行进程..." % N)
        procs = []
        for i in range(1, N + 1):
            cmd = [py, script, "--shard", str(i), "--of", str(N)]
            if globals().get("_FULL_UNIVERSE", False):
                cmd.append("--full-universe")
            p = subprocess.Popen(cmd)
            procs.append(p)
        for p in procs:
            p.wait()
        print("[自动分片] 各分片完成，开始合并...")
        merge()

if __name__ == "__main__":
    main()
