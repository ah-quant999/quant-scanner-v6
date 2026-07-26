"""
盘中扫描统一入口 — 带错误追踪，失败步骤写入 .fetch_errors.json
用法: python run_intraday_scan.py
     python run_intraday_scan.py --skip-standalone   # 跳过独立页面更新
     python run_intraday_scan.py --only-scan          # 只跑数据获取，不更新数据注入和独立页
"""
import subprocess, json, os, sys, time, argparse
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ERROR_FILE = os.path.join(BASE, 'data', '.fetch_errors.json')

# 2026-07-23：NT/盘中数据(异动/ETF/日历)、ETF资金与涨停联动均来自 akshare/东方财富(中国源)。
# 美区云端 runner 抓中国源网络不稳(软失败→部署陈旧数据)，故改由双机(小九/阿狸咪)在中国网络
# 抓取并 push main；云端设 CLOUD_RUNNER=true 时跳过这三步，只 git pull 复用双机数据。
CLOUD = os.environ.get('CLOUD_RUNNER') == 'true'
CLOUD_SKIP_STEPS = {'盘中数据NT', 'ETF资金', '涨停联动'}

STEPS = [
    ('scanner.py watch',      [sys.executable, 'scanner.py', 'watch']),
    ('涨跌家数',               [sys.executable, 'fetch_up_down_stats.py']),
    ('盘中数据NT',             [sys.executable, 'fetch_nt_data.py']),
    ('概念排行',               [sys.executable, 'fetch_concept_ranking.py']),
    ('板块资金',               [sys.executable, 'fetch_sector_fund_flow.py']),
    ('ETF资金',                [sys.executable, 'fetch_nt_data.py', '--etf-only']),
    ('市场快报',               [sys.executable, 'fetch_market_alerts.py']),
    # 涨停联动：akshare 中国源，云端跳过改由双机供
    ('涨停联动',               [sys.executable, 'fetch_limit_up_heatmap.py']),
    # 成交金额历史 + 两融余额：盘中必须刷新，否则曲线图/卡片会显示0或 stale
    ('成交历史',               [sys.executable, 'fetch_sh_sz_history.py']),
    ('两融余额',               [sys.executable, 'fetch_margin.py']),
]

def _sector_has_industry(base):
    """【2026-07-13新增】语义校验：板块资金产出必须含行业数据(type='行业')。
    否则前端只算行业净额会显示 0.0亿（主力板块/板块资金三合一卡）。"""
    import json as _json
    fp = os.path.join(base, 'data', 'sector_fund_flow.json')
    if not os.path.exists(fp):
        return False
    try:
        with open(fp, 'r', encoding='utf-8') as f:
            d = _json.load(f)
        for s in d.get('sectors_in', []) + d.get('sectors_out', []) + d.get('top_list', []):
            if s.get('type') == '行业':
                return True
        return False
    except Exception:
        return False

def run():
    parser = argparse.ArgumentParser(description='盘中数据扫描')
    parser.add_argument('--skip-standalone', action='store_true', help='跳过独立页面更新')
    parser.add_argument('--only-scan', action='store_true', help='只跑数据获取，不更新数据注入和独立页')
    args = parser.parse_args()
    
    errors = []
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # ── scanner.py watch 单步超时加长到 900s (273只股票@~2s需 500+s，旧 300s 必超时中断 → watch_result.json 2天未更新) ──
    _STEP_TIMEOUTS = {
        'scanner.py watch': 900,
        '涨跌家数': 180,
        '盘中数据NT': 180,
        '概念排行': 180,
        '板块资金': 360,
        'ETF资金': 180,
        '市场快报': 180,
        '涨停联动': 180,
        '成交历史': 180,
        '两融余额': 180,
    }
    for name, cmd in STEPS:
        if CLOUD and name in CLOUD_SKIP_STEPS:
            print(f'[{datetime.now().strftime("%H:%M:%S")}] ⊘ {name} 跳过（云端模式：NT/ETF 由双机供，git pull 复用 main 数据）')
            continue
        print(f'\n[{datetime.now().strftime("%H:%M:%S")}] ▶ {name}...')
        # 块内统一用 retries 控制重试，避免 continue/嵌套混乱
        r = None
        try:
            r = subprocess.run(cmd, cwd=BASE,
                             capture_output=True, text=True, timeout=_STEP_TIMEOUTS.get(name, 300))
        except subprocess.TimeoutExpired:
            print(f'  ❌ {name} 超时')
            errors.append({'step': name, 'time': now, 'error': '超时'})
            continue
        except Exception as e:
            print(f'  ❌ {name} 异常: {e}')
            errors.append({'step': name, 'time': now, 'error': str(e)[:200]})
            continue

        # 语义校验：板块资金必须含行业数据，否则视为失败
        semantic_ok = True
        if r.returncode != 0:
            semantic_ok = False
        elif name == '板块资金' and not _sector_has_industry(BASE):
            semantic_ok = False

        if semantic_ok:
            print(f'  ✅ {name} 完成')
            continue

        # 失败：收集错误
        err_msg = r.stderr.strip()[-200:] if (r and r.stderr) else f'exit code {r.returncode}'
        print(f'  ❌ {name} 失败: {err_msg}')
        errors.append({'step': name, 'time': now, 'error': err_msg})

        # 可重试条件：网络错误 或 板块资金行业数据缺失
        need_retry = ('DNS' in err_msg or '502' in err_msg
                      or 'timeout' in err_msg.lower() or 'timed out' in err_msg.lower()
                      or '行业数据' in err_msg)
        if need_retry:
            print(f'  🔄 可重试错误，60秒后重试...')
            time.sleep(60)
            try:
                r2 = subprocess.run(cmd, cwd=BASE,
                                   capture_output=True, text=True, timeout=300)
            except Exception as e2:
                print(f'  ❌ {name} 重试异常: {e2}')
                continue
            retry_ok = (r2.returncode == 0)
            if name == '板块资金':
                retry_ok = retry_ok and _sector_has_industry(BASE)
            if retry_ok:
                print(f'  ✅ {name} 重试成功（含行业数据）')
                # 移除本次步骤的错误记录
                errors[:] = [e for e in errors if e['step'] != name]
                continue
            else:
                print(f'  ❌ {name} 重试仍失败')
    
    # 保存错误记录
    if errors:
        with open(ERROR_FILE, 'w', encoding='utf-8') as f:
            json.dump({'last_scan': now, 'errors': errors}, f, ensure_ascii=False, indent=2)
        print(f'\n⚠️ {len(errors)} 个步骤失败，已记录到 {ERROR_FILE}')
        return 1
    else:
        # 清除之前的错误
        if os.path.exists(ERROR_FILE):
            os.remove(ERROR_FILE)
        print('\n✅ 全部步骤成功')
    
    # 数据获取完成后，更新数据注入 + 独立页面
    if not args.only_scan and not args.skip_standalone:
        print('\n' + '='*50)
        print('▶ 自动更新独立页面并部署')
        print('='*50)
        try:
            r = subprocess.run(
                [sys.executable, 'refresh_standalone_and_deploy.py'],
                cwd=BASE, capture_output=True, text=True, timeout=600
            )
            if r.returncode == 0:
                print('  ✅ 独立页面更新+部署完成')
            else:
                print(f'  ⚠️ 独立页面更新失败: {r.stderr[-200:]}')
                print('  （数据获取已成功，独立页面更新失败不影响主流程）')
        except Exception as e:
            print(f'  ⚠️ 独立页面更新异常: {e}')
    
    return 0

if __name__ == '__main__':
    # 非交易日（周末 + A股法定假日）跳过盘中扫描，避免休市日空跑抓行情
    try:
        from is_trading_day import is_trading_day as _itd
    except Exception:
        _itd = None
    if _itd is not None and not _itd():
        import datetime as _dt
        _w = _dt.date.today().weekday()
        _why = "周末" if _w >= 5 else "法定假日"
        print("⏭️ 非交易日（%s），盘中扫描跳过" % _why)
        sys.exit(0)
    sys.exit(run())
