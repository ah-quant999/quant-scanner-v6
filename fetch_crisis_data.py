#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_crisis_data.py — 危机雷达页数据采集

采集六维危机监测所需的 17 项指标，每项附近 1 年历史序列，
计算「近1年历史分位」+ 「趋势」，产出 data/crisis_data.json。

六维（雷达图）：流动性 / 利率 / 经济 / 房地产 / 全球 / 汇率
三大类（综合指数权重）：货币 40% / 经济 35% / 全球 25%

分位说明：percentile = 当前值在近1年历史中的百分位（0-100）。
方向说明：
  high_bad  = 数值越高越危险（SHIBOR/VIX/DXY/两融/离岸汇率）→ 危险分 = 分位
  low_bad   = 数值越低越危险（期限利差/中美利差/PMI/出口/CPI/房价/铜金比/BDI/M2/社融/原油/LPR）→ 危险分 = 100-分位
历史缺失时回退阈值打分（fallback_score）。

⚠️ 禁止删除（见 DO_NOT_DELETE.txt）。数据源全部实测于 2026-07-11。
"""
import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# ════════════════════════════════════════
#  指标注册表：定义每项指标的分类/维度/单位/方向
#  dir: high_bad(越高越危险) / low_bad(越低越危险)
# ════════════════════════════════════════
REGISTRY = {
    # ── 货币-流动性维 ──
    'shibor_on':      {'name': 'SHIBOR隔夜',   'cat': '货币', 'dim': '流动性', 'freq': '日频', 'unit': '%',    'dir': 'high_bad'},
    'margin_balance': {'name': '两融余额',     'cat': '货币', 'dim': '流动性', 'freq': '日频', 'unit': '万亿', 'dir': 'high_bad'},
    'm2_yoy':         {'name': 'M2同比',       'cat': '货币', 'dim': '流动性', 'freq': '月频', 'unit': '%',    'dir': 'low_bad'},
    # ── 货币-利率维 ──
    'term_spread':    {'name': '期限利差10Y-2Y', 'cat': '货币', 'dim': '利率', 'freq': '日频', 'unit': '%',    'dir': 'low_bad'},
    'cn_us_spread':   {'name': '中美利差10Y',    'cat': '货币', 'dim': '利率', 'freq': '日频', 'unit': '%',    'dir': 'low_bad'},
    'lpr_5y':         {'name': 'LPR 5年',        'cat': '货币', 'dim': '利率', 'freq': '月频', 'unit': '%',    'dir': 'low_bad'},
    # ── 经济-经济维 ──
    'pmi':            {'name': '制造业PMI',     'cat': '经济', 'dim': '经济', 'freq': '月频', 'unit': '',     'dir': 'low_bad'},
    'social_fin_yoy': {'name': '社融增量·滚动同比', 'cat': '经济', 'dim': '经济', 'freq': '月频', 'unit': '%', 'dir': 'low_bad'},
    'export_yoy':     {'name': '出口同比',      'cat': '经济', 'dim': '经济', 'freq': '月频', 'unit': '%',    'dir': 'low_bad'},
    'cpi_yoy':        {'name': 'CPI同比',       'cat': '经济', 'dim': '经济', 'freq': '月频', 'unit': '%',    'dir': 'low_bad'},
    # ── 经济-房地产维 ──
    'house_price_2h': {'name': '70城二手房价环比', 'cat': '经济', 'dim': '房地产', 'freq': '月频', 'unit': '%', 'dir': 'low_bad'},
    # ── 全球-全球维 ──
    'vix':            {'name': 'VIX恐慌指数',   'cat': '全球', 'dim': '全球', 'freq': '日频', 'unit': '',     'dir': 'high_bad'},
    'dxy':            {'name': '美元指数DXY',   'cat': '全球', 'dim': '全球', 'freq': '日频', 'unit': '',     'dir': 'high_bad'},
    'copper_gold':    {'name': '铜金比',        'cat': '全球', 'dim': '全球', 'freq': '日频', 'unit': '',     'dir': 'low_bad'},
    'bdi':            {'name': 'BDI波罗的海',   'cat': '全球', 'dim': '全球', 'freq': '日频', 'unit': '',     'dir': 'low_bad'},
    'oil_wti':        {'name': 'WTI原油',       'cat': '全球', 'dim': '全球', 'freq': '日频', 'unit': '$',    'dir': 'low_bad'},
    # ── 全球-汇率维 ──
    'usdcnh':         {'name': '离岸人民币',    'cat': '全球', 'dim': '汇率', 'freq': '日频', 'unit': '',     'dir': 'high_bad'},
    # ── 全球-全球维（C 扩充：全球风险更厚实）──
    'us_2s10s':       {'name': '美债10Y-2Y倒挂', 'cat': '全球', 'dim': '全球', 'freq': '日频', 'unit': '%',    'dir': 'low_bad'},
    'us_2y':          {'name': '美债2Y收益率',   'cat': '全球', 'dim': '全球', 'freq': '日频', 'unit': '%',    'dir': 'high_bad'},
}


def safe(fn, name):
    try:
        return fn()
    except Exception as e:
        print(f"  [WARN] {name} 失败: {e}")
        return None


# ════════════════════════════════════════
#  跨机历史缓存：DXY / USDCNH 在东财 kline 常因限流拿不到历史序列，
#  单位机（小九）跑通时把历史存入 data/_crisis_hist_cache.json（走坚果云双机共享），
#  家用机（阿狸咪）限流时用 macro_data.json 当前值 + 缓存历史算真实分位。
# ════════════════════════════════════════
HIST_CACHE = os.path.join(DATA_DIR, '_crisis_hist_cache.json')


def load_cached_hist(name):
    try:
        if os.path.exists(HIST_CACHE):
            c = json.load(open(HIST_CACHE, 'r', encoding='utf-8'))
            rec = c.get(name)
            if rec and rec.get('hist'):
                return rec['hist'], rec.get('date')
    except Exception:
        pass
    return None, None


def save_cached_hist(name, hist, date):
    try:
        c = {}
        if os.path.exists(HIST_CACHE):
            c = json.load(open(HIST_CACHE, 'r', encoding='utf-8'))
        c[name] = {'hist': hist, 'date': date}
        json.dump(c, open(HIST_CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
    except Exception:
        pass


# ════════════════════════════════════════
#  本地逐日累加历史（方案A，根治 DXY/USDCNH 伪分位）
#  东财 kline 在双机都常限流拿不到 DXY/USDCNH 历史序列，原跨机缓存从未触发。
#  改用 Sina 实时值（双机均可取）逐日累加进 data/{key}_hist.json（走坚果云双机共享）：
#  每交易日跑一次即追加当日值，~20 个交易日起有真实分位、半年后稳定。
#  文件格式：[{"date":"2026-07-11","value":100.96}, ...] 按日期正序，最多保留 max_keep 条。
# ════════════════════════════════════════
ACCUM_KEYS = ('dxy', 'usdcnh')


def _accum_path(key):
    return os.path.join(DATA_DIR, f'{key}_hist.json')


def load_accum_hist(key):
    try:
        p = _accum_path(key)
        if os.path.exists(p):
            arr = json.load(open(p, 'r', encoding='utf-8'))
            if isinstance(arr, list):
                return arr
    except Exception:
        pass
    return []


def append_accum_hist(key, value, date, max_keep=400):
    """追加当日值；同日已记录则去重（避免一日多跑重复）。"""
    if value is None or not date:
        return
    try:
        arr = load_accum_hist(key)
        if any(x.get('date') == date for x in arr):
            return
        arr.append({'date': str(date)[:10], 'value': round(float(value), 4)})
        if len(arr) > max_keep:
            arr = arr[-max_keep:]
        json.dump(arr, open(_accum_path(key), 'w', encoding='utf-8'), ensure_ascii=False)
    except Exception:
        pass


def accum_history_values(key):
    return [x['value'] for x in load_accum_hist(key) if x.get('value') is not None]


def percentile(cur, hist):
    """当前值在历史序列中的百分位 (0-100)"""
    h = [x for x in hist if x is not None]
    if not h or cur is None:
        return None
    n = len(h)
    below = sum(1 for x in h if x <= cur)
    return round(below / n * 100, 1)


def trend_of(hist, freq):
    """趋势：日频比 5 期前，月频比 1 期前"""
    h = [x for x in hist if x is not None]
    if len(h) < 2:
        return 'flat'
    lag = 5 if freq == '日频' else 1
    if len(h) <= lag:
        lag = 1
    cur = h[-1]
    prev = h[-1 - lag]
    d = cur - prev
    scale = abs(prev) if prev else 1
    rel = d / scale if scale else 0
    if rel > 0.005:
        return 'up'
    if rel < -0.005:
        return 'down'
    return 'flat'


# ════════════════════════════════════════
#  各指标采集器：返回 (current_value, date, history_list[chronological])
# ════════════════════════════════════════

def fetch_all():
    import akshare as ak
    import pandas as pd

    out = {}  # key -> {'value','date','history'}

    def put(key, value, date, history):
        out[key] = {'value': value, 'date': date, 'history': history}

    # ---- 中债/美债曲线（一次调用出 期限利差 + 中美利差）----
    print("中债/美债曲线...")
    df = safe(lambda: ak.bond_zh_us_rate(start_date='20250101'), 'bond_zh_us_rate')
    if df is not None and len(df) > 0:
        df = df.copy()
        # 期限利差 10Y-2Y
        ts = df[['日期', '中国国债收益率10年-2年']].dropna()
        if len(ts):
            hist = [round(float(x), 4) for x in ts['中国国债收益率10年-2年'].tolist()][-260:]
            last = ts.iloc[-1]
            put('term_spread', round(float(last['中国国债收益率10年-2年']), 4), str(last['日期'])[:10], hist)
        # 中美利差 10Y = 中10Y - 美10Y
        cu = df[['日期', '中国国债收益率10年', '美国国债收益率10年']].dropna()
        if len(cu):
            spr = (cu['中国国债收益率10年'] - cu['美国国债收益率10年'])
            hist = [round(float(x), 3) for x in spr.tolist()][-260:]
            last_d = str(cu.iloc[-1]['日期'])[:10]
            put('cn_us_spread', round(float(spr.iloc[-1]), 3), last_d, hist)
        # 美债 10Y-2Y 倒挂（衰退信号，负值=倒挂，越低越危险）
        us_spr = df[['日期', '美国国债收益率10年', '美国国债收益率2年']].dropna()
        if len(us_spr):
            diff = (us_spr['美国国债收益率10年'] - us_spr['美国国债收益率2年'])
            hist = [round(float(x), 3) for x in diff.tolist()][-260:]
            last_d = str(us_spr.iloc[-1]['日期'])[:10]
            put('us_2s10s', round(float(diff.iloc[-1]), 3), last_d, hist)
        # 美债 2Y 收益率（Fed 政策预期代理，越高=货币越紧）
        uy = df[['日期', '美国国债收益率2年']].dropna()
        if len(uy):
            hist = [round(float(x), 3) for x in uy['美国国债收益率2年'].tolist()][-260:]
            last_d = str(uy.iloc[-1]['日期'])[:10]
            put('us_2y', round(float(uy.iloc[-1]['美国国债收益率2年']), 3), last_d, hist)

    # ---- SHIBOR 隔夜 ----
    print("SHIBOR...")
    ds = safe(lambda: ak.macro_china_shibor_all(), 'shibor')
    if ds is not None and len(ds) > 0:
        col = 'O/N-定价' if 'O/N-定价' in ds.columns else None
        if col:
            sub = ds[['日期', col]].dropna()
            hist = [round(float(x), 4) for x in sub[col].tolist()][-260:]
            last = sub.iloc[-1]
            put('shibor_on', round(float(last[col]), 4), str(last['日期'])[:10], hist)

    # ---- 两融余额（沪市，元 -> 万亿）----
    print("两融余额...")
    dm = safe(lambda: ak.macro_china_market_margin_sh(), 'margin')
    if dm is not None and len(dm) > 0:
        sub = dm[['日期', '融资融券余额']].dropna()
        vals = [round(float(x) / 1e12, 4) for x in sub['融资融券余额'].tolist()]
        hist = vals[-260:]
        last = sub.iloc[-1]
        put('margin_balance', round(float(last['融资融券余额']) / 1e12, 4), str(last['日期'])[:10], hist)

    # ---- M2 同比（月频）----
    print("M2同比...")
    dm2 = safe(lambda: ak.macro_china_money_supply(), 'm2')
    if dm2 is not None and len(dm2) > 0:
        c = '货币和准货币(M2)-同比增长'
        if c in dm2.columns:
            # 数据按时间倒序（最新在前）
            sub = dm2[['月份', c]].dropna()
            vals = [float(x) for x in sub[c].tolist()]
            vals = list(reversed(vals))  # 转为时间正序
            hist = vals[-24:]
            row0 = sub.iloc[0]
            date0 = str(row0['月份']).replace('年', '-').replace('月份', '-01').replace('月', '-01')
            put('m2_yoy', float(row0[c]), date0[:10], hist)

    # ---- LPR 5年（月频）----
    print("LPR...")
    dl = safe(lambda: ak.macro_china_lpr(), 'lpr')
    if dl is not None and len(dl) > 0 and 'LPR5Y' in dl.columns:
        sub = dl[['TRADE_DATE', 'LPR5Y']].dropna()
        hist = [float(x) for x in sub['LPR5Y'].tolist()][-24:]
        last = sub.iloc[-1]
        put('lpr_5y', float(last['LPR5Y']), str(last['TRADE_DATE'])[:10], hist)

    # ---- 70城二手房价环比（月频，全国均值）----
    print("70城房价...")
    dh = safe(lambda: ak.macro_china_new_house_price(), 'house')
    if dh is not None and len(dh) > 0:
        col = '二手住宅价格指数-环比'
        if col in dh.columns and '日期' in dh.columns:
            # 每月对所有城市取均值，指数100为持平 -> 转百分比 (val-100)
            g = dh.groupby('日期')[col].mean().dropna()
            g = g.sort_index()
            pct_series = [round(float(x) - 100, 3) for x in g.tolist()]
            hist = pct_series[-24:]
            last_date = str(g.index[-1])[:10]
            put('house_price_2h', pct_series[-1], last_date, hist)

    # ---- 东财月度：PMI / CPI / 出口 ----
    def em(report, page=30):
        import requests as rq
        url = 'https://datacenter-web.eastmoney.com/api/data/v1/get'
        try:
            r = rq.get(url, params={'reportName': report, 'columns': 'ALL', 'pageNumber': 1,
                                    'pageSize': page, 'sortColumns': 'REPORT_DATE', 'sortTypes': '-1'}, timeout=12)
            d = r.json()
            if d.get('success') and d.get('result', {}).get('data'):
                return d['result']['data']
        except Exception as e:
            print(f"  [WARN] EM {report} 失败: {e}")
        return None

    print("PMI...")
    p = em('RPT_ECONOMY_PMI')
    if p:
        rows = [x for x in p if x.get('MAKE_INDEX') is not None]
        vals = list(reversed([float(x['MAKE_INDEX']) for x in rows]))
        put('pmi', float(rows[0]['MAKE_INDEX']), str(rows[0]['REPORT_DATE'])[:10], vals[-24:])

    print("CPI...")
    c = em('RPT_ECONOMY_CPI')
    if c:
        rows = [x for x in c if x.get('NATIONAL_SAME') is not None]
        vals = list(reversed([float(x['NATIONAL_SAME']) for x in rows]))
        put('cpi_yoy', float(rows[0]['NATIONAL_SAME']), str(rows[0]['REPORT_DATE'])[:10], vals[-24:])

    print("出口同比...")
    e = em('RPT_ECONOMY_CUSTOMS')
    if e:
        rows = [x for x in e if x.get('EXIT_BASE_SAME') is not None]
        vals = list(reversed([float(x['EXIT_BASE_SAME']) for x in rows]))
        put('export_yoy', float(rows[0]['EXIT_BASE_SAME']), str(rows[0]['REPORT_DATE'])[:10], vals[-24:])

    # ---- 社融增量·滚动同比（月频）----
    # 用滚动12个月社融增量之和的同比，平滑单月流量噪声，近似社融存量增速趋势
    print("社融增量·滚动同比...")
    sf = safe(lambda: ak.macro_china_shrzgm(), 'shrzgm')
    if sf is not None and len(sf) > 25 and '社会融资规模增量' in sf.columns:
        s = sf[['月份', '社会融资规模增量']].dropna().copy()
        s['月份'] = s['月份'].astype(str)
        s = s.sort_values('月份')
        vals = [float(x) for x in s['社会融资规模增量'].tolist()]
        months = s['月份'].tolist()
        ttm = [sum(vals[i - 11:i + 1]) for i in range(11, len(vals))]  # 滚动12月之和
        ttm_months = months[11:]
        yoy = []  # (month, yoy%)
        for i in range(12, len(ttm)):
            base = ttm[i - 12]
            if base and abs(base) > 1e-6:
                yoy.append((ttm_months[i], round((ttm[i] - base) / abs(base) * 100, 1)))
        if yoy:
            last_m, last_v = yoy[-1]
            date = f"{last_m[:4]}-{last_m[4:6]}-01"
            put('social_fin_yoy', last_v, date, [v for _, v in yoy][-24:])

    # ---- 外盘：VIX / 黄金 / 铜 / 原油（含铜金比）----
    def ff(sym, tries=3):
        last = None
        for _i in range(tries):
            try:
                r = ak.futures_foreign_hist(symbol=sym)
                if r is not None and len(r) > 0:
                    return r
            except Exception as e:
                last = e
        print(f"  [WARN] foreign_{sym} 失败({tries}次): {last}")
        return None

    print("VIX...")
    dv = ff('VX')
    if dv is not None and len(dv) > 0:
        sub = dv[['date', 'close']].dropna()
        hist = [round(float(x), 2) for x in sub['close'].tolist()][-260:]
        put('vix', round(float(sub.iloc[-1]['close']), 2), str(sub.iloc[-1]['date'])[:10], hist)

    print("原油...")
    dcl = ff('CL')
    if dcl is not None and len(dcl) > 0:
        sub = dcl[['date', 'close']].dropna()
        hist = [round(float(x), 2) for x in sub['close'].tolist()][-260:]
        put('oil_wti', round(float(sub.iloc[-1]['close']), 2), str(sub.iloc[-1]['date'])[:10], hist)

    print("黄金/铜 -> 铜金比...")
    dgc = ff('GC')  # 黄金 $/oz
    dhg = ff('HG')  # 铜 美分/磅
    if dgc is not None and dhg is not None and len(dgc) and len(dhg):
        gc = dgc[['date', 'close']].dropna().rename(columns={'close': 'gold'})
        hg = dhg[['date', 'close']].dropna().rename(columns={'close': 'copper'})
        gc['date'] = gc['date'].astype(str).str[:10]
        hg['date'] = hg['date'].astype(str).str[:10]
        mg = pd.merge(gc, hg, on='date', how='inner').sort_values('date')
        # 铜金比 = 铜($/磅)*2204.62 / 金($/oz); 铜close为美分/磅 -> /100
        mg['ratio'] = (mg['copper'] / 100.0 * 2204.62) / mg['gold']
        hist = [round(float(x), 3) for x in mg['ratio'].tolist()][-260:]
        put('copper_gold', round(float(mg.iloc[-1]['ratio']), 3), str(mg.iloc[-1]['date'])[:10], hist)

    # ---- BDI ----
    print("BDI...")
    db = safe(lambda: ak.macro_shipping_bdi(), 'bdi')
    if db is not None and len(db) > 0 and '最新值' in db.columns:
        sub = db[['日期', '最新值']].dropna()
        hist = [float(x) for x in sub['最新值'].tolist()][-260:]
        put('bdi', float(sub.iloc[-1]['最新值']), str(sub.iloc[-1]['日期'])[:10], hist)

    # ---- DXY 美元指数（东财 kline 100.UDI，成功则缓存历史）----
    print("DXY...")
    try:
        import urllib.request as ur
        u = ('https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=100.UDI'
             '&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57'
             '&klt=101&fqt=0&end=20500101&lmt=300')
        req = ur.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
        j = json.loads(ur.urlopen(req, timeout=15).read().decode('utf-8'))
        kl = j.get('data', {}).get('klines', [])
        if kl:
            closes = [round(float(x.split(',')[2]), 2) for x in kl]
            last_date = kl[-1].split(',')[0]
            put('dxy', closes[-1], last_date, closes[-260:])
            save_cached_hist('dxy', closes[-260:], last_date)
    except Exception as ex:
        print(f"  [WARN] DXY 东财失败: {ex}")

    # ---- 离岸人民币 USDCNH（东财 kline 试多个 secid，成功则缓存历史；失败交给 main 用 macro_data+缓存历史兜底）----
    print("离岸人民币...")
    cnh_done = False
    for secid in ('133.USDCNHC', '133.USDCNH', '119.USDCNH', '100.USDCNH'):
        try:
            import urllib.request as ur2
            u = (f'https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}'
                 '&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57'
                 '&klt=101&fqt=0&end=20500101&lmt=300')
            req = ur2.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
            j = json.loads(ur2.urlopen(req, timeout=15).read().decode('utf-8'))
            kl = j.get('data', {}).get('klines', [])
            if kl and len(kl) > 30:
                closes = [round(float(x.split(',')[2]), 4) for x in kl]
                last_date = kl[-1].split(',')[0]
                put('usdcnh', closes[-1], last_date, closes[-260:])
                save_cached_hist('usdcnh', closes[-260:], last_date)
                cnh_done = True
                break
        except Exception:
            continue
    if not cnh_done:
        print("  [WARN] USDCNH 东财全部失败，将用 macro_data 当前值+缓存历史兜底")

    return out


# ════════════════════════════════════════
#  历史缺失时的阈值回退打分（返回 danger_score 0-100）
# ════════════════════════════════════════
def fallback_score(key, val):
    if val is None:
        return None
    t = {
        'shibor_on':      lambda v: 85 if v > 3 else (55 if v > 2 else 20),
        'margin_balance': lambda v: 75 if v > 1.9 else (45 if v > 1.6 else 25),
        'm2_yoy':         lambda v: 80 if v < 0 else (55 if v < 8 else 25),
        'term_spread':    lambda v: 85 if v < 0 else (55 if v < 0.3 else 20),
        'cn_us_spread':   lambda v: 85 if v < -2.5 else (55 if v < -1.5 else 25),
        'lpr_5y':         lambda v: 60 if v > 4.2 else 30,
        'pmi':            lambda v: 85 if v < 49 else (55 if v < 50 else 20),
        'social_fin_yoy': lambda v: 80 if v < 7 else (50 if v < 9 else 25),
        'export_yoy':     lambda v: 85 if v < -5 else (55 if v < 0 else 20),
        'cpi_yoy':        lambda v: 80 if v < 0 else (55 if v < 0.5 else 25),
        'house_price_2h': lambda v: 85 if v < -0.5 else (55 if v < 0 else 20),
        'vix':            lambda v: 85 if v > 30 else (55 if v > 20 else 20),
        # DXY：真实当前值→连续透明危险分（95≈平稳,112≈高压），去除三段硬编码假分位观感
        'dxy':            lambda v: max(5, min(98, (v - 98) / (110 - 98) * 90 + 8)),
        'copper_gold':    lambda v: 80 if v < 3 else (50 if v < 3.5 else 25),
        'bdi':            lambda v: 75 if v < 1200 else (45 if v < 1800 else 25),
        'oil_wti':        lambda v: 70 if v < 55 else (45 if v < 65 else 25),
        # USDCNH：真实当前值→连续透明危险分（7.0≈平稳,7.4≈贬值高压），去除三段硬编码假分位观感
        'usdcnh':         lambda v: max(5, min(98, (v - 7.0) / (7.4 - 7.0) * 90 + 8)),
        'us_2s10s':       lambda v: 85 if v < -0.5 else (55 if v < 0 else 20),   # 美债倒挂越深越危险
        'us_2y':          lambda v: 80 if v > 5.5 else (50 if v > 4.5 else 25),   # 美债2Y越高=货币越紧
    }.get(key)
    return t(val) if t else None


def main():
    print("=" * 50)
    print("危机雷达数据采集开始")
    print("=" * 50)

    raw = fetch_all()

    # macro_data.json 兜底：补齐采集失败但已有当前值的指标（如家用机限流的 DXY/USDCNH）
    # 当前值用 macro_data，历史优先用跨机缓存（单位机存的历史序列），无缓存才回退阈值
    try:
        with open(os.path.join(DATA_DIR, 'macro_data.json'), 'r', encoding='utf-8') as f:
            md = json.load(f)
        gm = md.get('global_macro', {})
        if raw.get('dxy', {}).get('value') is None and gm.get('dxy', {}).get('value') is not None:
            h, _ = load_cached_hist('dxy')
            raw['dxy'] = {'value': round(float(gm['dxy']['value']), 2), 'date': gm['dxy'].get('date', ''), 'history': h or []}
            print("  [FALLBACK] DXY 用 macro_data 当前值 + 缓存历史" if h else "  [FALLBACK] DXY 用 macro_data 当前值（无缓存历史，回退阈值）")
        if raw.get('vix', {}).get('value') is None and gm.get('vix', {}).get('value') is not None:
            raw['vix'] = {'value': round(float(gm['vix']['value']), 2), 'date': gm['vix'].get('date', ''), 'history': []}
        if raw.get('usdcnh', {}).get('value') is None and gm.get('usdcnh', {}).get('price') is not None:
            h, _ = load_cached_hist('usdcnh')
            raw['usdcnh'] = {'value': round(float(gm['usdcnh']['price']), 4), 'date': gm['usdcnh'].get('date', ''), 'history': h or []}
            print("  [FALLBACK] USDCNH 用 macro_data 当前值 + 缓存历史" if h else "  [FALLBACK] USDCNH 用 macro_data 当前值（无缓存历史，回退阈值）")
        # USDCNH 终极兜底：宏微观均无则用 Sina 现价（无历史）
        if raw.get('usdcnh', {}).get('value') is None:
            try:
                import urllib.request as ur3
                req = ur3.Request('http://hq.sinajs.cn/list=fx_susdcnh', headers={'Referer': 'https://finance.sina.com.cn'})
                raw_s = ur3.urlopen(req, timeout=10).read().decode('gbk')
                parts = raw_s.split('"')[1].split(',')
                raw['usdcnh'] = {'value': round(float(parts[5]), 4), 'date': datetime.now().strftime('%Y-%m-%d'), 'history': []}
                print("  [FALLBACK] USDCNH 用 Sina 现价（无历史）")
            except Exception as ex:
                print(f"  [WARN] USDCNH Sina 兜底失败: {ex}")
    except Exception as e:
        print(f"  [WARN] macro_data.json 兜底失败: {e}")

    # 方案A：DXY/USDCNH 本地逐日累加历史（Sina 实时值双机可取，自愈真实分位）
    # 在 final 当前值确定后追加；东财历史不足 20 点时 main 评分改用本地累加历史算分位
    for key in ACCUM_KEYS:
        rec = raw.get(key)
        if rec and rec.get('value') is not None:
            append_accum_hist(key, rec['value'], rec.get('date') or datetime.now().strftime('%Y-%m-%d'))

    # 持久化 DXY/USDCNH 累加历史（修复根因：data/ 被 gitignore 未跟踪，
    # 跨机/部署 git reset 会清空 → 永远到不了20点 → 危险分恒为阈值假值。
    # 改为强制跟踪 + 每次追加后 git 提交，双机经 git 共享、自愈合到真实分位）
    try:
        import subprocess as _sp
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _sp.run('git add data/dxy_hist.json data/usdcnh_hist.json',
                 shell=True, cwd=_root, capture_output=True, timeout=30)
        _sp.run('git -c user.name=九宝量化 -c user.email=hh@local commit -m '
                 '"data: 累加DXY/USDCNH历史(方案A自愈真实分位)" '
                 'data/dxy_hist.json data/usdcnh_hist.json',
                 shell=True, cwd=_root, capture_output=True, timeout=60)
    except Exception:
        pass

    indicators = {}
    for key, meta in REGISTRY.items():
        rec = raw.get(key)
        if not rec or rec.get('value') is None:
            print(f"  [MISS] {meta['name']} 无数据")
            indicators[key] = {**meta, 'value': None, 'date': '', 'percentile': None,
                               'trend': 'flat', 'score': None, 'level': None}
            continue
        val = rec['value']
        hist = rec.get('history') or []
        # DXY/USDCNH：东财历史不足时改用本地累加历史（方案A 自愈真实分位）
        if key in ACCUM_KEYS and len(hist) < 20:
            _acc = accum_history_values(key)
            if _acc:
                hist = _acc
        pct = percentile(val, hist) if len(hist) >= 20 else None
        tr = trend_of(hist + [val] if val not in (hist[-1:] or [None]) else hist, meta['freq']) if hist else 'flat'
        # 危险分
        if pct is not None:
            score = pct if meta['dir'] == 'high_bad' else round(100 - pct, 1)
        else:
            score = fallback_score(key, val)
        level = None
        if score is not None:
            level = 2 if score >= 70 else (1 if score >= 40 else 0)
        indicators[key] = {
            **meta,
            'value': val,
            'date': rec.get('date', ''),
            'percentile': pct,
            'trend': tr,
            'score': score,
            'level': level,
            'hist_n': len(hist),
        }

    result = {
        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'indicators': indicators,
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, 'crisis_data.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 50)
    print(f"已保存: {path}")
    ok = sum(1 for v in indicators.values() if v['value'] is not None)
    print(f"有效指标: {ok}/{len(REGISTRY)}")
    print("\n--- 指标摘要（值 | 分位 | 危险分 | 趋势）---")
    for key, v in indicators.items():
        if v['value'] is None:
            print(f"  ✗ {v['name']}: 缺失")
            continue
        pct = f"{v['percentile']}%" if v['percentile'] is not None else "阈值"
        print(f"  · {v['name']:<12} {v['value']:>10} | 分位{pct:>6} | 危险{v['score']:>4} | {v['trend']}")


if __name__ == '__main__':
    try:
        from fetch_logger import record_success, record_failure
    except Exception:
        record_success = record_failure = lambda *a, **k: None
    try:
        main()
        record_success(__file__)
    except Exception as e:
        record_failure(__file__, str(e))
        raise
