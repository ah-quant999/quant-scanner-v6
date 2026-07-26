# -*- coding: utf-8 -*-
"""
腾讯 GTimg 数据源适配器（专供 GitHub Actions / 云端 runner）
============================================================
美区 runner 无法直接访问 akshare/东财/BaoStock 等中国 HTTP 数据源，
但腾讯 GTimg（qt.gtimg.cn）和腾讯前复权日K（web.ifzq.gtimg.cn）
在美国网络可达。本模块提供：

- 实时行情批量获取：候选池/金股池构建
- 前复权日K获取：scanner 三线共振计算
- 成交额/成交量排序：活跃股池

本地双机（小九/阿狸咪）仍走 mootdx/akshare，不使用本模块，
避免与现有稳定链路冲突。
"""
import os
import re
import json
import time
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd

# ════════════════════════════════════════════════════════════════
# 环境检测
# ════════════════════════════════════════════════════════════════
def is_cloud_runner():
    """检测是否在 GitHub Actions / 云端 runner 上运行。"""
    return (
        os.environ.get("GITHUB_ACTIONS", "").lower() == "true"
        or os.environ.get("CLOUD_RUNNER", "").lower() == "true"
    )


# ════════════════════════════════════════════════════════════════
# 实时行情
# ════════════════════════════════════════════════════════════════
_GTIMG_BASE = "https://qt.gtimg.cn/q="
_GTIMG_BATCH = 800  # 实测 800 只 0.4s 可返回


def _gtimg_symbol(market, code):
    """把内部 (market, code) 转成 GTimg 接口符号。"""
    c = str(code).strip().zfill(6) if market != "hk" else str(code).strip().zfill(5)
    if market == "hk":
        return f"hk{c}"
    # 6/9/688 开头 或明确 sh 都走上海
    if c.startswith(("6", "9", "688")) or market == "sh":
        return f"sh{c}"
    return f"sz{c}"


def _parse_gtimg_realtime(body):
    """解析 GTimg 实时行情返回体。"""
    rows = []
    for line in body.strip().split(";"):
        line = line.strip()
        if not line:
            continue
        m = re.match(r'v_([a-z]+\d+)="([^"]+)"', line)
        if not m:
            continue
        full = m.group(1)
        fields = m.group(2).split("~")
        if len(fields) < 36:
            continue
        name = fields[1]
        code = fields[2]
        try:
            price = float(fields[3]) if fields[3] else 0.0
        except Exception:
            price = 0.0
        try:
            prev_close = float(fields[4]) if fields[4] else 0.0
        except Exception:
            prev_close = 0.0
        try:
            open_price = float(fields[5]) if fields[5] else 0.0
        except Exception:
            open_price = 0.0
        try:
            high = float(fields[6]) if fields[6] else 0.0
        except Exception:
            high = 0.0
        try:
            low = float(fields[7]) if fields[7] else 0.0
        except Exception:
            low = 0.0
        try:
            volume_shou = float(fields[36]) if fields[36] else 0.0
        except Exception:
            volume_shou = 0.0
        # 字段35 格式: 当前价/成交量/成交额
        amount = 0.0
        try:
            parts = fields[35].split("/")
            if len(parts) >= 3:
                amount = float(parts[2])
        except Exception:
            pass

        # 市场 & 板块
        if full.startswith("sh"):
            market = "sh"
            board = "科创板" if code.startswith("688") else "主板"
        elif full.startswith("sz"):
            market = "sz"
            board = "创业板" if code.startswith("3") else "主板"
        elif full.startswith("hk"):
            market = "hk"
            board = "港股"
        else:
            continue

        rows.append({
            "代码": code,
            "名称": name,
            "market": market,
            "board": board,
            "当前价": price,
            "昨收": prev_close,
            "今开": open_price,
            "最高": high,
            "最低": low,
            "成交量": volume_shou,  # 手
            "成交额": amount,       # 元
        })
    return pd.DataFrame(rows)


def fetch_gtimg_spot(codes=None, batch_size=_GTIMG_BATCH, timeout=30):
    """
    批量获取 GTimg 实时行情。

    Args:
        codes: list of (market, code)；为 None 时从 stock_names.json 加载全 A 股。
        batch_size: 每批最大数量（GTimg 实测可支持 800+）。
        timeout: 单批请求超时。

    Returns:
        pd.DataFrame or None
    """
    if codes is None:
        codes = _load_all_a_share_codes()
    if not codes:
        return None

    all_dfs = []
    for i in range(0, len(codes), batch_size):
        batch = codes[i:i + batch_size]
        gt_codes = [_gtimg_symbol(m, c) for m, c in batch]
        url = _GTIMG_BASE + ",".join(gt_codes)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("gbk", "ignore")
            df = _parse_gtimg_realtime(body)
            if df is not None and len(df):
                all_dfs.append(df)
                print(f"  [GTimg] batch {i // batch_size + 1}: {len(df)} 行")
            else:
                print(f"  [GTimg] batch {i // batch_size + 1}: 无数据")
        except Exception as e:
            print(f"  [GTimg] batch {i // batch_size + 1} 失败: {e}")
            time.sleep(1)

    if not all_dfs:
        return None
    return pd.concat(all_dfs, ignore_index=True)


def _load_all_a_share_codes():
    """从 stock_names.json 加载全 A 股代码列表。"""
    try:
        base = os.path.dirname(os.path.abspath(__file__))
        sn_file = os.path.join(base, "data", "stock_names.json")
        with open(sn_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        codes = []
        for s in data:
            c = str(s.get("code", "")).strip().zfill(6)
            if not c:
                continue
            m = "sh" if c.startswith(("6", "9", "688")) else "sz"
            codes.append((m, c))
        return codes
    except Exception as e:
        print(f"  [GTimg] 加载 stock_names.json 失败: {e}")
        return []


def _board_of_a(code):
    """A股代码 → 上市板。"""
    c = str(code).strip()
    if c.startswith(("600", "601", "603", "605", "000", "001", "002", "003")):
        return "主板"
    if c.startswith(("300", "301")):
        return "创业板"
    if c.startswith(("688", "689")):
        return "科创板"
    return None


def fetch_volume_top_stocks_gtimg(top_cy=100, top_kc=100, top_zb=100, top_hk=0):
    """
    获取按成交额排序的活跃股池，返回 scanner.py 需要的 tuple 列表。
    云端专用：本地双机不走这里。
    """
    print(f"  [GTimg] 获取实时行情并排序 (CY={top_cy}, KC={top_kc}, ZB={top_zb}, HK={top_hk})...")
    df = fetch_gtimg_spot()
    if df is None or df.empty:
        print("  [GTimg] 实时行情获取失败")
        return []

    df = df[df["成交额"] > 0].copy()
    df["_board"] = df["代码"].map(_board_of_a)

    all_stocks = []
    for board, top_n in (("创业板", top_cy), ("科创板", top_kc), ("主板", top_zb)):
        sub = df[df["_board"] == board].sort_values("成交额", ascending=False).head(top_n)
        for _, r in sub.iterrows():
            code = r["代码"]
            mkt = r["market"]
            # 计算总市值（亿元）：用价格估算，但无股本数据，置 0 由后续 fallback 处理
            mv_yi = 0.0
            all_stocks.append((
                code, r["名称"], mkt, board,
                float(r["成交额"]), 0.0, mv_yi, "混合"
            ))
        print(f"    {board}: {len(sub)} 只")

    # 港股：GTimg 港股实时行情不稳定，默认云端不处理；若 top_hk>0 则尝试
    if top_hk > 0:
        hk_df = df[df["market"] == "hk"].sort_values("成交额", ascending=False).head(top_hk)
        for _, r in hk_df.iterrows():
            all_stocks.append((
                r["代码"].zfill(5), r["名称"], "hk", "港股",
                float(r["成交额"]), 0.0, 0.0, "港股"
            ))
        print(f"    港股: {len(hk_df)} 只")

    print(f"  [GTimg] 股池汇总: {len(all_stocks)} 只")
    return all_stocks


# ════════════════════════════════════════════════════════════════
# 历史日K（前复权）
# ════════════════════════════════════════════════════════════════
def _fetch_gtimg_daily_single(args, retry=1):
    """单只股票获取前复权日K。供多线程调用。"""
    code, market, bars = args
    c = str(code).zfill(6)
    if market == "hk":
        return None
    gt_code = f"sh{c}" if c.startswith(("6", "9", "688")) or market == "sh" else f"sz{c}"
    end = time.strftime("%Y-%m-%d")
    start = (pd.Timestamp.now() - pd.Timedelta(days=bars * 2)).strftime("%Y-%m-%d")
    url = (
        f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        f"?param={gt_code},day,{start},{end},{bars},qfq"
    )
    for attempt in range(retry + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode("utf-8", "ignore"))
            klines = data.get("data", {}).get(gt_code, {}).get("qfqday", [])
            if not klines or len(klines) < 60:
                return None
            rows = []
            for k in klines:
                if len(k) < 6:
                    continue
                rows.append({
                    "date": k[0],
                    "open": float(k[1]),
                    "close": float(k[2]),
                    "high": float(k[3]),
                    "low": float(k[4]),
                    "volume": float(k[5]),
                })
            df = pd.DataFrame(rows)
            if len(df) > 1:
                df["pct_chg"] = ((df["close"] / df["close"].shift(1) - 1) * 100).round(2)
            else:
                df["pct_chg"] = 0.0
            return df.reset_index(drop=True)
        except Exception as e:
            if attempt < retry:
                time.sleep(1.5 ** attempt)
            else:
                return None
    return None


def fetch_a_daily_gtimg(code, market="sh", bars=250):
    """单只股票获取前复权日K（云端专用）。"""
    return _fetch_gtimg_daily_single((code, market, bars))


def fetch_a_daily_batch_gtimg(codes, market="sh", bars=250, max_workers=3):
    """批量获取前复权日K，返回 {code: DataFrame}。

    注意：GTimg 日K接口并发敏感，默认 max_workers=3；过小批量会慢，过大则失败率高。
    """
    results = {}
    args = [(c, market, bars) for c in codes]
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_fetch_gtimg_daily_single, a): a[0] for a in args}
        for fut in as_completed(futures):
            c = futures[fut]
            try:
                df = fut.result()
                if df is not None and len(df) >= 60:
                    results[c] = df
            except Exception:
                pass
    return results


# ════════════════════════════════════════════════════════════════
# 候选池构建辅助：直接产出 candidate_pool.json 风格结构
# ════════════════════════════════════════════════════════════════
def build_candidate_pool_from_gtimg():
    """用 GTimg 实时行情构建 candidate_pool.json 内容（云端专用）。"""
    df = fetch_gtimg_spot()
    if df is None or df.empty:
        return None

    df = df[df["成交额"] > 0].copy()
    df["_board"] = df["代码"].map(_board_of_a)

    pool = {}
    for board, top_n in (("主板", 100), ("创业板", 100), ("科创板", 100)):
        sub = df[df["_board"] == board].sort_values("成交额", ascending=False).head(top_n)
        for _, r in sub.iterrows():
            code = r["代码"]
            mkt = r["market"]
            key = f"{mkt}_{code}"
            pool[key] = {
                "code": code,
                "name": r["名称"],
                "market": mkt,
                "board_label": board,
                "sources": [f"{board}成交前{top_n}"],
            }
    return pool


# 简单自测（仅在直接执行时）
if __name__ == "__main__":
    print(f"cloud_runner={is_cloud_runner()}")
    print("--- 实时行情测试 ---")
    df = fetch_gtimg_spot([("sh", "600000"), ("sz", "000001"), ("sz", "300001")])
    print(df[["代码", "名称", "当前价", "成交额"]])
    print("--- 日K测试 ---")
    dfk = fetch_a_daily_gtimg("600000", "sh", 250)
    print(dfk.tail())
