#!/usr/bin/env python3
# DO NOT DELETE: 核心调度脚本，所有定时任务的入口 (see DO_NOT_DELETE.md)
"""
batch_update.py — 九宝量化统一调度脚本
每个步骤独立超时 → 失败自动重试一次 → 汇总报告

流程：... → update_data_v2 → enhance_dist → deploy → ...
enhance_dist 负责注入 MAHORO_COVERAGE、同步 getScore()、同步逻辑详解页 HTML

用法：
  python batch_update.py pre_market     09:15 盘前（研报+maharo→全量扫描→增强→部署）
  python batch_update.py morning_scan   09:45 盘中快速扫描
  python batch_update.py morning_plus   10:30 扫描+三卡刷新（板块/ETF/AI速览）
  python batch_update.py morning_report 11:45 午间（研报+maharo→扫描→增强→部署）
  python batch_update.py afternoon      13:30/14:30/15:30/16:30 午后
  python batch_update.py close          周六 07:30 T+1全量（研报+maharo→全量fetch→扫描→增强→部署）
  python batch_update.py close_p1       17:30 收盘抓取第一批（研报+全量数据，龙虎榜除外）
  python batch_update.py close_p2       18:30 收盘扫描+生成（龙虎榜+scanner全量+生成）
  python batch_update.py close_deploy   19:30 收盘最终部署（注入+部署，数据已由p1/p2就绪）
  python batch_update.py backup         21:00 备份
"""

import subprocess
import sys
import time
import os
import concurrent.futures

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORKSPACE)

# 安全同步：彻底消除 autostash pull 的 stash-pop 冲突（data/ 双机重写根因）
from git_safe_sync import safe_pull  # noqa: E402

# 非交易日判断（周末 + A股法定假日 + 调休补班），用于休市日跳过抓行情
try:
    from is_trading_day import is_trading_day as _is_trading_day
    from is_trading_day import is_holiday as _is_holiday
except Exception:
    _is_trading_day = None
    _is_holiday = None

# 所有数据源每日执行，不再有每周限制
WEEKLY_ONLY_COMMANDS = set()
WEEKLY_RUN_WEEKDAY = 0  # 已废弃，所有任务每日执行

# 查找系统 Python 3.14（避免 managed Python 的 py_mini_racer 崩溃）
def _find_system_python():
    # 尝试 py launcher
    try:
        r = subprocess.run(
            ["py", "-3.14", "-c", "import sys; print(sys.executable)"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0:
            p = r.stdout.strip()
            if p and "workbuddy" not in p.lower():
                return p
    except Exception:
        pass
    # 常见路径兜底
    for c in [
        r"C:\Users\HH20210606\AppData\Local\Programs\Python\Python314\python.exe",
        r"C:\Python314\python.exe",
    ]:
        if os.path.exists(c):
            return c
    return sys.executable   # 找不到就用自己的

SYSTEM_PYTHON = _find_system_python()

# ──────────────────────────────────────────────────────────
# 模式定义：每个步骤 (命令, 超时秒数)
# ──────────────────────────────────────────────────────────
MODES = {
    "pre_market": {
        "desc": "盘前全量 (08:45)",
        "steps": [
            # 并行组：5 个 fetch 同时跑 → wall-time ~5min
            # 2026-07-20 改：前 5 步并行化 + 启动提前到 08:45，09:21 开盘前部署完毕
            [
                ("guanlan_extractor.py", 300),
                ("fetch_mahoro_signals.py --non-interactive", 120),
                ("fetch_sector_fund_flow.py", 120),
                # 2026-07-24 移除：fetch_market_fund_flow.py —— 该卡为「资金流向时间轴·长线盘后」专属，应只跑盘后 close_p1(18:30)，早晨跑会覆盖昨日数据造成误导
                ("fetch_concept_ranking.py", 120),
                ("fetch_market_alerts.py", 120),
                ("fetch_close_summary.py", 60),  # 2026-07-22 新增：15:00 收盘后汇总快照
            ],
            ("build_candidate_pool.py", 600),  # 2026-07-24: 300→600，外部源逐只拉取慢日(~6min)易超时→09:20静默失败根因
            ("scanner.py full", 600),
            ("generate_recommend.py", 120),
            # 2026-07-27 根因修复：盘前全量抓取后必须把新鲜中国源数据推 main，
            # 否则 deploy_now.py 的 safe_pull(reset) 会把 data/ 回退成 origin/main 陈旧版
            # —— 正是「08:45 跑了但网站仍 2-3 天前」反复发生的根因（post_close/close_p2 已修正，pre_market 漏了）。
            ("push_china_data.py", 120),
            ("update_data_v2.py", 300),
            ("enhance_dist.py", 30),
            ("refresh_standalone_and_deploy.py --skip-data --skip-deploy", 300),
            ("sync_check.py", 30),
            ("deploy_now.py --force", 180),
        ],
    },
    "morning_scan": {
        "desc": "盘中快速扫描 (09:45)",
        "steps": [
            ("fetch_overnight_brief.py --news-only", 90),
            ("scanner.py", 300),
            # 2026-07-27 根因修复：先推中国源数据，防 update_data_v2 的 safe_pull 回退陈旧版
            ("push_china_data.py", 90),
            ("update_data_v2.py", 300),
            ("enhance_dist.py", 30),
            ("refresh_standalone_and_deploy.py --skip-data --skip-deploy", 300),
            ("sync_check.py", 30),      # 坚果云同步检查
            ("deploy_now.py --force", 180),
        ],
    },
    "morning_plus": {
        "desc": "盘中扫描+三卡刷新 (10:30)",
        "steps": [
            ("fetch_overnight_brief.py --news-only", 90),
            ("fetch_sector_fund_flow.py", 120),
            ("fetch_etf_subscription.py", 120),
            ("fetch_market_alerts.py", 120),
            ("fetch_concept_ranking.py", 120),
            ("fetch_sector_rs.py", 90),
            ("fetch_limit_up_heatmap.py", 120),
            # 10:30 补充成交历史，避免午间金额曲线断崖
            ("fetch_sh_sz_history.py", 120),
            ("scanner.py", 300),
            # 2026-07-21 接入：三重选股盘中刷新（收盘前先给当日预览，close_p2 给最终版）
            ("triple_select_scan.py", 600),
            # 2026-07-27 根因修复：先推中国源数据，防 safe_pull 回退陈旧版
            ("push_china_data.py", 90),
            ("update_data_v2.py", 300),
            ("enhance_dist.py", 30),
            ("refresh_standalone_and_deploy.py --skip-data --skip-deploy", 300),
            ("sync_check.py", 30),      # 坚果云同步检查
            ("deploy_now.py --force", 180),
        ],
    },
    "morning_report": {
        "desc": "午间研报+扫描 (11:45)",
        "steps": [
            ("fetch_overnight_brief.py --news-only", 90),
            ("guanlan_extractor.py", 300),
            ("fetch_mahoro_signals.py --non-interactive", 120),
            ("scanner.py", 300),
            # 大盘资金/两融/成交历史需在午间刷新，避免盘中卡片显示0或 stale
            ("fetch_sh_sz_history.py", 120),
            ("fetch_margin.py", 120),
            ("fetch_concept_ranking.py", 180),
            ("fetch_market_alerts.py", 180),
            ("fetch_sector_fund_flow.py", 180),
            ("fetch_limit_up_heatmap.py", 120),
            # 2026-07-27 根因修复：先推中国源数据，防 safe_pull 回退陈旧版
            ("push_china_data.py", 90),
            ("update_data_v2.py", 300),
            ("enhance_dist.py", 30),
            ("refresh_standalone_and_deploy.py --skip-data --skip-deploy", 300),
            ("sync_check.py", 30),      # 坚果云同步检查
            ("deploy_now.py --force", 180),
        ],
    },
    "afternoon": {
        "desc": "午后扫描 (13:30/14:30/16:30)",
        "steps": [
            ("fetch_overnight_brief.py --news-only", 90),
            ("scanner.py", 300),
            # 2026-07-24 接入：基于最新 scan_result 生成 A/B 档推荐（阿狸咪独立 + 小九对照），驾驶舱顶部横幅
            ("gen_cockpit_tier_recommend.py", 30),
            ("fetch_sh_sz_history.py", 120),
            ("fetch_margin.py", 120),
            ("fetch_concept_ranking.py", 180),
            ("fetch_market_alerts.py", 180),
            ("fetch_sector_fund_flow.py", 180),
            ("fetch_limit_up_heatmap.py", 120),
            # 2026-07-27 根因修复：先推中国源数据，防 safe_pull 回退陈旧版
            ("push_china_data.py", 90),
            ("update_data_v2.py", 300),
            ("enhance_dist.py", 30),
            ("refresh_standalone_and_deploy.py --skip-data --skip-deploy", 300),
            ("sync_check.py", 30),      # 坚果云同步检查
            ("deploy_now.py --force", 180),
        ],
    },
    "post_close": {
        "desc": "收盘后快速更新 (15:20)",
        "steps": [
            ("scanner.py", 300),
            ("fetch_sector_fund_flow.py", 180),
            ("fetch_concept_ranking.py", 180),
            ("fetch_market_alerts.py", 180),
            ("fetch_sh_sz_history.py", 120),
            ("fetch_up_down_stats.py", 120),
            ("fetch_limit_up_heatmap.py", 120),
            # 2026-07-24 修复：5个"盘前"文件原只在 pre_market/19:30 刷新，
            # 若当日 pre_market 漏跑(09:20事故)，这5文件停滞>30h，
            # 触发 verify_data_vs_website.py --gate 新鲜度 FAIL → 阻断 15:30 部署。
            # → 全部补抓，确保 15:30 部署不被误拦
            ("fetch_herding_data.py", 180),
            ("fetch_main_stock.py", 180),
            ("fetch_suspension_alert.py", 180),
            ("fetch_analyst_ratings.py", 180),
            ("fetch_policy_density.py", 120),
            ("update_data_v2.py", 300),
            ("refresh_standalone_and_deploy.py --skip-data --skip-deploy", 300),
            # 2026-07-24 修复：把刚刷新的中国源数据提交推 main，
            # 否则 deploy_now.py 的 git pull 把 data/ 回退成 origin/main 陈旧版
            # （正是 15:30 数据反复"没部署"的回退源）→ 先 push 再部署
            ("push_china_data.py", 120),
            ("sync_check.py", 30),      # 坚果云同步检查
            ("deploy_now.py --force", 600),   # 2026-07-24 修复：SSH 慢网 clone+push gh-pages 实测 ~5min，180s 会被掐断 → 调 600s
        ],
    },
    "close": {
        "desc": "收盘后全量 (19:30) — 并行优化",
        "steps": [
            # ══ Group 1: 研报+投行信号（并行） ══
            [
                ("guanlan_extractor.py", 300),
                ("fetch_maharo_signals.py --non-interactive", 120),
            ],
            # ══ Group 2: 全量数据抓取（并行） ══
            [
                ("fetch_nt_data.py", 120),
                ("fetch_margin.py", 120),
                ("fetch_margin_etf.py", 120),
                ("fetch_etf_subscription.py", 120),
                ("fetch_suspension_alert.py", 120),
                ("fetch_stock_deviation.py", 180),
                ("fetch_sector_fund_flow.py", 180),
                ("fetch_sector_rs.py", 90),
                ("fetch_main_week.py", 120),
                ("fetch_market_alerts.py", 180),
                ("fetch_concept_ranking.py", 180),
                ("fetch_lhb.py", 300),
                ("fetch_main_stock.py", 300),
                ("fetch_north_fund.py", 300),
                ("fetch_south_individual.py", 300),
                ("fetch_herding_data.py", 180),
                ("fetch_cffex_holdings.py", 120),
                ("fetch_inst_trade.py", 120),
                ("fetch_ipo_data.py", 120),
                ("fetch_macro_data.py", 180),
                ("fetch_fomc.py", 60),
                ("fetch_sh_sz_history.py", 120),
                ("fetch_up_down_stats.py", 120),
                ("fetch_sh_index_fib.py", 60),
            ],
            # ══ 危机雷达数据（串行，依赖 macro_data.json 兜底 DXY，须在 Group2 后） ══
            ("fetch_crisis_data.py", 180),
            # ══ Group 3: 全量扫描（串行） ══
            ("build_candidate_pool.py", 300),
            ("scanner.py full", 600),
            # ══ Group 4: 生成脚本（并行） ══
            [
                ("calc_crds.py", 300),
                ("calc_volatility_watch.py", 300),
                ("triple_select_scan.py", 600),
                ("fetch_overnight_brief.py", 120),
                ("generate_recommend.py", 120),
                ("generate_top10.py", 60),
                ("fetch_industry_map.py", 3600),
                ("fetch_limit_up_heatmap.py", 120),
                ("fetch_52w_high.py", 120),
                ("fetch_analyst_ratings.py", 180),
                ("fetch_policy_density.py", 120),
            ],
            # ══ 实验数据入仓：三重选股等实验文件由双机预跑，提交到 main 供云端构建读取 ══
            ("push_experiment_files.py", 120),
            # ══ 中国源数据入仓：板块资金/概念/龙虎榜/北向/研报等双机专属数据，
            #    解耦自部署守卫，每日必推 main，云端方能构建新鲜数据（根因修复）══
            ("push_china_data.py", 120),
            # ══ Group 5: 注入+部署（串行） ══
            ("update_data_v2.py", 300),
            ("enhance_dist.py", 30),
            ("refresh_standalone_and_deploy.py --skip-data --skip-deploy", 300),
            ("check_syntax.py", 30),
            ("sync_check.py", 30),
            ("deploy_now.py", 180),
            ("push_notify.py", 30),
        ],
        "max_parallel": 6,
    },
    # ── 收盘分段（19:30 过载拆分，按数据时效编排） ──
    "close_p1": {
        "desc": "收盘数据抓取第一批 (17:30) — 研报+全量数据(龙虎榜除外，龙虎榜17点后出)",
        "steps": [
            # ══ Group 1: 研报+投行信号（并行） ══
            [
                ("guanlan_extractor.py", 300),
                ("fetch_maharo_signals.py --non-interactive", 120),
            ],
            # ══ Group 2: 全量数据抓取（并行，龙虎榜除外，因17点后才发布） ══
            [
                ("fetch_nt_data.py", 120),
                ("fetch_margin.py", 120),
                ("fetch_margin_etf.py", 120),
                ("fetch_etf_subscription.py", 120),
                ("fetch_suspension_alert.py", 120),
                ("fetch_stock_deviation.py", 180),
                ("fetch_sector_fund_flow.py", 180),
                ("fetch_market_fund_flow.py", 60),  # 2026-07-23 新增：盘后刷新上交所大盘资金流时间轴
                ("fetch_sector_rs.py", 90),
                ("fetch_main_week.py", 120),
                ("fetch_market_alerts.py", 180),
                ("fetch_concept_ranking.py", 180),
                ("fetch_main_stock.py", 300),
                ("fetch_north_fund.py", 300),
                ("fetch_south_individual.py", 300),
                ("fetch_herding_data.py", 180),
                ("fetch_cffex_holdings.py", 120),
                ("fetch_inst_trade.py", 120),
                ("fetch_ipo_data.py", 120),
                ("fetch_macro_data.py", 180),
                ("fetch_fomc.py", 60),
                ("fetch_sh_sz_history.py", 120),
                ("fetch_up_down_stats.py", 120),
                ("fetch_sh_index_fib.py", 60),
            ],
            # ══ 危机雷达数据（串行，依赖 macro_data.json 兜底 DXY，须在 Group2 后） ══
            ("fetch_crisis_data.py", 180),
            # ══ 双机心跳刷新：写 hb_<role>.json 并推 main，保持三方监控时间戳新鲜 ══
            ("report_heartbeat.py --role auto --mode close_p1", 60),
        ],
        "max_parallel": 6,
    },
    "close_p2": {
        "desc": "收盘扫描+生成 (18:30) — 龙虎榜(已出)+scanner全量+各类生成",
        "steps": [
            # ══ 龙虎榜（17点后交易所才发布，置于18:30确保已出） ══
            ("fetch_lhb.py", 300),
            # ══ Group 3: scanner 全量（串行） ══
            ("build_candidate_pool.py", 300),
            ("scanner.py full", 600),
            # ══ Group 4: 生成脚本（并行） ══
            [
                ("calc_crds.py", 300),
                ("calc_volatility_watch.py", 300),
                ("triple_select_scan.py", 600),
                ("fetch_overnight_brief.py", 120),
                ("generate_recommend.py", 120),
                ("generate_top10.py", 60),
                ("fetch_industry_map.py", 3600),
                ("fetch_limit_up_heatmap.py", 120),
                ("fetch_52w_high.py", 120),
                ("fetch_analyst_ratings.py", 180),
                ("fetch_policy_density.py", 120),
                ("backtest_tdx.py", 600),  # 2026-07-22 接入：收盘后生成当日K线60日回测
                # 2026-07-23 接入：消费刚生成的 backtest_tdx.json，刷新驾驶舱顶部「回测驱动买卖建议」横幅
                #   主推信号按胜率自动切换，关注/回避池随之刷新。无需改前端
                ("gen_cockpit_advice.py", 60),
                # 2026-07-24 接入：基于 scan_result 生成驾驶舱顶部 A/B 档推荐
                ("gen_cockpit_tier_recommend.py", 30),
                # 2026-07-26 补漏：基本面质量分（依赖 candidate_pool.json 已由 build_candidate_pool 生成）。
                #   原由已删除的「凌晨数据刷新」自动化(1784174169718/1784797279602)负责，删除后此源冻结，
                #   而 gen_triple_consensus / gen_triple_track 每日读取 fundamental_quality.json → 必须并入收盘链。
                ("fetch_fundamental_quality.py", 300),
            ],
            # ══ 2026-07-26 补漏：资金流汇总（依赖 north_fund/inst_trade/sector_fund_flow[close_p1] +
            #    lhb_result[本段 fetch_lhb] + industry_map[本段 Group4]，故置于 Group4 之后串行）。
            #    同样原属已删除的凌晨刷新自动化，删除后 capital_flow_summary.json 冻结于 07-24。══
            ("capital_flow_summary.py", 120),
            # ══ 2026-07-26 接入：三重共识历史追踪（先确保 triple_consensus.json 新鲜，再累加历史快照）══
            ("gen_triple_consensus.py", 30),
            ("update_triple_resonance_history.py", 30),
            # ══ 实验数据入仓：三重选股等实验文件由双机预跑，提交到 main 供云端构建读取 ══
            ("push_experiment_files.py", 120),
            # ══ 2026-07-24 接入：驾驶舱回测 + 综合回测（串行，依赖前述全量数据就绪） ══
            ("cockpit_backtest_now.py", 120),
            ("backtest_comprehensive.py", 300),
            # ══ 2026-07-26 接入：基于历史快照 + 回测文件生成历史追踪分析（依赖 backtest_comprehensive 已就绪）══
            ("gen_triple_track.py", 60),
            # ══ 中国源数据入仓：板块资金/概念/龙虎榜/北向/研报等双机专属数据，
            #    解耦自部署守卫，每日必推 main，云端方能构建新鲜数据（根因修复）══
            ("push_china_data.py", 120),
            # ══ 双机心跳刷新：写 hb_<role>.json 并推 main，保持三方监控时间戳新鲜 ══
            ("report_heartbeat.py --role auto --mode close_p2", 60),
        ],
        "max_parallel": 6,
    },
    "close_deploy": {
        "desc": "收盘最终部署 (19:30) — 注入+部署（数据已由 close_p1/close_p2 就绪）",
        "steps": [
            # ══ 安全网：即便 close_p2 未跑，也确保双机当日中国源数据已推 main ══
            ("push_china_data.py", 120),
            ("update_data_v2.py", 300),
            ("enhance_dist.py", 30),
            ("refresh_standalone_and_deploy.py --skip-data --skip-deploy", 300),
            ("check_syntax.py", 30),
            ("sync_check.py", 30),
            ("close_deploy_guarded.py", 200),
            ("push_notify.py", 30),
            # ══ 双机心跳刷新：写 hb_<role>.json 并推 main，保持三方监控时间戳新鲜 ══
            ("report_heartbeat.py --role auto --mode deploy", 60),
            # ══ 收盘收尾：数据新鲜度自检（print 型，exit0 不拖垮部署；异常由每日20:00邮件巡检告警）══
            ("check_data_freshness.py", 60),
        ],
    },
    "backup": {
        "desc": "审核+自动备份 (21:00)",
        "steps": [
            ("enhanced_backup.py", 600),
            ("report_heartbeat.py --role auto --mode backup", 60),
        ],
    },
    "weekend_light": {
        "desc": "周末轻量维护 (SA/SU 19:30) — 仅部署+读交接+注入周末标注，跳过行情fetch与update_data_v2",
        "steps": [
            ("auto_handoff_read.py", 120),
            ("inject_weekend_run.py", 30),
            ("sync_check.py", 30),
            ("deploy_now.py --force", 180),
        ],
    },
}


def run_step(command, timeout):
    """Run a single step with subprocess timeout.
    Returns (ok, elapsed, detail).
    fetch_* 步骤对网络超时/偶发失败自动重试 1 次（避免家用机限流导致数据静默落后）。
    """
    start = time.time()
    parts = command.split()
    # scanner.py 路由: 实测系统 Python 3.12.8 的 py_mini_racer(V8) 在多次初始化时会
    # FATAL 崩溃(选股观测台全扫进程被杀); 托管 Python 3.13.12 的 py_mini_racer 容许多次
    # 初始化, 配合 scanner.py 专用单线程执行器可稳定运行 → scanner 走 sys.executable(托管3.13.12)。
    exe = sys.executable if parts[0] == "scanner.py" else sys.executable
    is_fetch = parts[0].startswith("fetch_")
    max_attempts = 2 if is_fetch else 1
    last_detail = ""
    for attempt in range(max_attempts):
        try:
            proc = subprocess.run(
                [exe] + parts,
                cwd=WORKSPACE,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            elapsed = time.time() - start
            ok = proc.returncode == 0
            detail = ""
            if not ok:
                detail = f"exit={proc.returncode}"
                if proc.stderr:
                    tail = proc.stderr.strip()[-150:]
                    if tail:
                        detail += " | " + tail
                last_detail = detail
                if attempt < max_attempts - 1:
                    print(f"    ↻ {parts[0]} 失败，{3}s 后重试({attempt+1}/{max_attempts-1})...")
                    time.sleep(3)
                    continue
            return ok, elapsed, detail
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            last_detail = "TIMEOUT"
            if attempt < max_attempts - 1:
                print(f"    ↻ {parts[0]} 超时，{3}s 后重试({attempt+1}/{max_attempts-1})...")
                time.sleep(3)
                continue
            return False, elapsed, "TIMEOUT"
        except FileNotFoundError:
            elapsed = time.time() - start
            return False, elapsed, "NOT_FOUND"
        except Exception as e:
            elapsed = time.time() - start
            last_detail = str(e)[:150]
            if attempt < max_attempts - 1:
                time.sleep(3)
                continue
            return False, elapsed, str(e)[:150]
    return False, time.time() - start, last_detail


def run_parallel_group(group_steps, max_workers=6):
    """Run a group of steps in parallel.
    
    group_steps: list of (command, timeout)
    Returns: (group_ok, group_elapsed, group_detail)
        - group_ok: bool, True if all tasks succeeded
        - group_elapsed: float, total elapsed time in seconds
        - group_detail: dict, {index: (command, ok, elapsed, detail)}
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    start = time.time()
    
    def _run_one(cmd_timeout):
        cmd, timeout = cmd_timeout
        ok, elapsed, detail = run_step(cmd, timeout)
        return (cmd, ok, elapsed, detail)
    
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_run_one, ct) for ct in group_steps]
        for f in as_completed(futures):
            results.append(f.result())
    
    # Return in original order (for consistent output)
    order = {ct[0]: i for i, ct in enumerate(group_steps)}
    results.sort(key=lambda r: order.get(r[0], 999))
    
    # Calculate return values
    group_ok = all(ok for _, ok, _, _ in results)
    group_elapsed = time.time() - start
    group_detail = {i: r for i, r in enumerate(results)}
    
    return group_ok, group_elapsed, group_detail


def _sync_dual_machine_code(workspace):
    """双机代码同步：阿狸咪↔小九，每次任务执行前拉取对方最新代码。
    
    v3（强制拉取，防止覆盖旧版）：
      - 代码（py/html/js/css）走 Git 同步
      - 数据（data/*.json）走坚果云实时同步，不进 Git
      - 只需 git pull 拉取代码变更，不再 commit/push 数据
      - 失败时重试1次，仍失败则明确告警
    """
    print("  [0/1] 🔄 双机代码同步（强制拉取最新代码）...", end="", flush=True)
    start = time.time()

    # 防 SSH 挂死：限制连接超时，失败即报错而非无限挂起（与 deploy_now.py 一致）。
    # 同时强制 HTTP/1.1，规避 GitHub HTTP/2 端点偶发断连导致 pull 卡死。
    os.environ.setdefault(
        "GIT_SSH_COMMAND",
        "ssh -o ConnectTimeout=15 -o ServerAliveInterval=15 -o ServerAliveCountMax=3 -o StrictHostKeyChecking=no",
    )

    # 拉取对端最新代码。
    # 旧实现用 --autostash：双机各自重生成 data/ 导致 stash-pop 冲突、留下 UU 混乱。
    # 现统一走 safe_pull()：拉取前丢弃本地派生数据改动（总会被重新构建，
    #   权威版在 origin/main），干净树 rebase 拉取，冲突安全 pop。永绝后患。
    for attempt in range(2):
        ok = safe_pull()
        if ok:
            elapsed = time.time() - start
            print(f"✓  {elapsed:.1f}s")
            break
        elif attempt == 0:
            # 第一次失败，等5秒重试
            time.sleep(5)
        else:
            # 第二次仍失败，严重告警！
            elapsed = time.time() - start
            print(f"\n  ❌ Git Pull 失败（已重试1次）！可能使用旧版代码！")
            print(f"     ⚠️  请立即检查网络或手动执行: cd {workspace} && git pull")
            print(f"     继续使用本地代码... ({elapsed:.1f}s)")


def _check_code_version(workspace):
    """检查关键文件是否包含最新版本的代码标记。
    如果没有，说明坚果云可能还没同步完成，当前用的可能是旧版代码。
    """
    # 关键代码标记（不匹配 = 旧版）
    import glob as _glob
    
    SAFETY_MARKERS = {
        "index_master.html": [
            ("typeof CLOSED_SET !== 'undefined'", "CLOSED_SET防御检查"),
        ],
        "fetch_sector_fund_flow.py": [
            ("neodata流入+流出完整", "neodata双查询修复"),
        ],
    }
    
    issues = []
    for fname, markers in SAFETY_MARKERS.items():
        fpath = os.path.join(workspace, fname)
        if not os.path.exists(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            for marker, desc in markers:
                if marker not in content:
                    issues.append(f"{fname} 缺少 {desc}")
        except Exception:
            pass
    
    if issues:
        print(f"\n  ⚠️ 坚果云版本检查异常（可能是同步延迟导致使用旧版代码）:")
        for issue in issues:
            print(f"     ❌ {issue}")
        print(f"     风险：部署旧版代码可能导致网站崩溃或数据异常")
        print(f"     建议：检查坚果云是否正在同步，等待完成后再部署")
    
    # 清理坚果云冲突文件
    # 仅限会双机写的同步目录 + 根目录非递归层，避免递归全 workspace 误删源码/.git/backup_
    # 典型冲突副本：scan_result(冲突).json / xxx.conflict.json / HANDOVER_LOG(冲突).jsonl
    # 注意：os.remove 的删除会被坚果云记入其回收站（坚果云机制，代码无法阻止）；
    #       若想根治回收站堆积，请在坚果云客户端设置「回收站保留 N 天自动清理」。
    CONFLICT_PATTERNS = ["*冲突*", "*conflict*", "*.conflict.*"]
    CONFLICT_SUBDIRS = ["data", "dist/data", "standalone", "dist/standalone"]
    cleaned = 0
    # 1) 已知会冲突的子目录（递归）
    for d in CONFLICT_SUBDIRS:
        base = os.path.join(workspace, d)
        if not os.path.isdir(base):
            continue
        for pat in CONFLICT_PATTERNS:
            for f in _glob.glob(os.path.join(base, "**", pat), recursive=True):
                try:
                    os.remove(f)
                    cleaned += 1
                    print(f"  🧹 清理坚果云冲突文件: {os.path.relpath(f, workspace)}")
                except Exception:
                    pass
    # 2) 根目录层（非递归）冲突副本，如 HANDOVER_LOG(冲突).jsonl
    for pat in CONFLICT_PATTERNS:
        for f in _glob.glob(os.path.join(workspace, pat)):
            try:
                os.remove(f)
                cleaned += 1
                print(f"  🧹 清理坚果云冲突文件: {os.path.relpath(f, workspace)}")
            except Exception:
                pass
    if cleaned:
        print(f"  ✓ 共清理 {cleaned} 个坚果云冲突副本")


def _write_handover_log(workspace, mode, my_host, results, still_failed):
    """每次任务结束后写交接日志，坚果云同步给另一台电脑。
    日志文件：HANDOVER_LOG.jsonl（每行一个JSON，方便追加）
    """
    import json as _j
    from datetime import datetime as _dt

    log_file = os.path.join(workspace, "HANDOVER_LOG.jsonl")
    now = _dt.now().strftime("%Y-%m-%d %H:%M:%S")

    # 收集关键数据的时间戳
    data_times = {}
    key_files = [
        ("data/scan_result.json", "scan_time"),
        ("data/gold_pool.json", "update_time"),
        ("data/north_fund.json", "update_time"),
        ("data/lhb_result.json", "update_time"),
    ]
    for fpath, time_key in key_files:
        full = os.path.join(workspace, fpath)
        if os.path.exists(full):
            try:
                with open(full, "r", encoding="utf-8") as f:
                    d = _j.load(f)
                if isinstance(d, dict):
                    t = d.get(time_key, "")
                    if t:
                        data_times[fpath] = t
            except Exception:
                pass

    entry = {
        "time": now,
        "mode": mode,
        "host": my_host,
        "success": len(still_failed) == 0,
        "failed_steps": still_failed,
        "data_times": data_times,
    }

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(_j.dumps(entry, ensure_ascii=False) + "\n")
        print(f"  📝 交接日志已写: {my_host} {mode} {'✓' if len(still_failed)==0 else '✗'}")
    except Exception as e:
        print(f"  ⚠️ 交接日志写入失败: {e}")

    # 🔁 小九自动写 HANDOVER_小九_YYYY-MM-DD.md（便于阿狸咪 19:30 读取）
    if "xiaojiu" in my_host.lower():
        _write_xiaojiu_handover_md(workspace, now[:10], now, mode, my_host, results, still_failed, entry)


def _write_xiaojiu_handover_md(workspace, today, now_str, mode, my_host, results, still_failed, entry):
    """小九任务完成时，自动生成/更新 HANDOVER_小九_YYYY-MM-DD.md。
    如果当天已有 .md 文件，则追加本次运行记录（不覆盖之前的内容）。
    """
    import json as _j

    md_file = os.path.join(workspace, f"HANDOVER_小九_{today}.md")

    ok_count = sum(1 for _, ok, _, _ in results.values() if ok)
    total = len(results)
    fail_count = total - ok_count

    # 本次运行概要
    block = []
    block.append(f"---\n")
    block.append(f"**🕐 {now_str}** | 模式: `{mode}` | 结果: {'✓ 全部通过' if not still_failed else '✗ 有失败'}")
    block.append(f"步骤: 成功 {ok_count}/{total}")
    if still_failed:
        for s in still_failed:
            block.append(f"- ❌ {s}")
    else:
        block.append("")

    # 关键数据时间戳
    dt = entry.get("data_times", {})
    if dt:
        block.append(f"关键数据:")
        for k, v in dt.items():
            block.append(f"  - {k} → {v}")
    block.append("")

    content = "\n".join(block)

    try:
        # 如果已有当天文件，追加新记录；否则创建
        mode_write = "a" if os.path.exists(md_file) else "w"
        with open(md_file, mode_write, encoding="utf-8") as f:
            if mode_write == "w":
                f.write(f"# 九宝量化 v6.0 — 交接单（小九 → 阿狸咪）\n\n")
                f.write(f"**日期**：{today}\n")
                f.write(f"**方向**：小九（单位机） → 阿狸咪（家用机）\n")
                f.write(f"\n自动生成，每轮任务执行后追加。\n\n")
            f.write(content)
        print(f"  📄 小九交接文档已{'更新' if mode_write=='a' else '创建'}: {os.path.basename(md_file)}")
    except Exception as e:
        print(f"  ⚠️ 小九交接文档写入失败: {e}")


def print_header(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}  —  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}\n")


def print_summary(results, still_failed):
    total = len(results)
    ok_count = sum(1 for _, ok, _, _ in results if ok)
    fail_count = total - ok_count
    print(f"\n{'=' * 60}")
    print(f"  总计: {total}  成功: {ok_count}  失败: {fail_count}")
    if not still_failed:
        print(f"  ✓ 全部通过")
    else:
        print(f"  ✗ 以下步骤重试后仍未通过:")
        for name in still_failed:
            print(f"    - {name}")
    print(f"{'=' * 60}\n")
    return 0 if not still_failed else 1


def _check_peer_stop_signal():
    """若本机是阿狸咪，且存在小九今日发出的 URGENT 停机文件，则禁止运行。"""
    role_file = os.path.join(WORKSPACE, ".machine_role")
    try:
        with open(role_file, encoding="utf-8") as f:
            role = f.read().strip().upper()
    except Exception:
        return  # 无角色文件时不误判，避免在未知机器上误停
    if role not in ("ALIMI", "LEMONCAT"):
        return
    import glob as _glob
    import datetime as _dt
    today = _dt.date.today().isoformat()
    for f in _glob.glob(os.path.join(WORKSPACE, "URGENT_小九_*.md")):
        base = os.path.basename(f)
        if "停机" in base and today in base:
            sep = "=" * 55
            print(f"\n{sep}")
            print(f"🛑 小九紧急停机指令已送达：{base}")
            print("   阿狸咪本机立即退出 batch_update，不得与主机冲突。")
            print(f"{sep}\n")
            sys.exit(0)


def main():
    _check_peer_stop_signal()

    if len(sys.argv) < 2 or sys.argv[1] in ("--help", "-h"):
        print("batch_update.py — 九宝量化统一调度脚本")
        print("\n可用模式:")
        for k, v in MODES.items():
            print(f"  {k:<18s} {v['desc']}")
        print("\n用法: python batch_update.py <模式>")
        return

    mode = sys.argv[1]
    if mode not in MODES:
        print(f"✗ 未知模式: {mode}")
        print(f"  可用: {', '.join(MODES.keys())}")
        sys.exit(2)

    # ── Step 0.2: 非交易日跳过（周末 + A股法定假日）──
    # 避免双机在休市日空跑抓行情（浪费 token / 报错 / 部署陈旧数据）。
    # 规则：行情类模式在休市日跳过；weekend_light / backup 等始终运行；
    # 周六 close 仍跑（T+1 全量刷新）。模块缺失则 fail-safe 照跑不误伤。
    ALWAYS_RUN_MODES = {"weekend_light", "backup"}
    MARKET_MODES = {"pre_market", "morning_scan", "morning_plus", "morning_report",
                    "afternoon", "post_close", "close_p1", "close_p2", "close"}
    if mode in ALWAYS_RUN_MODES or mode not in MARKET_MODES:
        _skip_reason = None
    else:
        import datetime as _dt
        _today = _dt.date.today()
        if mode == "close" and _today.weekday() == 5 and not _is_holiday(_today):
            _skip_reason = None  # 周六且非法定假日 → T+1 全量刷新照跑
        elif _is_trading_day is None:
            _skip_reason = None  # 模块缺失不放行跳过，fail-safe 照跑
        elif _is_trading_day(_today):
            _skip_reason = None
        else:
            if _today.weekday() >= 5 and _is_holiday is not None and _is_holiday(_today):
                _skip_reason = "法定假日(周末)"
            elif _today.weekday() >= 5:
                _skip_reason = "周末"
            else:
                _skip_reason = "法定假日"
    if _skip_reason:
        print(f"⏭️ 非交易日（{_skip_reason}），模式 [{mode}] 跳过，不抓行情")
        sys.exit(0)

    cfg = MODES[mode]
    print_header(f"📊 {cfg['desc']}")

    # ── Step 0: 双机代码同步（阿狸咪 ↔ 小九互相识别对方最新版） ──
    _sync_dual_machine_code(WORKSPACE)

    # ── Step 0.5: 双机心跳互备（一台掉线另一台自动接棒） ──
    import json as _json
    HEARTBEAT_FILE = os.path.join(WORKSPACE, ".batch_heartbeat.json")
    HEARTBEAT_TIMEOUT = 120  # 2分钟无心跳视为掉线

    # 机器标识：优先读 .machine_role（ALIMI / XIAOJIU），否则回退 COMPUTERNAME。
    # 两台机器 COMPUTERNAME 都叫 CAT，必须用 .machine_role 区分谁是谁，否则日志无法分辨。
    def _get_host_name():
        role_file = os.path.join(WORKSPACE, ".machine_role")
        try:
            if os.path.exists(role_file):
                with open(role_file, "r", encoding="utf-8") as _f:
                    _role = _f.read().strip()
                if _role:
                    return _role
        except Exception:
            pass
        return os.environ.get("COMPUTERNAME", "unknown")

    my_host = _get_host_name()
    resume_from = 0  # 接棒时的断点步骤索引

    try:
        if os.path.exists(HEARTBEAT_FILE):
            with open(HEARTBEAT_FILE, "r") as f:
                hb = _json.load(f)
            hb_age = time.time() - hb.get("last_beat", 0)
            hb_mode = hb.get("mode", "")
            hb_host = hb.get("host", "?")
            hb_done = hb.get("steps_done", 0)
            hb_total = hb.get("total_steps", len(cfg["steps"]))

            if hb_age < HEARTBEAT_TIMEOUT and hb_mode == mode:
                print(f"  ❤️ {hb_host} 正在执行 {hb_mode} (心跳 {hb_age:.0f}秒前, 已完成 {hb_done}/{hb_total})")
                print(f"     本机({my_host})跳过")
                sys.exit(0)

            if hb_age >= HEARTBEAT_TIMEOUT and hb_mode == mode and hb_done < hb_total:
                print(f"  💔 {hb_host} 心跳超时 ({hb_age:.0f}秒), 掉线于步骤 {hb_done}/{hb_total}")
                print(f"     {my_host} 接棒，从步骤 {hb_done + 1} 继续!")
                resume_from = hb_done
                # 继续执行：不退出，resume_from 跳过已完成步骤

            if hb_mode != mode:
                print(f"  🔄 模式不同 ({hb_mode} vs {mode})，正常启动")
    except Exception:
        pass

    # 初始化心跳
    def _write_heartbeat(steps_done, total, started=None):
        try:
            hb = {
                "mode": mode,
                "host": my_host,
                "started": started or time.time(),
                "last_beat": time.time(),
                "steps_done": steps_done,
                "total_steps": total,
            }
            with open(HEARTBEAT_FILE, "w") as f:
                _json.dump(hb, f)
        except Exception:
            pass

    start_ts = time.time()
    _write_heartbeat(0, len(cfg["steps"]), start_ts)
    if resume_from > 0:
        print(f"  🔁 接棒执行: 已完成 {resume_from}/{len(cfg['steps'])} 步")
    else:
        print(f"  ▶️ 正常启动 ({my_host}, {mode})")

    results = {}
    failed_indices = []

    # ── Phase 1: 首轮执行 ──
    start_idx = resume_from
    for i in range(start_idx, len(cfg["steps"])):
        step = cfg["steps"][i]

        # ═══ 并行组：列表中包含多个 (cmd, tmo) ═══
        if isinstance(step, list):
            label = f"[{i + 1}/{len(cfg['steps'])}]"
            max_workers = cfg.get("max_parallel", 6)
            print(f"  {label} 🔀 并行组 ({len(step)}个任务, 最多{max_workers}并发)")
            group_ok, group_elapsed, group_detail = run_parallel_group(step, max_workers)
            # 存储组内每个结果
            for j, (cmd_j, tmo_j) in enumerate(step):
                results[(i, j)] = group_detail.get(j, (cmd_j, False, 0, "NOT_RUN"))
            # 用组摘要作为 i 的结果
            results[i] = (f"PARALLEL_GROUP_{len(step)}", group_ok, group_elapsed, "")
            _write_heartbeat(i + 1, len(cfg["steps"]), start_ts)
            if not group_ok:
                failed_sub = [
                    cmd_j for j, (cmd_j, tmo_j) in enumerate(step)
                    if not results.get((i, j), (cmd_j, True, 0, ""))[1]
                ]
                print(f"    ⚠ 组内失败子任务: {', '.join(failed_sub)}")
                failed_indices.append(i)
            continue

        # ═══ 单步执行 ═══
        cmd, tmo = step
        cmd_name = cmd.split()[0]

        # 🔒 部署前数据监控闸门（盘前/盘中/盘后通用）：verify --gate 命中 FAIL 则阻断部署，
        # 保留上一版正常数据，绝不把残缺/矛盾/陈旧数据推上线（修复"上午鸡飞狗跳"综合症）。
        if cmd_name == "deploy_now.py":
            print(f"  🔒 部署前闸门检查 (verify_data_vs_website.py --fast --gate)...")
            gate_ok, gate_el, gate_detail = run_step("verify_data_vs_website.py --fast --gate", 120)
            if not gate_ok:
                print(f"  🚫 闸门 FAIL → 阻断部署（保留上一版正常数据），跳过: {cmd}")
                print(f"     原因: {gate_detail}")
                results[i] = (cmd, False, gate_el, "GATE_BLOCKED:" + str(gate_detail))
                # deploy 通常为流程末步；阻断即结束，不再部署，避免半残上线
                break
            else:
                print(f"  🟢 闸门通过 ({gate_el:.1f}s)，继续部署")

        label = f"[{i + 1}/{len(cfg['steps'])}]"
        print(f"  {label} {cmd:<35s} ", end="", flush=True)
        ok, elapsed, detail = run_step(cmd, tmo)
        results[i] = (cmd, ok, elapsed, detail)

        icon = "✓" if ok else "✗"
        extra = f"  {detail}" if detail else ""
        print(f"{icon}  {elapsed:.1f}s{extra}")

        # 💓 每步更新心跳
        _write_heartbeat(i + 1, len(cfg["steps"]), start_ts)

        if not ok:
            failed_indices.append(i)
            # 关键数据源失败：立即终止后续步骤，避免用陈旧数据继续扫描/部署
            if cmd_name == "build_candidate_pool.py":
                print(f"  🚫 关键步骤 {cmd_name} 失败，终止后续步骤（防止陈旧数据上线）")
                break

    # ── Phase 2: 失败步骤重试（仅一次） ──
    still_failed = []
    if failed_indices:
        print(f"\n  ── 重试 {len(failed_indices)} 个失败步骤 ──")
        for idx in failed_indices:
            step = cfg["steps"][idx]

            # 并行组：重试组内失败的任务
            if isinstance(step, list):
                max_workers = cfg.get("max_parallel", 6)
                print(f"  [R] 🔀 并行组重试 ({len(step)}个任务)")
                group_ok, group_elapsed, group_detail = run_parallel_group(step, max_workers)
                for j, (cmd_j, tmo_j) in enumerate(step):
                    results[(idx, j)] = group_detail.get(j, (cmd_j, False, 0, "NOT_RUN"))
                if not group_ok:
                    # 记录具体失败的子任务（含错误详情），避免只写 PARALLEL_GROUP_N 盲区
                    failed_sub = []
                    for j, (cmd_j, tmo_j) in enumerate(step):
                        r = group_detail.get(j)
                        if r is None or not r[1]:
                            detail_msg = (r[3] if r else "NOT_RUN")
                            failed_sub.append(f"{cmd_j} [{detail_msg}]")
                    still_failed.append(
                        f"PARALLEL_GROUP_{len(step)}: " + " | ".join(failed_sub)
                    )
                continue

            # 单步重试
            cmd, tmo = step
            label = "[R]"
            print(f"  {label} {cmd:<35s} ", end="", flush=True)
            ok, elapsed, detail = run_step(cmd, tmo)
            results[idx] = (cmd, ok, elapsed, detail)

            icon = "✓" if ok else "✗"
            extra = f"  {detail}" if detail else ""
            print(f"{icon}  {elapsed:.1f}s{extra}")

            if not ok:
                still_failed.append(cmd)

        if still_failed:
            names = ", ".join(still_failed)
            print(f"\n  ⚠ 重试后仍然超时/失败: {names}")

    exit_code = print_summary(list(results.values()), still_failed)
    # 写交接日志（坚果云同步，另一台电脑可读取）
    _write_handover_log(WORKSPACE, mode, my_host, results, still_failed)
    # 清理心跳（全部完成）
    try:
        if os.path.exists(HEARTBEAT_FILE):
            with open(HEARTBEAT_FILE, "r") as f:
                hb = _json.load(f)
            if hb.get("host") == my_host and hb.get("mode") == mode:
                os.remove(HEARTBEAT_FILE)
                print(f"  ✅ 清理心跳 ({my_host}, {mode})")
    except Exception:
        pass
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
