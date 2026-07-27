# 注册中国源调度器到 Windows 任务计划程序，实现开机自启
# 以管理员权限运行 PowerShell 后执行本脚本

$taskName = "九宝量化-中国源确定性调度器"
$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"D:\stock-scanner-repo\repo-temp\start_china_scheduler.vbs`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable:$false
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
Write-Host "已注册任务: $taskName"
Write-Host "启动命令: wscript.exe `"D:\stock-scanner-repo\repo-temp\start_china_scheduler.vbs`""
