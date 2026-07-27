@echo off
chcp 65001 >nul
setlocal

REM 中国源确定性调度器 — 前台启动（保留控制台日志）
REM 用法：双击运行，或放入 Windows 任务计划程序

cd /d "D:\stock-scanner-repo\repo-temp"
REM 2026-07-27 根因修复：原 envs/default venv 不存在 → 调度器起不来/scanner.py 崩（py_mini_racer/mootdx 缺失）
REM → scan_result.json 自 07-24 起不刷新 → 健康看板"云服务维护"红横幅常驻。
REM 改用系统 Python 3.14.3 全路径（已验证含全部依赖，scanner.py quick 69s 跑通，落盘 scan_time=今日）。
set PYTHON="C:\Users\Administrator\AppData\Local\Microsoft\WindowsApps\python.exe"

%PYTHON% china_source_scheduler.py

endlocal
