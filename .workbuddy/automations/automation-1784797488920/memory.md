# 小九-每日自动化审计 16:30 档 — 执行摘要

## 2026-07-24 首次运行
- severity=ERROR, errors=3, warns=6, fixed=0
- 3个ERR：
  - `automation-1784796217689` 500 Internal error(非429)
  - `1783303308242` 429 quota exceeded(hy3频率超限)
  - `automation-1779668598510` 429 quota exceeded(hy3频率超限)
- 6个WARN：
  - 心跳缺失4项(08:00交接/09:25打新/11:46/14:31盘中)
  - neodata token 0.9h后过期
  - 小九部署4.4h前(盘中应<1h)
- 告警行已写入 _heartbeat.log
- model_id 无错配（0修复）
