' 中国源确定性调度器 — 无窗口后台启动
' 用法：双击运行，或放入 Windows 任务计划程序 -> 启动程序指向本 vbs

Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c ""D:\stock-scanner-repo\repo-temp\start_china_scheduler.bat""", 0, False
Set WshShell = Nothing
