# automation-1783428527805 执行记录

## 2026-07-11 (周六) 18:26
- 执行 `python batch_update.py close_p2`
- 结果：非交易日（周末）自动跳过，未抓行情，无报错，耗时 3s。
- 注：BYDAY=MO-FR 定时任务，周末本不应触发；本次为手动/测试触发，脚本自身周末守卫正确生效。

## 2026-07-14 (周二) 18:26
- 执行 `python batch_update.py close_p2`
- **第1次**：fetch_analyst_ratings.py TIMEOUT（家用机东财慢，60s不够）
- **修复**：batch_update.py 中 fetch_analyst_ratings.py 超时 60s→180s（close 和 close_p2 双处）
- **第2次（重跑）**：14/14 全部通过 ✓，总耗时 ~4min。scanner.py full 耗时正常。
- ⚠️ 家用机东财接口慢的问题持续存在，超时已放宽到 180s

## 2026-07-15 (周三) 18:31（自动触发+手动修复重跑）
- **问题**：`build_candidate_pool.py` 在家用机（阿狸咪）上无限挂起，导致两次超时（120s→300s 均不够）
- **根因**：home 机 mootdx TrafficStatSocket 泄漏 + 东财 akshare 接口慢/挂起
- **修复1**：`batch_update.py` 中 `build_candidate_pool.py` 超时 120s→300s（三处 pre_market/close_p1/close_p2）
- **修复2**：`build_candidate_pool.py` 中数据源优先级反转：akshare(东财/新浪)优先 → mootdx兜底（原为 mootdx 优先）
- **最终结果**：14步中13步通过 ✅，仅 `build_candidate_pool.py` 重试后仍 TIMEOUT
- **影响**：候选池未重建（使用前次数据），其余13步正常（龙虎榜/scanner/并行组）
- **未解决**：home 机 东财 API 仍慢到 5min 无法返回，需要 HTTP 连接超时或跳过 A股排名
