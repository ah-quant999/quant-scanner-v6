"""
生成三线共振历史数据（从2026-06-01开始）
- 处理history数组中的重复日期（使用最后一次出现）
- 历史日期：从history数组读取
- 今天：从顶层字段读取
- 缺失pct_chg自动从新浪日K线API补全
"""
import json
import os
import urllib.request
from datetime import datetime, timedelta

# 新浪日K线缓存（symbol → [{day, close}]）
_SINA_CACHE = {}

# 加载交易日历
_CALENDAR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'important_calendar.json')
_HOLIDAYS = set()
_ADJUSTED = set()

def _load_calendar():
    global _HOLIDAYS, _ADJUSTED
    if _HOLIDAYS:
        return
    try:
        with open(_CALENDAR_PATH, 'r', encoding='utf-8') as f:
            cal = json.load(f)
        _HOLIDAYS = set(cal.get('holidays', {}).keys())
        _ADJUSTED = set(cal.get('adjusted_workdays', {}).keys())
    except Exception:
        pass

def is_trading_day(dt):
    """判断是否A股交易日（跳过周末和法定假期，含调休上班日）"""
    _load_calendar()
    ds = dt.strftime('%Y-%m-%d')
    # 调休上班日优先（即使是周末也开市）
    if ds in _ADJUSTED:
        return True
    # 周末
    if dt.weekday() >= 5:
        return False
    # 法定假期
    if ds in _HOLIDAYS:
        return False
    return True

def _fetch_stock_close_map(code):
    """从日K线API获取该股票全部可用收盘价，返回 {date_str: close}"""
    market_map = {'sh_': 'sh', 'sz_': 'sz', 'bj_': 'bj', 'hk_': 'hk'}
    prefix = ''
    for p in market_map:
        if code.startswith(p):
            prefix = market_map[p]
            code_short = code[len(p):]
            break
    if not prefix:
        return {}

    # 港股用腾讯API
    if prefix == 'hk':
        cache_key = f'hk_{code_short}_close'
        if cache_key not in _SINA_CACHE:
            try:
                url = f'http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=hk{code_short},day,,,320,qfq'
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                resp = urllib.request.urlopen(req, timeout=10)
                data = json.loads(resp.read().decode('utf-8'))
                klines = data.get('data', {}).get(f'hk{code_short}', {}).get('day', [])
                _SINA_CACHE[cache_key] = {k[0]: float(k[2]) for k in klines}
            except Exception:
                _SINA_CACHE[cache_key] = {}
        return _SINA_CACHE[cache_key]

    # A股用新浪API
    symbol = f'{prefix}{code_short}'
    cache_key = f'{symbol}_close'
    if cache_key not in _SINA_CACHE:
        try:
            url = f'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={symbol}&scale=240&ma=no&datalen=320'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read().decode('utf-8'))
            _SINA_CACHE[cache_key] = {d['day']: float(d['close']) for d in data}
        except Exception:
            _SINA_CACHE[cache_key] = {}
    return _SINA_CACHE[cache_key]

def _fetch_day_pct_chg(code, date_str):
    """从新浪/Tencent日K线API获取指定日期涨跌幅。返回 float 或 None"""
    market_map = {'sh_': 'sh', 'sz_': 'sz', 'bj_': 'bj', 'hk_': 'hk'}
    prefix = ''
    for p in market_map:
        if code.startswith(p):
            prefix = market_map[p]
            code_short = code[len(p):]
            break
    if not prefix:
        return None

    # 港股用腾讯API
    if prefix == 'hk':
        cache_key = f'hk_{code_short}'
        if cache_key not in _SINA_CACHE:
            try:
                url = f'http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=hk{code_short},day,,,60,qfq'
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                resp = urllib.request.urlopen(req, timeout=10)
                data = json.loads(resp.read().decode('utf-8'))
                klines = data.get('data', {}).get(f'hk{code_short}', {}).get('day', [])
                _SINA_CACHE[cache_key] = klines
            except Exception:
                _SINA_CACHE[cache_key] = []
        klines = _SINA_CACHE[cache_key]
        for i, k in enumerate(klines):
            if k[0] == date_str and i > 0:
                prev_close = float(klines[i - 1][2])
                close = float(k[2])
                return round((close - prev_close) / prev_close * 100, 2)
        return None

    # A股用新浪API
    symbol = f'{prefix}{code_short}'
    if symbol not in _SINA_CACHE:
        try:
            url = f'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={symbol}&scale=240&ma=no&datalen=60'
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read().decode('utf-8'))
            _SINA_CACHE[symbol] = data
        except Exception:
            _SINA_CACHE[symbol] = []
    data = _SINA_CACHE[symbol]
    for i, d in enumerate(data):
        if d.get('day') == date_str and i > 0:
            prev_close = float(data[i - 1]['close'])
            close = float(d['close'])
            return round((close - prev_close) / prev_close * 100, 2)
    return None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_HTML = os.path.join(BASE_DIR, 'index_master.html')
GOLD_POOL_FILE = os.path.join(BASE_DIR, 'data/gold_pool.json')
OUTPUT_FILE = os.path.join(BASE_DIR, 'data/triple_resonance_history.json')
START_DATE = '2026-06-01'
END_DATE = datetime.now().strftime('%Y-%m-%d')

def read_gold_pool(file_path):
    """从gold_pool.json读取数据"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取GOLD_POOL失败: {e}")
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
        '金钻_起涨': get_signal('金钻_起涨'),
        '四量图_机构变红': get_signal('四量图_机构变红'),
        '上涨趋势': get_signal('上涨趋势')
    }
    
    signal_count = sum(1 for v in signals.values() if v)
    return signals, signal_count

def generate_snapshots(gold_pool):
    snapshots = {}
    stocks = gold_pool.get('stocks', {})
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 构建每只股票的每日信号状态（处理重复日期）
    stock_daily = {}  # {code: {date: data}}
    
    for code, data in stocks.items():
        stock_daily[code] = {}
        seen_dates = {}  # {date: index_in_array}
        
        for idx, item in enumerate(data.get('history', [])):
            item_date = item.get('date', '')
            if not item_date:
                continue
            
            # 检查信号字段
            signals = {
                '缠论买_日K': item.get('缠论买_日K', False),
                '金钻_起涨': item.get('金钻_起涨', False),
                '四量图_机构变红': item.get('四量图_机构变红', False),
                '上涨趋势': item.get('上涨趋势', False)
            }
            signal_count = sum(1 for v in signals.values() if v)
            
            # 如果日期重复，使用最后一次（覆盖）
            stock_daily[code][item_date] = {
                'signals': signals,
                'signal_count': signal_count,
                'close': item.get('close', 0),
                'pct_chg': item.get('pct_chg', 0)
            }
    
    # 生成每日快照
    current = datetime.strptime(START_DATE, '%Y-%m-%d')
    end = datetime.strptime(END_DATE, '%Y-%m-%d')
    
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        
        if is_trading_day(current):  # 跳过周末和法定假期
            daily_stocks = []
            
            # 当日数据不读历史，统一由WATCH_DATA+SCAN_DATA补充（避免GOLD_POOL历史残留假数据）
            if date_str != today:
                for code, data in stocks.items():
                    use_data = None
                    
                    if date_str in stock_daily.get(code, {}):
                        # 有当日实际数据才用
                        use_data = stock_daily[code][date_str]
                    # 删掉fallback逻辑：无当日数据则跳过，避免用旧数据填充假新增/假退出
                    
                    if use_data and use_data['signal_count'] >= 3:
                        # 计算连续共振天数
                        consecutive = 0
                        for d in reversed(sorted(stock_daily.get(code, {}).keys())):
                            if d <= date_str:
                                if stock_daily[code][d]['signal_count'] >= 3:
                                    consecutive += 1
                                else:
                                    break
                        daily_stocks.append({
                            'code': code,
                        'name': data.get('name', ''),
                        'close': use_data['close'],
                        'pct_chg': use_data['pct_chg'],
                        '缠论买_日K': use_data['signals']['缠论买_日K'],
                        '金钻_起涨': use_data['signals']['金钻_起涨'],
                        '四量图_机构变红': use_data['signals']['四量图_机构变红'],
                        '上涨趋势': use_data['signals']['上涨趋势'],
                        'signal_count': use_data['signal_count'],
                        'score': use_data.get('score', use_data['signal_count'] * 3),
                        'days_in_resonance': consecutive,
                        'enter_date': data.get('enter_date', ''),
                        'duration_days': data.get('duration_days', 0)
                    })
            
            snapshots[date_str] = daily_stocks
            print(f"  {date_str}: {len(daily_stocks)}只")
        
        current += timedelta(days=1)
    
    return snapshots

def main():
    print("=== 生成三线共振历史数据（修复版） ===\n")

    gold_pool = read_gold_pool(GOLD_POOL_FILE)
    if not gold_pool or 'stocks' not in gold_pool:
        print("错误：无法读取GOLD_POOL数据")
        return

    # 加载watch_data（精监三线共振数据，可能包含金池外的股票）
    watch_file = os.path.join(os.path.dirname(GOLD_POOL_FILE), 'watch_result.json')
    watch_data = None
    if os.path.exists(watch_file):
        with open(watch_file, 'r', encoding='utf-8') as f:
            watch_data = json.load(f)
        print(f"WATCH_DATA三线共振: {len(watch_data.get('triple_signals', []))}只")

    print(f"GOLD_POOL股票数: {len(gold_pool['stocks'])}")
    print(f"\n生成历史快照 ({START_DATE} ~ {END_DATE})...")

    snapshots = generate_snapshots(gold_pool)

    # 补充：将watch_data + scan_data中的三线共振股并入当天快照（当日唯一权威来源）
    def merge_triple_signals(source, source_name):
        if not source or not source.get('triple_signals'):
            return
        today = datetime.now()
        if is_trading_day(today):
            today_str = today.strftime('%Y-%m-%d')
            if today_str not in snapshots:
                snapshots[today_str] = []
            existing_codes = {s['code'].replace('sh_','').replace('sz_','').replace('hk_','') for s in snapshots[today_str]}
            added = 0
            for ts in source['triple_signals']:
                code = ts.get('code', '')
                code_normalized = code.replace('sh_','').replace('sz_','').replace('hk_','')
                if code_normalized in existing_codes:
                    continue
                snapshots[today_str].append({
                    'code': code,
                    'name': ts.get('name', ''),
                    'close': ts.get('close', 0),
                    'pct_chg': ts.get('pct_chg', 0),
                    '缠论买_日K': ts.get('缠论买_日K', False),
                    '金钻_起涨': ts.get('金钻_起涨', False),
                    '四量图_机构变红': ts.get('四量图_机构变红', False),
                    '上涨趋势': ts.get('上涨趋势', False),
                    'signal_count': ts.get('signal_count', 3),
                    'score': ts.get('score', ts.get('signal_count', 3) * 3),
                    'days_in_resonance': 1,
                    'enter_date': '',
                    'duration_days': 0
                })
                existing_codes.add(code_normalized)
                added += 1
            if added:
                print(f"  {today_str}: {source_name}补充 {added}只 → 共{len(snapshots[today_str])}只")

    merge_triple_signals(watch_data, 'WATCH')
    
    # 加载SCAN_DATA补充
    scan_file = os.path.join(os.path.dirname(GOLD_POOL_FILE), 'scan_result.json')
    scan_data = None
    if os.path.exists(scan_file):
        with open(scan_file, 'r', encoding='utf-8') as f:
            scan_data = json.load(f)
        print(f"SCAN_DATA三线共振: {len(scan_data.get('triple_signals', []))}只")
    merge_triple_signals(scan_data, 'SCAN')
    
    # 合并已有数据：仅保留超出生成范围的历史日期（如生成范围外的手动补充数据）
    # 生成范围内的日期以新数据为准（不用旧fallback数据覆盖）
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        kept = 0
        for date, data in existing.items():
            if date.startswith('_'):
                continue
            if date in snapshots:
                continue  # 已生成，以新数据为准
            dt = datetime.strptime(date, '%Y-%m-%d')
            if not is_trading_day(dt):
                continue
            snapshots[date] = data
            kept += 1
        print(f"加载已有数据: {len(existing)}个日期（保留{kept}个超范围日期）")
    
    # ═══════════════════════════════════════════════
    # 提取所有出现过的股票的价格历史（用于前端计算退出价/最高涨幅）
    # ═══════════════════════════════════════════════
    all_codes = set()
    for date, daily_stocks in snapshots.items():
        if date.startswith('_'): 
            continue
        for s in daily_stocks:
            all_codes.add(s['code'])
    
    print(f"\n提取价格历史: {len(all_codes)}只股票")
    price_history = {}
    supplemented = 0
    for code in all_codes:
        date_map = {}
        # 1. 优先从 gold_pool 提取完整历史
        if code in gold_pool.get('stocks', {}):
            stock_data = gold_pool['stocks'][code]
            for item in stock_data.get('history', []):
                item_date = item.get('date', '')
                if item_date:
                    date_map[item_date] = item.get('close', 0)
        # 2. 从 snapshots 补充（已退出 gold_pool 的老股票）
        for date, daily_stocks in snapshots.items():
            if date.startswith('_'):
                continue
            for s in daily_stocks:
                if s['code'] == code and s.get('close'):
                    if date not in date_map:
                        date_map[date] = s['close']
        # 3. 如果数据点太少（<5），从新浪API补充日K线
        if len(date_map) < 5:
            try:
                api_closes = _fetch_stock_close_map(code)
                for api_date, api_close in api_closes.items():
                    if api_date not in date_map:
                        date_map[api_date] = api_close
                if len(date_map) >= 5:
                    supplemented += 1
            except Exception:
                pass
        if date_map:
            price_history[code] = sorted([[d, c] for d, c in date_map.items()])
    
    snapshots['_stock_price_history'] = price_history
    print(f"  价格历史条目: {sum(len(v) for v in price_history.values())}条（新浪API补充: {supplemented}只）\n")
    
    # ═══════════════════════════════════════════════
    # 生成 _tracking_latest：每只历史追踪股的最新收盘价
    # ═══════════════════════════════════════════════
    # 先尝试保留已有数据，再补充新股票
    tracking_latest = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                old = json.load(f)
            old_tl = old.get('_tracking_latest', {})
            if old_tl and isinstance(old_tl, dict):
                tracking_latest = dict(old_tl)
        except Exception:
            pass
    
    # 从 gold_pool 获取所有历史追踪股的最新价格
    # 【2026-06-26修复】不再跳过已有条目，每次都用 gold_pool history 最新数据刷新
    updated_from_gp = 0
    for code, stock_data in gold_pool.get('stocks', {}).items():
        norm = code.replace('sh_', '').replace('sz_', '').replace('hk_', '').replace('bj_', '')
        hist = stock_data.get('history', [])
        if hist:
            latest_h = hist[-1]
            tracking_latest[norm] = {
                'name': stock_data.get('name', ''),
                'close': float(latest_h.get('close', 0) or 0),
                'pct_chg': float(latest_h.get('pct_chg', 0) or 0),
                'pct_chg_20d': 0,
                'update_time': datetime.now().strftime('%Y-%m-%d'),
                '_source': 'gold_pool'
            }
            updated_from_gp += 1
    print(f"  [gold_pool] 刷新: {updated_from_gp}只")
    
    # 【2026-06-26新增】从 scan_data.json 刷新最新价格（扫描器数据比 gold_pool 的 history[-1] 更新）
    scan_data_file = os.path.join(os.path.dirname(GOLD_POOL_FILE), 'scan_result.json')
    if os.path.exists(scan_data_file):
        try:
            with open(scan_data_file, 'r', encoding='utf-8') as f:
                scan_result = json.load(f)
            refreshed = 0
            # scan_result.results[] 包含全量扫描结果
            all_results = scan_result.get('results', [])
            # 也可能在 scan_data.json 中
            for item in all_results:
                code = (item.get('code', '') or '').replace('sh_', '').replace('sz_', '').replace('hk_', '').replace('bj_', '')
                if code and code in tracking_latest:
                    close = item.get('close', 0)
                    pct = item.get('pct_chg', 0)
                    try:
                        close = float(close)
                        pct = float(pct)
                    except (ValueError, TypeError):
                        continue
                    if close > 0:
                        tracking_latest[code] = {
                            'name': item.get('name', tracking_latest[code].get('name', '')),
                            'close': close,
                            'pct_chg': pct,
                            'pct_chg_20d': float(item.get('pct_chg_20d', 0) or 0),
                            'update_time': scan_result.get('scan_time', datetime.now().strftime('%Y-%m-%d')),
                            '_source': 'scan_result'
                        }
                        refreshed += 1
            if refreshed:
                print(f"  [scan_result] 刷新: {refreshed}只（最新收盘价）")
        except Exception as e:
            print(f"  [scan_result] 读取失败: {e}")
    
    # 补充 snapshots 中出现但不在 gold_pool 的股票
    for date, daily_stocks in snapshots.items():
        if date.startswith('_'):
            continue
        for s in daily_stocks:
            norm = s['code'].replace('sh_', '').replace('sz_', '').replace('hk_', '').replace('bj_', '')
            if norm not in tracking_latest:
                tracking_latest[norm] = {
                    'name': s.get('name', ''),
                    'close': float(s.get('close', 0) or 0),
                    'pct_chg': float(s.get('pct_chg', 0) or 0),
                    'pct_chg_20d': 0,
                    'update_time': date,
                    '_source': 'snapshot'
                }
    
    snapshots['_tracking_latest'] = tracking_latest
    print(f"  追踪股最近收盘价: {len(tracking_latest)}只\n")
    
    # 保存
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(snapshots, f, ensure_ascii=False, indent=2)
    
    print(f"\n历史数据已保存: {OUTPUT_FILE}")
    print(f"总日期数: {len(snapshots)}")
    
    # 统计
    total_stocks = set()
    for date, stocks in snapshots.items():
        if date.startswith('_'):  # 跳过元数据key
            continue
        for s in stocks:
            total_stocks.add(s['code'])
    print(f"出现过三线共振的股票总数: {len(total_stocks)}")
    print("\n=== 完成 ===")

if __name__ == '__main__':
    main()
