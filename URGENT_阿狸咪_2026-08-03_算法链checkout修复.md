# 🔴 URGENT · v8 盘后算法链 checkout 失败修复（2026-08-03 21:50）

## 现状（已审计，GitHub API 实测）
- `v8_algo_run` 定时修复**已生效**：今晚 **21:23（UTC 13:23）真的被调度触发**了（`run#30817739173`）。
- **但首步 `📥 Checkout v8` 直接 `failure`** —— 算法一行没跑，无新鲜 raw_data 推上。
- 21:34 的 `v8_build_deploy (#30818542717 success)` 只是把**陈旧 raw_data（gold_pool/triple→08-02、lhb→08-01、candidate→07-31）重新打包部署** → 主站看到的盘后/选股/共振数据全是旧的。
- 失败根因（高置信）：自托管 cn runner（Windows 持久化工作目录）脏树 / git dubious ownership → `actions/checkout@v4` 检出即 abort。（精确报错行因匿名 API 拉 logs 返回 403 无法读取；若加固后仍失败，查 GitHub Actions 日志确认具体 checkout 错误。）

## 已修复（已 push 到 v8 main @ 2384b5d）
- `v8_algo_run.yml` 在 checkout 前加清理前置步：
  - `git config --global --add safe.directory '*'`
  - `git reset --hard HEAD`
  - `git clean -fdx -e out -e algorithms/out -e algorithms/data`（保留算法产物）
  - checkout 本身加 `clean: true`
- YAML 已用 pyyaml 校验通过。分支 `feat/v8-detach-v6` 已 rebase 到含此修复的 main。
- 效果：明日起 18:30 / 20:00 定时跑应能正常过 checkout。

## 🔥 今晚就要最新数据 —— 请立即在 cn 机器本地重跑（机器在线，刚还接了任务）
沙箱无行情源访问权限（东财 push2 不可达、无 mootdx），**只有 cn 机器能产数据**。在本机 `E:/workspace/quant-scanner-v8` 执行：

```powershell
cd E:/workspace/quant-scanner-v8
git fetch origin
git checkout main
git reset --hard origin/main
git clean -fdx -e out -e algorithms/out -e algorithms/data
$env:V8_PUSH = "1"
python algorithms/run_algorithms.py
```

跑完（约 15–30 分钟）`run_algorithms.py` 会经 `api_push_raw.py` 自动推送 `raw_data/` → 触发 `v8_build_deploy` → 主站 Pages 刷新。
若本地 `file:///E:/workspace/quant-scanner-v8/index.html` 想同步看到，推送后执行：
```powershell
git pull
python update_v8.py
```
（或直接在浏览器刷新 GitHub Pages 主站）。

### 备选：用 GitHub Actions 手动触发
v8 仓 → Actions → `🇨🇳 v8 盘后算法链(cn)` → Run workflow（已加固，应能过 checkout）。但需 cn runner 在线接单。

## 验收
跑完后确认 `raw_data/` 这些文件 update_time = 2026-08-03：
`gold_pool / triple_consensus / lhb_data / candidate / top10_daily / sector_rs / inst_trade / mahoro / cockpit_advice`
选股策略页 / 盘后数据页 / 共振日历页即全部恢复最新。

---
*阿狸咪 21:50 审计结论：之前说"v8 算法更新更强"没错 —— 算法脚本确实是增强版；问题出在**定时任务 checkout 步在自托管 runner 上失败**（不是算法本身），现已加固并给出今晚本地重跑命令。*
