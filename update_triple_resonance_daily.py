"""
每日更新三线共振快照（增量更新）
只更新今天的数据，不重新生成历史
"""
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_HTML = os.path.join(BASE_DIR, 'index_master.html')
GOLD_POOL_FILE = os.path.join(BASE_DIR, 'data/gold_pool.json')
WATCH_FILE = os.path.join(BASE_DIR, 'data/watch_result.json')
SCAN_FILE = os.path.join(BASE_DIR, 'data/scan_result.json')
SCAN_DATA_FILE = os.path.join(BASE_DIR, 'data/scan_data.json')
OUTPUT_FILE = os.path.join(BASE_DIR, 'data/triple_resonance_history.json')

def read_gold_pool(file_path):
    """从gold_pool.json读取数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取GOLD_POOL失败: {e}")
        return None

def read_watch_result(file_path):
    """从watch_result.json读取三线共振数据（补全GOLD_POOL可能遗漏的股票）"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取WATCH_RESULT失败: {e}")
        return None

def read_scan_result(file_path):
    """从scan_result.json读取三线共振数据（补全GOLD_POOL可能遗漏的股票）"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取SCAN_RESULT失败: {e}")
        return None

def read_scan_data(file_path):
    """从scan_data.json读取全量扫描数据（最可靠的价格源）"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取SCAN_DATA失败: {e}")
        return None

def get_latest_signals(data):
    """获取最新信号状态（和主页面逻辑一致）"""
    history = data.get('history', [])
    latest = history[-1] if history else {}
    
    def get_signal(key):
        val = latest.get(key)
        if val is None:
            val = data.get(key)
        return val or False
    
    signals = {
        '缠论买_日K': get_signal('缠论买_日K'),
        '金钻_黄柱': get_signal('金钻_黄柱'),
        '金钻_起涨': get_signal('金钻_起涨'),
        '四量图_机构变红': get_signal('四量图_机构变红'),
        '上涨趋势': get_signal('上涨趋势')
    }

    # 金钻信号 = 黄柱 OR 起涨 (与 scanner.py 第1507行一致)
    jz_signal = signals['金钻_黄柱'] or signals['金钻_起涨']
    signal_count = sum([signals['缠论买_日K'], jz_signal, signals['四量图_机构变红'], signals['上涨趋势']])
    return signals, signal_count

def normalize_code(code):
    """去掉前缀统一比较"""
    return (code or '').replace('sh_', '').replace('sz_', '').replace('hk_', '')

def main():
    print("=== 每日更新三线共振快照 ===")
    print(f"日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # 读取GOLD_POOL
    gold_pool = read_gold_pool(GOLD_POOL_FILE)
    # 同时读WATCH_RESULT（补全可能遗漏的股票）
    watch_result = read_watch_result(WATCH_FILE)
    # 同时读SCAN_RESULT（补全可能遗漏的股票）
    scan_result = read_scan_result(SCAN_FILE)
    # 读全量扫描数据（最可靠的价格源，用于追踪股最新价）
    scan_data = read_scan_data(SCAN_DATA_FILE)

    if not gold_pool and not watch_result and not scan_result:
        print("错误：无法读取任何数据源")
        return

    # 用dict去重，key=normalize_code
    today_stocks_map = {}

    # 1. 从GOLD_POOL提取
    if gold_pool and 'stocks' in gold_pool:
        for code, data in gold_pool['stocks'].items():
            signals, signal_count = get_latest_signals(data)
            if signal_count >= 3:
                latest = data.get('history', [])
                latest_item = latest[-1] if latest else {}
                norm = normalize_code(code)
                today_stocks_map[norm] = {
                    'code': code,
                    'name': data.get('name', ''),
                    'close': latest_item.get('close', data.get('close', 0)),
                    'pct_chg': latest_item.get('pct_chg', data.get('pct_chg', 0)),
                    '缠论买_日K': signals['缠论买_日K'],
                    '金钻_起涨': signals['金钻_起涨'],
                    '金钻_黄柱': signals['金钻_黄柱'],
                    '四量图_机构变红': signals['四量图_机构变红'],
                    '上涨趋势': signals['上涨趋势'],
                    'signal_count': signal_count,
                    'enter_date': data.get('enter_date', ''),
                    'duration_days': data.get('duration_days', 0),
                    '_source': 'GOLD'
                }
        print(f"GOLD_POOL提取: {len([k for k,v in today_stocks_map.items() if v.get('_source')=='GOLD'])}只")

    # 2. 从WATCH_RESULT补充（信号数>=3且不在GOLD_POOL中的）
    if watch_result and 'triple_signals' in watch_result:
        for s in watch_result['triple_signals']:
            sig_cnt = s.get('signal_count', 0)
            if sig_cnt >= 3:
                norm = normalize_code(s.get('code', ''))
                # 只在不存在或信号数更高时更新
                existing = today_stocks_map.get(norm)
                if not existing or (sig_cnt > existing.get('signal_count', 0)):
                    today_stocks_map[norm] = {
                        'code': s.get('code', ''),
                        'name': s.get('name', ''),
                        'close': s.get('close', s.get('latest', {}).get('close', 0)),
                        'pct_chg': s.get('pct_chg', 0),
                        '缠论买_日K': s.get('缠论买_日K', False),
                        '金钻_起涨': s.get('金钻_起涨', False) or s.get('金钻_黄柱', False),
                        '四量图_机构变红': s.get('四量图_机构变红', False),
                        '上涨趋势': s.get('上涨趋势', False),
                        'signal_count': sig_cnt,
                        'enter_date': '',
                        'duration_days': 0,
                        '_source': 'WATCH'
                    }
        watch_added = len([k for k, v in today_stocks_map.items() if v.get('_source') == 'WATCH'])
        print(f"WATCH_RESULT补充: {watch_added}只（新增/升级）")

    # 3. 从SCAN_RESULT补充 — 从 results 中筛选三线共振=True 的股票
    if scan_result and 'results' in scan_result:
        for s in scan_result['results']:
            if s.get('三线共振'):  # 扫描结果中的三线共振标记
                sig_cnt = s.get('signal_count', 0)
                if sig_cnt >= 3:
                    norm = normalize_code(s.get('code', ''))
                    existing = today_stocks_map.get(norm)
                    if not existing or (sig_cnt > existing.get('signal_count', 0)):
                        today_stocks_map[norm] = {
                            'code': s.get('code', ''),
                            'name': s.get('name', ''),
                            'close': s.get('close', s.get('latest', {}).get('close', 0)),
                            'pct_chg': s.get('pct_chg', 0),
                            '缠论买_日K': s.get('缠论买_日K', False),
                            '金钻_起涨': s.get('金钻_起涨', False) or s.get('金钻_黄柱', False),
                            '四量图_机构变红': s.get('四量图_机构变红', False),
                            '上涨趋势': s.get('上涨趋势', False),
                            'signal_count': sig_cnt,
                            'enter_date': '',
                            'duration_days': 0,
                            '_source': 'SCAN'
                        }
        scan_added = len([k for k, v in today_stocks_map.items() if v.get('_source') == 'SCAN'])
        print(f"SCAN_RESULT补充: {scan_added}只（新增/升级）")

    today_stocks = list(today_stocks_map.values())

    # 周末非交易日，跳过不写入
    today_dt = datetime.now()
    if today_dt.weekday() >= 5:
        print(f"今天 {today_dt.strftime('%Y-%m-%d')} 是周末（非交易日），跳过更新")
        return
    # 非交易时间（9:30前）跳过不写入，避免用昨日数据污染今日
    current_hour = today_dt.hour + today_dt.minute / 60
    if current_hour < 9.5:
        print(f"当前 {today_dt.strftime('%H:%M')}，尚未开盘（开盘时间 9:30），跳过更新")
        return
    today_str = today_dt.strftime('%Y-%m-%d')
    
    print(f"今天三线共振: {len(today_stocks)}只")
    for s in today_stocks:
        print(f"  {s['code']} {s['name']}: {s['signal_count']}/4")
    
    # 读取已有历史
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = {}
    
    # 更新今天的数据
    history[today_str] = today_stocks
    
    # ═══════════════════════════════════════════════
    # 更新所有追踪股的最近收盘价 (_tracking_latest)
    # 数据源优先级: scan_data(最全) > watch_result > gold_pool
    # 保留已有_tracking_latest中的条目（来自完整gold_pool），追加新增股
    # ═══════════════════════════════════════════════
    tracking_latest = {}
    old_tl = history.get('_tracking_latest', {})
    if old_tl and isinstance(old_tl, dict):
        tracking_latest = dict(old_tl)  # 保留已有完整条目

    # 收集所有历史出现过的股票代码
    all_codes = set()
    for date_key in history:
        if date_key.startswith('_'):
            continue  # 跳过特殊键
        for entry in history[date_key]:
            if isinstance(entry, dict):
                all_codes.add(normalize_code(entry['code']))
            elif isinstance(entry, str):
                all_codes.add(normalize_code(entry))
            else:
                print(f"警告：跳过未知格式的条目 {type(entry)}: {entry}")

    print(f"  历史追踪股共: {len(all_codes)}只")

    # === 源1: scan_data.json（最可靠，包含全量扫描的最新价）===
    if scan_data:
        sd_stocks = scan_data.get('stocks', scan_data.get('data', []))
        if isinstance(sd_stocks, list) and len(sd_stocks) > 0:
            for item in sd_stocks:
                if not isinstance(item, dict):
                    continue
                # 支持多种字段名格式
                item_code = normalize_code(item.get('code', item.get('Code', '')))
                if item_code and item_code in all_codes:
                    close = item.get('close', item.get('Close', 0))
                    pct_chg = item.get('pct_chg', item.get('pctChg', 0))
                    name = item.get('name', item.get('Name', ''))
                    try:
                        close = float(close)
                        pct_chg = float(pct_chg)
                    except (ValueError, TypeError):
                        continue
                    tracking_latest[item_code] = {
                        'name': name,
                        'close': close,
                        'pct_chg': round(pct_chg, 2),
                        'pct_chg_20d': 0,
                        'update_time': today_str,
                        '_source': 'scan_data'
                    }
            from_scan = sum(1 for k,v in tracking_latest.items() if v.get('_source') == 'scan_data')
            print(f"  [源1-scan_data] 匹配: {from_scan}只")

    # === 源2: watch_result（补充 scan_data 中没有的）===
    remaining_codes = all_codes - set(tracking_latest.keys())
    if watch_result and remaining_codes:
        all_signals = (watch_result.get('triple_signals', []) +
                       watch_result.get('double_signals', []))
        for code in remaining_codes:
            for s in all_signals:
                if normalize_code(s.get('code', '')) == code:
                    tracking_latest[code] = {
                        'name': s.get('name', ''),
                        'close': float(s.get('close', 0) or 0),
                        'pct_chg': float(s.get('pct_chg', 0) or 0),
                        'pct_chg_20d': float(s.get('pct_chg_20d', 0) or 0),
                        'update_time': watch_result.get('scan_time', ''),
                        '_source': 'watch'
                    }
                    break
        from_watch = sum(1 for k,v in tracking_latest.items() if v.get('_source') == 'watch')
        print(f"  [源2-watch] 补充: {from_watch}只")

    # === 源3: gold_pool（兜底，主要是港股）===
    remaining_codes = all_codes - set(tracking_latest.keys())
    if gold_pool and remaining_codes and 'stocks' in gold_pool:
        for code in remaining_codes:
            for gp_code, gp_data in gold_pool['stocks'].items():
                if normalize_code(gp_code) == code:
                    hist = gp_data.get('history', [])
                    latest_h = hist[-1] if hist else {}
                    tracking_latest[code] = {
                        'name': gp_data.get('name', ''),
                        'close': float(latest_h.get('close', gp_data.get('close', 0)) or 0),
                        'pct_chg': float(latest_h.get('pct_chg', gp_data.get('pct_chg', 0)) or 0),
                        'pct_chg_20d': 0,
                        'update_time': today_str,
                        '_source': 'gold'
                    }
                    break
        from_gold = sum(1 for k,v in tracking_latest.items() if v.get('_source') == 'gold')
        print(f"  [源3-gold_pool] 兜底: {from_gold}只")

    still_missing = all_codes - set(tracking_latest.keys())
    if still_missing:
        print(f"  ⚠️ 仍缺失 {len(still_missing)}只: {list(still_missing)[:5]}{'...' if len(still_missing)>5 else ''}")

    print(f"  追踪股最近收盘价总计: {len(tracking_latest)}只")
    
    history['_tracking_latest'] = tracking_latest if tracking_latest else {}
    
    # 保存
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    
    print(f"\n快照已保存: {OUTPUT_FILE}")
    print(f"历史日期数: {len(history)}")
    print("\n=== 完成 ===")

if __name__ == '__main__':
    main()
