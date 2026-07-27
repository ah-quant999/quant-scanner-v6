@echo off
chcp 65001 >nul
setlocal

REM 中国源确定性调度器 — 前台启动（保留控制台日志）
REM 用法：双击运行，或放入 Windows 任务计划程序

cd /d "D:\stock-scanner-repo\repo-temp"
set PYTHON="C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe"

%PYTHON% china_source_scheduler.py

endlocal
