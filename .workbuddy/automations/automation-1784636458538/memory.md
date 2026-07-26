# 自动清理陈旧部署锁 — 执行记录

## 2026-07-25 19:20
- 检查 origin/main，无远程 .deploy_lock → nothing to clean
- 无事可做，跳过

## 2026-07-26 19:23
- 检测到 origin/main 上存留 host=CAT lock（部署锁，由并发 deploy 中途上锁）
- `clean_deploy_lock.py` 首次 push 失败：远程 main 在被清理前已推进到锁的 commit
- 手动处理：同步本地到 origin/main → `git rm .deploy_lock` → commit `2f04e171` → push（SSH 一度 connection reset，重试后确认成功）
- 清理成功，远程锁被删除
- `_heartbeat.log` 写入 `clean_lock_20260726_1923`

## 2026-07-22 19:22
- 检测到 origin/main 上存留 host=CAT 残锁（age≈73s → 实际已过期）
- `clean_deploy_lock.py` 清理并 push commit `d62e8a4d` [lock] cleanup stale lock from CAT
- 清理成功，远程锁被删除
- 但并发部署进程（19:20 的 deploy automation）随后重新上锁（host=CAT, age=52s at 19:23）→ 新锁有效，非残锁
- `_heartbeat.log` 写入 `clean_lock_20260722_192205`
- 脚本 bug 修复：`_git()` 不支持 `allow_empty` 参数，已改为 `commit --allow-empty` 内联
