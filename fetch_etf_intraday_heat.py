#!/usr/bin/env python3
"""
fetch_etf_intraday_heat.py
用途：抓取全市场 ETF 实时行情（东方财富 fund_etf_spot_em），生成盘中「ETF资金热度」榜。
数据去向：data/etf_intraday_heat.json → update_data_v2.py 注入 ETF_INTRADAY_HEAT → index_master.html 渲染「📊 ETF资金热度」卡片（T+0 盘中）。
依赖：akshare(fund_etf_spot_em)
时效：盘中实时（T+0），与华宝证券盘中版等价；弥补 ETF净申购(ETF_SUBSCRIPTION) 结构性 T+1 的空窗。
字段：top_active=按成交额排序TOP10（最活跃ETF）；top_inflow=按主力净流入净额排序TOP10（资金流入榜）；summary=全市场涨跌家数+主力净流入合计。
注意：货币/债券类 ETF 已排除，仅保留股票型/跨境/商品等权益类 ETF，对齐华宝「股票型ETF」口径。
"""
import akshare as ak
import json
import os
import time
from datetime import datetime, timedelta

DATA_DIR = 'data'
os.makedirs(DATA_DIR, exist_ok=True)

# 排除非权益类 ETF（货币/债券），对齐华宝「股票型ETF」口径
EXCLUDE_KW = ['货币', '国债', '国开', '政金', '城投', '信用', '短融', '存单', '理财',
              '转债', '短债', '中债', '企业债', '地方债', '金融债', '同业']

def is_equity_etf(name):
    for kw in EXCLUDE_KW:
        if kw in name:
            return False
    return True

def safe_float(v):
    """NaN/None → 0.0，避免 int(NaN) 崩溃。"""
    try:
        f = float(v)
        if f != f:  # NaN
            return 0.0
        return f
    except Exception:
        return 0.0

def main():
    print('🔵 抓取全市场 ETF 实时行情 (fund_etf_spot_em)...')
    try:
        df = ak.fund_etf_spot_em()
    except Exception as e:
        print('✗ 行情接口失败: ' + str(e))
        # 保留旧数据，不覆盖
        return
    if df is None or len(df) == 0:
        print('✗ 行情为空')
        return

    # 列名映射（兼容不同 akshare 版本）
    cols = list(df.columns)
    def col(*cands):
        for c in cands:
            if c in cols:
                return c
        return None
    c_code = col('代码')
    c_name = col('名称')
    c_pct  = col('涨跌幅')
    c_amt  = col('成交额')
    c_net  = col('主力净流入-净额')
    c_price = col('最新价')
    c_date = col('数据日期')
    c_time = col('更新时间')

    rows = []
    for _, r in df.iterrows():
        name = str(r.get(c_name, '') or '')
        if not is_equity_etf(name):
            continue
        # 货币ETF 最新价恒为 ~100，按价格剔除（比名称匹配更稳）
        try:
            price = safe_float(r.get(c_price, 0))
            if price >= 50:
                continue
        except Exception:
            pass
        try:
            code = str(r.get(c_code, ''))
            pct = safe_float(r.get(c_pct, 0))
            amt = safe_float(r.get(c_amt, 0))
            net = safe_float(r.get(c_net, 0))
        except Exception:
            continue
        rows.append({
            'code': code,
            'name': name,
            'pct': round(pct, 2),
            'amount': int(amt),
            'main_net_inflow': int(net),
        })

    # 排除成交额/净流入异常的（如 0）
    active = [x for x in rows if x['amount'] > 0]
    active.sort(key=lambda x: x['amount'], reverse=True)
    top_active = active[:10]

    flow = [x for x in rows if x['main_net_inflow'] != 0]
    flow.sort(key=lambda x: x['main_net_inflow'], reverse=True)
    top_inflow = flow[:10]
    top_outflow = flow[-10:][::-1]  # 净流出最多，按净流出绝对值从大到小

    up = sum(1 for x in rows if x['pct'] > 0)
    down = sum(1 for x in rows if x['pct'] < 0)
    flat = len(rows) - up - down
    net_total = sum(x['main_net_inflow'] for x in rows)

    update_time = ''
    try:
        if c_time:
            update_time = str(df.iloc[0][c_time])
            # 清理时区后缀 +08:00 与 ISO 的 T
            if '+08:00' in update_time:
                update_time = update_time.replace('+08:00', '')
            if 'T' in update_time:
                update_time = update_time.replace('T', ' ')
    except Exception:
        update_time = datetime.now().strftime('%Y-%m-%d %H:%M')

    data_date = (update_time or '')[:10] or datetime.now().strftime('%Y-%m-%d')

    # 维护历史榜单，计算“连续在榜天数”
    HISTORY_FILE = os.path.join(DATA_DIR, 'etf_intraday_heat_history.json')
    history = {}
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception:
            history = {}
    if not isinstance(history, dict):
        history = {}
    history[data_date] = {
        'inflow_codes': [x['code'] for x in top_inflow],
        'outflow_codes': [x['code'] for x in top_outflow],
    }
    # 只保留最近 60 天
    cutoff = (datetime.strptime(data_date, '%Y-%m-%d') - timedelta(days=60)).strftime('%Y-%m-%d')
    history = {k: v for k, v in history.items() if k >= cutoff}
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    def calc_streak(code, direction):
        d = datetime.strptime(data_date, '%Y-%m-%d')
        days = 0
        while True:
            key = d.strftime('%Y-%m-%d')
            entry = history.get(key, {})
            if code in entry.get(direction, []):
                days += 1
                d -= timedelta(days=1)
            else:
                break
        return days

    for x in top_inflow:
        x['streak'] = calc_streak(x['code'], 'inflow_codes')
    for x in top_outflow:
        x['streak'] = calc_streak(x['code'], 'outflow_codes')

    result = {
        'update_time': update_time or datetime.now().strftime('%Y-%m-%d %H:%M'),
        'data_date': data_date,
        'total': len(rows),
        'top_active': top_active,
        'top_inflow': top_inflow,
        'top_outflow': top_outflow,
        'summary': {
            'up': up, 'down': down, 'flat': flat,
            'net_inflow_yi': round(net_total / 1e8, 2),
        }
    }
    out = os.path.join(DATA_DIR, 'etf_intraday_heat.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print('  ✅ 已保存：' + out)
    print('  📊 权益类ETF ' + str(len(rows)) + ' 只 | 涨' + str(up) + '/跌' + str(down) + '/平' + str(flat))
    print('  💰 全市场ETF主力净流入 ' + str(round(net_total/1e8, 2)) + ' 亿')
    print('  🔥 最活跃TOP3: ' + '、'.join([x['name'] + ' ' + ('+%+.2f%%' % x['pct']) for x in top_active[:3]]))

if __name__ == "__main__":
    from fetch_logger import record_success, record_failure
    try:
        main()
        record_success(__file__)
    except Exception as e:
        record_failure(__file__, str(e))
        raise
