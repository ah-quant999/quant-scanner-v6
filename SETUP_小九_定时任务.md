# 小九定时任务设置脚本（单位电脑运行）

## 使用方法
1. 把本文件保存为 `setup_xiaojiu_tasks.ps1`
2. 在单位电脑上 **右键 → 以管理员身份运行 PowerShell**
3. 执行：`.\setup_xiaojiu_tasks.ps1`

## 自动创建的任务（工作日）

| 时间 | 任务 | 说明 |
|------|------|------|
| 07:30 | pre_brief | 晨间速报 |
| 09:15 | pre_market | 盘前扫描 |
| 09:45 | morning_scan | 盘中快速扫描 |
| 10:30 | morning_plus | 扫描+三卡刷新 |
| 11:45 | morning_report | 午间报告 |
| 13:30 | afternoon | 午后更新 |
| 14:30 | afternoon | 午后更新 |
| 15:20 | afternoon | 收盘前最后更新 |
| 19:30 | close | 收盘全量（双机都跑，互为备份）|
| 21:00 | backup | 审核备份 |

## PowerShell 脚本内容

```powershell
$wd = "E:\workspace\workspace\stock-scanner"
$py = "C:\Users\HH20210606\AppData\Local\Programs\Python\Python312\python.exe"

# 如果 Python 路径不同，请修改上面两行

$tasks = @(
    @{Name="九宝量化-晨间速报"; Time="07:30"; Mode="pre_brief"},
    @{Name="九宝量化-盘前"; Time="09:15"; Mode="pre_market"},
    @{Name="九宝量化-盘中快速"; Time="09:45"; Mode="morning_scan"},
    @{Name="九宝量化-盘中三卡"; Time="10:30"; Mode="morning_plus"},
    @{Name="九宝量化-午间报告"; Time="11:45"; Mode="morning_report"},
    @{Name="九宝量化-午后1"; Time="13:30"; Mode="afternoon"},
    @{Name="九宝量化-午后2"; Time="14:30"; Mode="afternoon"},
    @{Name="九宝量化-收盘前"; Time="15:20"; Mode="afternoon"},
    @{Name="九宝量化-收盘全量"; Time="19:30"; Mode="close"},
    @{Name="九宝量化-审核备份"; Time="21:00"; Mode="backup"}
)

foreach ($task in $tasks) {
    $act = New-ScheduledTaskAction -Execute $py -Argument "batch_update.py $($task.Mode)" -WorkingDirectory $wd
    $trig = New-ScheduledTaskTrigger -Daily -At $task.Time
    $set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    Register-ScheduledTask -TaskName $task.Name -Trigger $trig -Action $act -Settings $set -Description "$($task.Time) $($task.Mode)" -Force
    Write-Output "✅ $($task.Name) ($($task.Time))"
}

Write-Output "`n=== 全部创建完成 ==="
Get-ScheduledTask -TaskName '*九宝量化*' | Select-Object TaskName,State,NextRunTime | Format-Table
```

## 验证

设置完成后，打开"任务计划程序" → 找到"九宝量化*"任务 → 确认：
- State = Ready
- NextRunTime = 明天对应时间
