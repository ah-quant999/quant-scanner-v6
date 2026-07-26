# 数据新鲜度看门狗自修复 — 执行记录

## 2026-07-26 20:30
- **状态**: 完成（exit 0，部署成功）
- **修复项数**: 6
  - maharo_signals.json (82h 陈旧) ✅
  - cockpit_backtest.json (缺失) ✅
  - recommend.json (数组格式被识别为缺失) ✅
  - industry_map.json (49h 陈旧) ✅
  - stock_names.json (缺失) ✅
  - guanlan_reports.json (60h 陈旧) ✅
- **注意**: push_china_data.py 超时 (180s)，但 deploy_now.py --force 正常完成
- **代码修复**: `get_data_time()` 加 `isinstance(d, list)` 兜底，避免 JSON 数组文件崩溃
