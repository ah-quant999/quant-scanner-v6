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

# ETF 分级分类规则：按优先级自上而下匹配，越靠前优先级越高
# 格式：(category_1, category_2, [keywords])
CATEGORY_RULES = [
    # 1) 商品 ETF（名称里常带跨境/行业词，优先判定）
    ('商品', '贵金属', ['黄金ETF', '白银ETF', '黄金', '白银']),
    ('商品', '能源', ['原油ETF', '油气ETF', '原油', '油气']),
    ('商品', '农产品', ['豆粕ETF', '农产品ETF', '豆粕']),
    ('商品', '有色金属', ['有色ETF', '稀土ETF', '有色金属', '稀土']),

    # 2) 跨境 ETF
    ('跨境', '港股', ['恒生', '港股', 'H股']),
    ('跨境', '美股', ['纳斯达克', '标普', '道琼斯', '纳指', '标普500']),
    ('跨境', '亚太', ['日经', '越南', '印度', '韩国', '东南亚']),
    ('跨境', '欧洲', ['德国', '法国', '英国', '欧洲']),
    ('跨境', '其他跨境', ['沙特', '新兴市场', '中概']),

    # 3) 宽基 ETF
    ('宽基', '大盘宽基', ['沪深300', '上证50', '深证100', '中证A50', '中证A500', 'MSCI中国A50']),
    ('宽基', '中盘宽基', ['中证500']),
    ('宽基', '小盘宽基', ['中证1000', '国证2000', '中证2000']),
    ('宽基', '双创宽基', ['创业板', '科创板', '双创', '科创100', '科创200']),
    ('宽基', '全市场宽基', ['中证800', '中证全指', '深证成指', '中小板', '中小盘']),

    # 4) 行业 ETF
    ('行业', '金融地产', ['银行', '券商', '证券', '保险', '地产', '金融科技']),
    ('行业', '科技', ['半导体', '芯片', '通信', '计算机', '电子', '5G', '人工智能', 'AI', '软件', '云计算', '大数据', '网络安全', '信创', '物联网', '工业互联网']),
    ('行业', '医药医疗', ['医药', '医疗', '创新药', '生物科技', '医疗器械', '中药', '疫苗', '精准医疗', '细胞治疗']),
    ('行业', '消费', ['酒ETF', '白酒', '食品饮料', '家电', '汽车', '农业', '养殖', '畜牧', '旅游', '酒店', '传媒', '游戏', '影视', '教育', '商贸零售', '电商']),
    ('行业', '周期资源', ['煤炭', '钢铁', '有色', '化工', '石油', '石化', '建材', '稀土', '矿产', '资源']),
    ('行业', '先进制造', ['机械', '电力设备', '新能源', '光伏', '储能', '锂电', '新能源车', '军工', '航天', '船舶', '机器人', '工业母机', '机床', '高端制造', '智能制造']),
    ('行业', '公用事业', ['电力', '交运', '运输', '环保', '水务', '公用事业']),
    ('行业', '基建地产', ['基建', '建筑', '建材', '房地产', '城镇化']),

    # 5) 策略 ETF（SmartBeta）
    ('策略', '红利股息', ['红利', '高股息', '股息']),
    ('策略', '低波', ['低波', '低波动']),
    ('策略', '质量价值成长', ['质量', '价值', '成长', '基本面']),
    ('策略', '等权', ['等权']),

    # 6) 主题 ETF（兜底，但仍做二级细分）
    ('主题', '红利主题', ['红利', '高股息', '股息']),
    ('主题', '科技主题', ['人工智能', 'AI', '机器人', '芯片', '半导体', '5G', '通信', '云计算', '大数据', '元宇宙', '区块链', '数字货币', '信创', '物联网']),
    ('主题', '新能源主题', ['新能源', '光伏', '储能', '锂电', '新能源车', '碳中和', '绿色电力', '环保']),
    ('主题', '医药主题', ['创新药', '生物科技', '医疗器械', '中药', '疫苗', '精准医疗', '细胞治疗', '养老', '健康']),
    ('主题', '消费主题', ['新消费', '国潮', '电商', '互联网', '养老', '健康', '旅游', '酒店', '游戏', '影视', '传媒']),
    ('主题', '资源主题', ['黄金', '白银', '原油', '油气', '有色', '稀土', '豆粕', '农产品', '资源']),
    ('主题', '跨境主题', ['港股科技', '中概互联', '恒生科技', '互联网']),
]


def classify_etf(name):
    """返回 (category_1, category_2)，按 CATEGORY_RULES 优先级匹配。"""
    for c1, c2, kws in CATEGORY_RULES:
        for kw in kws:
            if kw in name:
                return c1, c2
    return '主题', '其他主题'


def aggregate_categories(rows):
    """按 category_1 / category_2 聚合统计与榜单。"""
    from collections import defaultdict
    cat1_map = defaultdict(list)
    cat2_map = defaultdict(list)
    for r in rows:
        cat1_map[r['category_1']].append(r)
        cat2_map[(r['category_1'], r['category_2'])].append(r)

    def stats(sub_rows):
        up = sum(1 for x in sub_rows if x['pct'] > 0)
        down = sum(1 for x in sub_rows if x['pct'] < 0)
        flat = len(sub_rows) - up - down
        net = sum(x['main_net_inflow'] for x in sub_rows)
        active = sorted(sub_rows, key=lambda x: x['amount'], reverse=True)[:5]
        flow = sorted(sub_rows, key=lambda x: x['main_net_inflow'], reverse=True)
        inflow = flow[:5]
        outflow = flow[-5:][::-1]
        return {
            'count': len(sub_rows),
            'up': up, 'down': down, 'flat': flat,
            'net_inflow_yi': round(net / 1e8, 2),
            'top_active': active,
            'top_inflow': inflow,
            'top_outflow': outflow,
        }

    categories = {}
    for c1, c1_rows in cat1_map.items():
        sub_map = defaultdict(list)
        for r in c1_rows:
            sub_map[r['category_2']].append(r)
        subcategories = {c2: stats(sub_rows) for (c1_key, c2), sub_rows in cat2_map.items() if c1_key == c1}
        categories[c1] = {
            **stats(c1_rows),
            'subcategories': subcategories,
        }
    return categories


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
        c1, c2 = classify_etf(name)
        rows.append({
            'code': code,
            'name': name,
            'pct': round(pct, 2),
            'amount': int(amt),
            'main_net_inflow': int(net),
            'category_1': c1,
            'category_2': c2,
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

    # 兼容 v8 已下架面板「国家队ETF资金流向」渲染：需要 etfs 数组（与 top_active 同构）
    etfs_for_v8 = [{
        'code': x['code'],
        'name': x['name'],
        'type': x.get('category_1', '主题'),
        'price': 0.0,  # 盘中快照未保留价格，v8 当前不展示该字段
        'change_pct': x['pct'],
        'volume': 0,
        'amount': round(x['amount'] / 1e8, 3),  # v8 renderDelisted 以亿为单位展示成交额
        'amplitude': 0.0,
    } for x in top_active]

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
        },
        'categories': aggregate_categories(rows),
        'etfs': etfs_for_v8,
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
