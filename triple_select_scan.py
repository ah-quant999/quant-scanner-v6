#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
暂未上架实验: 三重选股(金钻起涨 + 波段是金 + 主力清洗 三维共振)
================================================================
来源: 阿狸咪 2026-07-15 交接文档「三重选股」4 个通达信公式中的 3 个
  - 金钻起涨 (条件选股, 今早调试确认最终版)
  - 波段是金 (副图指标 -> 波段多头)
  - 主力清洗 (副图指标 -> 主力进场/出货)
  - (大单500万分时图 暂缺源码 .tn6 加密未解出, 未接入)

本脚本**完全自包含**: 自带全部指标计算 (不依赖 scanner.calc_*, 仅复用
scanner 的数据获取 load_candidate_pool / fetch_a_daily), 避免与线上主扫描
scanner.py 冲突。实验期不部署、不污染主站, 只写本地 data/experiment/ 观察。

设计目的: 跟跑几天看三重选股命中稳定性 + 后续表现(胜率), 验证后再决定是否上云。

用法:
  python triple_select_scan.py [--limit N] [--date YYYY-MM-DD]
  --limit N : 仅扫描前 N 只 (调试/控时, 避开 BaoStock 限流)
"""
import os
import sys
import json
import argparse
import datetime

import numpy as np
import pandas as pd

# 将脚本所在目录注入 sys.path，使 import scanner 可用（根目录或子目录调用均可）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scanner


# ===================== 自包含辅助函数 (与 scanner 同语义, 独立副本) =====================
def ref(series, n):
    if isinstance(n, pd.Series):
        result = pd.Series(np.nan, index=series.index)
        for i in range(len(series)):
            shift_n = max(0, int(n.iloc[i])) if pd.notna(n.iloc[i]) else 0
            if i - shift_n >= 0:
                result.iloc[i] = series.iloc[i - shift_n]
        return result
    return series.shift(int(n) if pd.notna(n) else 0)


def llv(series, n):
    if isinstance(n, pd.Series):
        result = pd.Series(np.nan, index=series.index)
        for i in range(len(series)):
            window = max(1, int(n.iloc[i])) if pd.notna(n.iloc[i]) else 1
            start = max(0, i - window + 1)
            result.iloc[i] = series.iloc[start:i + 1].min()
        return result
    return series.rolling(window=max(1, int(n)), min_periods=1).min()


def hhv(series, n):
    if isinstance(n, pd.Series):
        result = pd.Series(np.nan, index=series.index)
        for i in range(len(series)):
            window = max(1, int(n.iloc[i])) if pd.notna(n.iloc[i]) else 1
            start = max(0, i - window + 1)
            result.iloc[i] = series.iloc[start:i + 1].max()
        return result
    return series.rolling(window=max(1, int(n)), min_periods=1).max()


def sma_tdx(series, n, m):
    result = pd.Series(np.nan, index=series.index)
    result.iloc[0] = series.iloc[0]
    for i in range(1, len(series)):
        result.iloc[i] = (series.iloc[i] * m + result.iloc[i - 1] * (n - m)) / n
    return result


def xma(series, n):
    """通达信 XMA 近似 (scanner 同款: 对称局部均值窗口)。注意: 此即 XMA 重绘特性来源。"""
    half = n // 2
    result = pd.Series(np.nan, index=series.index)
    for i in range(len(series)):
        start = max(0, i - half)
        end = min(len(series), i + half + 1)
        result.iloc[i] = series.iloc[start:end].mean()
    return result


def cross(a, b):
    return (a > b) & (a.shift(1) <= b.shift(1))


def ma(series, n):
    return series.rolling(window=n, min_periods=1).mean()


def forcast(series, n):
    """通达信 FORCAST(X,N): 基于最近 N 周期线性回归返回预测值 (非未来函数)。"""
    s = np.asarray(series, dtype=float)
    out = np.full(len(s), np.nan)
    x = np.arange(n, dtype=float)
    for i in range(n - 1, len(s)):
        y = s[i - n + 1:i + 1]
        if np.any(np.isnan(y)):
            continue
        coef = np.polyfit(x, y, 1)
        out[i] = coef[0] * x[-1] + coef[1]
    return pd.Series(out, index=series.index)


# ===================== 三个指标 (阿狸咪公式逐行转写) =====================
def ts_calc_jinzuan(df):
    """金钻起涨 — 严格对齐阿狸咪 2026-07-15 今早调试确认最终版 (tdx_formulas/金钻起涨.tni)。"""
    H = df["high"]; L = df["low"]; C = df["close"]; O = df["open"]
    V = df.get("volume", pd.Series(0, index=df.index))

    AH = xma(xma(H, 25), 25)
    AL = xma(xma(L, 25), 25)
    金钻趋势 = AL - (AH - AL)
    金牛 = AH - (AL - AH)
    df["金钻趋势"] = 金钻趋势
    df["金牛"] = 金牛
    df["黄柱"] = 金钻趋势 > H

    if "volume" in df.columns and V.sum() > 0:
        JJ = (H + L + C) / 3
        HL_eq = (H == L)
        QJ0 = V / pd.Series(np.where(HL_eq, 4, H - L), index=df.index)
        T1 = pd.Series(np.where(HL_eq, 1, np.minimum(C, O) - L), index=df.index)
        T2 = pd.Series(np.where(HL_eq, 1, JJ - np.minimum(C, O)), index=df.index)
        T3 = pd.Series(np.where(HL_eq, 1, H - np.maximum(C, O)), index=df.index)
        T4 = pd.Series(np.where(HL_eq, 1, np.maximum(C, O) - JJ), index=df.index)
        QJ1 = QJ0 * T1; QJ2 = QJ0 * T2; QJ3 = QJ0 * T3; QJ4 = QJ0 * T4
        DDX = ((QJ1 + QJ2) - (QJ3 + QJ4)) / 10000
        V2 = sma_tdx(pd.Series(np.where(C >= ref(C, 1), DDX, -DDX / 100), index=df.index), 2, 1)
        DY = (C < ref(C, 1))
        DY2 = ref(V2, 1) - pd.Series(DY, index=df.index, dtype=float)
        金钻起涨 = (C > O) & (DY2 < 0.02) & (ma(C, 5) > ma(C, 60)) & \
                  (C / ref(C, 1) >= 1.02) & (H < 金牛) & (L < 金钻趋势)
    else:
        金钻起涨 = pd.Series(False, index=df.index)
    df["金钻起涨"] = 金钻起涨
    return df


def ts_calc_band(df):
    """波段是金 副图指标 -> 波段多头。信号规则(公式语义, 非自由发挥):
       波段多头 = 主趋势 VAR7 向上 且 七星转向蓝柱 (TOWERC>=REF(TOWERC,1))。"""
    O = df["open"]; H = df["high"]; L = df["low"]; C = df["close"]

    def ema(s, n):
        return s.ewm(span=n, adjust=False).mean()

    OHLC4 = (O + H + L + C) / 4
    A1 = (ema(OHLC4, 3) + ema(OHLC4, 6) + ema(OHLC4, 9)) / 3
    A2 = (ema(OHLC4, 5) + ema(OHLC4, 10) + ema(OHLC4, 20)) / 3
    A3 = (ema(OHLC4, 7) + ema(OHLC4, 14) + ema(OHLC4, 28)) / 3
    A4 = (ema(OHLC4, 9) + ema(OHLC4, 18) + ema(OHLC4, 36)) / 3
    A5 = (ema(OHLC4, 11) + ema(OHLC4, 22) + ema(OHLC4, 44)) / 3
    A6 = (ema(OHLC4, 13) + ema(OHLC4, 26) + ema(OHLC4, 52)) / 3
    A7 = (ema(OHLC4, 21) + ema(OHLC4, 34) + ema(OHLC4, 68)) / 3
    VAR1 = forcast(A1, 6); VAR2 = forcast(A2, 6); VAR3 = forcast(A3, 6)
    VAR4 = forcast(A4, 6); VAR5 = forcast(A5, 6); VAR6 = forcast(A6, 6); VAR7 = forcast(A7, 6)
    TOWERC = forcast(ema((3 * C + 2 * O + H + L) / 7, 3), 6)
    df["波段多头"] = (VAR7 > ref(VAR7, 1)) & (TOWERC >= ref(TOWERC, 1))
    df["波段_VAR7"] = VAR7
    df["波段_TOWERC"] = TOWERC
    return df


def ts_calc_zhuli(df):
    """主力清洗 副图指标 -> 主力进场/出货。信号规则(公式语义, 非自由发挥):
       主力进场 = VAR5>REF(VAR5,1) (红柱=建仓)
       主力出货 = VAR51>REF(VAR51,1)(青柱=出货, 危险)。"""
    O = df["open"]; H = df["high"]; L = df["low"]; C = df["close"]

    def ema(s, n):
        return s.ewm(span=n, adjust=False).mean()

    VAR1 = ref((L + O + C + H) / 4, 1)
    VAR2 = sma_tdx(abs(L - VAR1), 13, 1) / sma_tdx(np.maximum(L - VAR1, 0), 10, 1)
    VAR3 = ema(VAR2, 10)
    VAR4 = llv(L, 33)
    VAR5 = ema(VAR3.where(L <= VAR4, 0), 3)
    VAR21 = sma_tdx(abs(H - VAR1), 13, 1) / sma_tdx(np.minimum(H - VAR1, 0), 10, 1)
    VAR31 = ema(VAR21, 10)
    VAR41 = hhv(H, 33)
    VAR51 = ema(VAR31.where(H >= VAR41, 0), 3)
    df["主力进场"] = VAR5 > ref(VAR5, 1)
    df["主力出货"] = VAR51 > ref(VAR51, 1)
    df["主力洗盘"] = VAR5 < ref(VAR5, 1)
    df["主力拉高"] = VAR51 < ref(VAR51, 1)
    return df


# ===================== 三重选股组合判定 =====================
def evaluate(df):
    df = ts_calc_zhuli(ts_calc_band(ts_calc_jinzuan(df.copy())))
    last = df.iloc[-1]
    金钻起涨 = bool(last.get("金钻起涨", False))
    波段多头 = bool(last.get("波段多头", False))
    主力进场 = bool(last.get("主力进场", False))
    主力出货 = bool(last.get("主力出货", False))
    三重选股 = 金钻起涨 and 波段多头 and 主力进场 and not 主力出货
    return dict(
        金钻起涨=金钻起涨, 波段多头=波段多头, 主力进场=主力进场,
        主力出货=主力出货, 三重选股=三重选股,
        close=float(last["close"]),
        金钻趋势=float(last.get("金钻趋势", float("nan"))),
        金牛=float(last.get("金牛", float("nan"))),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="仅扫描前 N 只 (调试/控时)")
    ap.add_argument("--date", type=str, default=datetime.date.today().strftime("%Y-%m-%d"))
    args = ap.parse_args()

    pool = scanner.load_candidate_pool() or {}
    items = []
    for k, info in pool.items():
        mkt = info.get("market", "")
        if mkt not in ("sh", "sz"):
            continue  # 仅 A 股 (跳过港股/其他)
        code = str(info.get("code") or k)
        if not code.isdigit():
            continue
        items.append((code, info))
    if args.limit > 0:
        items = items[:args.limit]

    total = len(items)
    scanned = 0
    failed = 0
    sig = {k: 0 for k in ["金钻起涨", "波段多头", "主力进场", "主力出货", "三重选股"]}
    hits = []
    # 各信号个股明细（便于实验盯盘逐只观察）
    lists = {k: [] for k in ["金钻起涨", "波段多头", "主力进场", "主力出货"]}

    print(f"[三重选股实验] 候选 A 股 {total} 只, 本次扫描 {len(items)} 只")
    for idx, (code, info) in enumerate(items):
        try:
            df = scanner.fetch_a_daily(code, bars=130)
            if df is None or len(df) < 60:
                failed += 1
                continue
            r = evaluate(df)
            scanned += 1
            for k in sig:
                if r[k]:
                    sig[k] += 1
            name = info.get("name") or info.get("stock_name") or code
            close = round(r["close"], 2)
            for k in lists:
                if r.get(k):
                    lists[k].append(dict(code=str(code), name=name, close=close))
            if r["三重选股"]:
                hits.append(dict(
                    code=str(code), name=name, close=close,
                    金钻起涨=True, 波段多头=True, 主力进场=True, 主力出货=False,
                ))
            if (idx + 1) % 20 == 0:
                print(f"  ...已处理 {idx+1}/{len(items)}, 三重命中 {len(hits)}")
        except Exception as e:
            failed += 1
            continue

    out = dict(
        date=args.date, total=total, scanned=scanned, failed=failed,
        signals=sig, hits=hits, lists=lists,
        generated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    # 输出目录: repo-temp/data/experiment/
    here = os.path.dirname(os.path.abspath(__file__))
    exp_dir = os.path.normpath(os.path.join(here, "..", "..", "data", "experiment"))
    os.makedirs(exp_dir, exist_ok=True)
    f1 = os.path.join(exp_dir, f"triple_select_{args.date.replace('-', '')}.json")
    json.dump(out, open(f1, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # 累计 history (便于几天后看趋势)
    hf = os.path.join(exp_dir, "triple_select_history.json")
    hist = {}
    if os.path.exists(hf):
        try:
            hist = json.load(open(hf, encoding="utf-8"))
        except Exception:
            hist = {}
    hist[args.date] = dict(scanned=scanned, failed=failed, signals=sig, hits=len(hits))
    json.dump(hist, open(hf, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(f"[三重选股实验] 扫描 {scanned}/{total} 失败 {failed}")
    print(f"  信号计数: {sig}")
    print(f"  三重选股命中 {len(hits)} 只: {[h['code'] for h in hits]}")
    print(f"  输出: {f1}")


if __name__ == "__main__":
    main()
