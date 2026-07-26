# 执行记录: 2026-07-24 06:27 (周五·第6轮)

## 结果概要
- **交易日**: 是 (周五)
- **脚本**: 14/15 ✅ (fetch_inst_trade.py ❌ exit=1, 保留旧数据属正常)
- **PUSHED**: true (f9b64465)
- **DEPLOYED**: true (gh-pages 131aa41)
- **运行耗时**: ~10分钟
- **备注**: 凌晨数据刷新，git stash→drop→pull→commit→push→deploy全链路正常

## 脚本状态
| 脚本 | 状态 | 耗时 | 备注 |
|------|------|------|------|
| fetch_nt_data.py | ✅ | 29s | ETF+异动+日历聚合 |
| fetch_margin.py | ✅ | 3s | 两融数据 |
| fetch_sh_sz_history.py | ✅ | 2s | 上证+深证K线 |
| fetch_etf_subscription.py | ✅ | 66s | ETF申赎 |
| fetch_up_down_stats.py | ✅ | 80s | 涨跌家数 |
| fetch_north_fund.py | ✅ | 10s | 北向资金 |
| capital_flow_summary.py | ✅ | 0s | 资金流汇总 |
| fetch_stock_deviation.py | ✅ | 116s | 股票乖离率扫描 |
| fetch_sector_fund_flow.py | ✅ | 15s | 行业板块资金流 |
| fetch_sector_rs.py | ✅ | 9s | 板块相对强弱 |
| fetch_market_alerts.py | ✅ | 51s | 市场预警+指数 |
| fetch_concept_ranking.py | ✅ | 34s | 概念板块排行 |
| fetch_cffex_holdings.py | ✅ | 39s | 中金所持仓 |
| fetch_inst_trade.py | ❌ | 40s | exit=1(旧数据保留) |
| fetch_sh_index_fib.py | ✅ | 10s | sh+sz双文件FIB |

## 部署信息
- data commit: f9b64465
- 部署: ✅ 成功 (gh-pages 131aa41)
- 站点: https://ah-quant999.github.io/quant-scanner-v6/
