# 10:05 盘前失败自愈 — 执行记忆

## 2026-07-21 (周二)
- 10:05 自愈：`check_morning_deploy.py` 退出码1 → 进入自愈。`batch_update pre_market` 失败(PREMARKET_EXIT=1)：build_candidate_pool 当时本机未装 mootdx → akshare 300s超时×2，verify gate 正确阻断部署（避免陈旧数据上线）。
- 但 10:09 小九走 GTimg 源(23s/371只) + 10:14 部署成功 → 站点已救活(标题 20260721101903)。自愈为冗余失败，逻辑无问题。
- 后续本机已装 mootdx；build_candidate_pool.py 加 GTimg 回退双保险（已验证跑通 12.8s/5012只）。

## 11:07 全修（用户"按你顺序全修"授权）
- 6项全完成：①UU冲突已清(无需) ②打新🔥高亮条(index_master) ③CRDS刷新07-21(calc_crds) ④triple_select入morning_plus盘中(batch_update) ⑤gold_pool update_time正常 ⑥归档22个PAUSED备机自动化(软删可恢复)。
- 源码改动 commit+push main (43c9387)。
- 未立即部署（避盘中push竞争），等今晚18:31云端或下次定时自动生效。

## 2026-07-22 (周三)
- 10:05 自愈：check_morning_deploy.py 退出码 0（MORNING_FIRED），premarket_heartbeat.log 09:43:54 已 `pre_market DONE` → 盘前正常，零开销结束，未重复跑。

## 2026-07-24 (周五) ✅ 自愈成功
- check_morning_deploy 退出码1(MORNING_MISSED) → 进入自愈。无 .deploy_lock。
- 关键发现：候选池其实今早 08:53 已成功构建(新鲜)，问题不在数据在**部署那步没完成**——09:20 pipeline 的"双机接棒"机制检测到 xiaojiu 心跳超时(901s)判掉线于步骤2/9，从步骤3接棒但整轮未真正走到部署/未写 DONE 留痕。
- 根因：`build_candidate_pool.py` 今日外部源**逐只拉取详情慢**(mootdx主源5010行仅12s很快，但随后 99只/段 @~1.3it/s ≈75s/段，多段累计~6min)，超过 pre_market 步骤 300s 超时→关键步骤失败终止流水线=09:20 静默失败根因。(与07-23 mootdx无限挂起不同，今天是"慢"非"挂")
- 处理：①先单独重建候选池成功(10:17, total380)；②**放宽 batch_update.py 里 build_candidate_pool 步骤超时 300→600s**(line 90，根治慢源日)；③重跑 `batch_update.py pre_market` exit0(接棒从步骤3复用新鲜候选池，8m44s)；④WebFetch 验线上标题「九宝量化 v6.0 (20260724102634)」构建戳今日10:26；⑤gh-pages 5a60b7fe→8e72ebff，本地 dist 戳一致。
- 误区排除：`SKIP_MOOTDX=1` 会强制走**慢的 akshare 兜底**(300s超时死)，慢源日反而要**保留 mootdx→GTimg 快路径**(勿加 SKIP_MOOTDX)。
- 留痕：premarket_heartbeat.log(DONE+SELF_HEAL) + _heartbeat.log 均写 DONE；check_morning_deploy 复核退0(MORNING_FIRED)。
- 持久化：超时修复+心跳 commit+push main(36f8e380)，防下次同步回退。

## 2026-07-23 (周四) ✅ 自愈成功
- check_morning_deploy 退出码1(MORNING_MISSED) → 进入自愈。
- 根因连锁：①09:20任务(batch_update pre_market)在 build_candidate_pool 阶段**卡死**(TDX不可达时 mootdx 无超时→无限挂起)，导致 50+ 分钟未部署；②本机又起了一轮竞争 batch_update，两进程并发争抢接口互相拖慢；③即使流水线跑完，部署前闸门 verify_data_vs_website --gate 因 **herding_data/main_stock/suspension_alert 自 07-20 起陈旧59h** 而 FAIL→阻断部署。
- 处理：杀掉卡死进程树(8392→17420→14988)清竞争；给 build_candidate_pool.py 的 mootdx 路径加 `socket.setdefaulttimeout(30)` 超时兜底+`SKIP_MOOTDX=1` 开关(本轮绕过挂死的 mootdx 直走已加(15,60)超时的 akshare)，fix 已由部署自动提交进 origin/main(d0b46099)，根治明日重演；手动跑 fetch_herding_data/main_stock/suspension_alert.py 刷新3个陈旧文件；重跑闸门→通过；deploy_now.py --force 部署成功，站点构建戳 20260723103839，WebFetch 验标题含「九宝量化」且构建戳今日。
- 留痕：premarket_heartbeat.log + _heartbeat.log 均写 DONE。
- 结论：上午静默失败已补救，站点已更新为今日盘前数据。
